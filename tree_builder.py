import logging
from typing import List, Dict, Optional
from datetime import datetime
from collections import defaultdict

from models import EmailNode, EmailThread, EmailForest, ThreadStats, MessageType


logger = logging.getLogger(__name__)


class TreeBuilder:
    def __init__(self):
        self.threads = []
        self.message_id_to_node = {}
        self.root_nodes = []
        
    def build_email_forest(self, emails: List[EmailNode]) -> EmailForest:
        """构建邮件森林（多个线程树）"""
        # 1. 创建message_id到node的映射
        self.message_id_to_node = {email.message_id: email for email in emails}
        
        # 2. 建立父子关系
        self._build_parent_child_relationships()
        
        # 3. 找出所有根节点
        self._identify_root_nodes()
        
        # 4. 构建线程
        self._build_threads()
        
        # 5. 计算统计信息
        self._calculate_statistics()
        
        # 6. 创建森林
        date_range = self._get_date_range(emails)
        forest = EmailForest(
            threads=self.threads,
            total_emails=len(emails),
            date_range=date_range,
            metadata={
                "total_threads": len(self.threads),
                "orphan_messages": len([e for e in emails if not e.parent_id and e not in self.root_nodes])
            }
        )
        
        return forest
    
    def _build_parent_child_relationships(self):
        """建立邮件之间的父子关系"""
        for email in self.message_id_to_node.values():
            if email.parent_id and email.parent_id in self.message_id_to_node:
                parent = self.message_id_to_node[email.parent_id]
                parent.children_ids.append(email.message_id)
                
                # 设置回复层级
                email.reply_level = parent.reply_level + 1
    
    def _identify_root_nodes(self):
        """识别所有根节点（没有父节点的邮件）"""
        self.root_nodes = []
        
        # 首先尝试按补丁系列分组
        patch_series_groups = self._group_by_patch_series()
        
        if patch_series_groups:
            # 如果有补丁系列，为每个系列创建一个虚拟根节点
            for series_id, patches in patch_series_groups.items():
                # 使用最早的patch作为根节点
                root_patch = min(patches, key=lambda p: p.date)
                self.root_nodes.append(root_patch)
                
                # 将其他patch作为子节点
                for patch in patches:
                    if patch != root_patch:
                        root_patch.children_ids.append(patch.message_id)
                        patch.parent_id = root_patch.message_id
        else:
            # 原有的逻辑作为fallback
            for email in self.message_id_to_node.values():
                if not email.parent_id or email.parent_id not in self.message_id_to_node:
                    if self._is_likely_root_node(email):
                        self.root_nodes.append(email)
    
    def _is_likely_root_node(self, email: EmailNode) -> bool:
        """判断是否可能是根节点"""
        # 补丁封面肯定是根节点
        if email.message_type == MessageType.PATCH_COVER:
            return True
        
        # 第一个补丁也可能是根节点
        if email.message_type == MessageType.PATCH and email.patch_info:
            if email.patch_info.number == 1:
                return True
        
        # 没有Re:前缀的通常是新线程
        if not email.subject.lower().startswith("re:"):
            return True
        
        # 有子节点但没有父节点的
        if email.children_ids and not email.parent_id:
            return True
        
        return False
    
    def _build_threads(self):
        """构建邮件线程"""
        self.threads = []
        
        for root_node in self.root_nodes:
            # 收集线程中的所有节点
            all_nodes = {}
            self._collect_thread_nodes(root_node, all_nodes)
            
            # 创建线程
            thread = EmailThread(
                thread_id=f"thread_{root_node.date.strftime('%Y%m%d')}_{root_node.git_hash[:8]}",
                root_node=root_node,
                all_nodes=all_nodes,
                statistics=None  # 稍后计算
            )
            
            self.threads.append(thread)
    
    def _collect_thread_nodes(self, node: EmailNode, all_nodes: Dict[str, EmailNode]):
        """递归收集线程中的所有节点"""
        all_nodes[node.message_id] = node
        
        for child_id in node.children_ids:
            if child_id in self.message_id_to_node:
                child_node = self.message_id_to_node[child_id]
                self._collect_thread_nodes(child_node, all_nodes)
    
    def _calculate_statistics(self):
        """计算每个线程的统计信息"""
        for thread in self.threads:
            stats = self._calculate_thread_statistics(thread)
            thread.statistics = stats
    
    def _calculate_thread_statistics(self, thread: EmailThread) -> ThreadStats:
        """计算单个线程的统计信息"""
        nodes = list(thread.all_nodes.values())
        
        # 统计各种类型的消息
        type_counts = defaultdict(int)
        for node in nodes:
            type_counts[node.message_type] += 1
        
        # 获取贡献者列表
        contributors = list(set(node.sender for node in nodes))
        
        # 计算日期范围
        dates = [node.date for node in nodes]
        date_range = (min(dates), max(dates))
        
        # 计算最大深度
        max_depth = max(node.reply_level for node in nodes)
        
        # 补丁系列信息
        patch_series = None
        if thread.root_node.patch_info:
            patch_series = {
                "version": thread.root_node.patch_info.version,
                "total_patches": thread.root_node.patch_info.total,
                "completion_status": self._get_patch_series_status(thread)
            }
        
        return ThreadStats(
            total_messages=len(nodes),
            patches=type_counts[MessageType.PATCH],
            replies=type_counts[MessageType.REPLY],
            reviews=type_counts[MessageType.REVIEW],
            acks=type_counts[MessageType.ACK],
            max_depth=max_depth,
            contributors=contributors,
            date_range=date_range,
            patch_series=patch_series
        )
    
    def _get_patch_series_status(self, thread: EmailThread) -> str:
        """获取补丁系列的状态"""
        # 检查是否有review或ack
        has_review = any(node.message_type == MessageType.REVIEW 
                        for node in thread.all_nodes.values())
        has_ack = any(node.message_type == MessageType.ACK 
                     for node in thread.all_nodes.values())
        
        if has_ack:
            return "acked"
        elif has_review:
            return "under_review"
        else:
            return "new"
    
    def _group_by_patch_series(self) -> Dict[str, List[EmailNode]]:
        """按补丁系列分组"""
        groups = defaultdict(list)
        
        for email in self.message_id_to_node.values():
            if email.message_type == MessageType.PATCH and email.patch_info:
                # 从Message-ID推断系列ID，如 20250705071717.5062-x-ankita@nvidia.com
                # 我们使用前缀作为系列标识
                msg_id = email.message_id
                if '-' in msg_id:
                    # 提取基础部分，去掉 -x-email 的 x 部分
                    parts = msg_id.split('-')
                    if len(parts) >= 3:
                        # 重构为基础格式：timestamp.num-email
                        base_id = f"{parts[0]}-{parts[2]}"  # 跳过数字部分
                        groups[base_id].append(email)
                    else:
                        # fallback：使用patch info的version和total作为分组
                        series_key = f"v{email.patch_info.version}_{email.patch_info.total}patches"
                        groups[series_key].append(email)
        
        # 只返回有多个patch的组
        return {k: v for k, v in groups.items() if len(v) > 1}
    
    def _get_date_range(self, emails: List[EmailNode]) -> tuple[datetime, datetime]:
        """获取邮件的日期范围"""
        if not emails:
            now = datetime.now()
            return (now, now)
        
        dates = [email.date for email in emails]
        return (min(dates), max(dates))


def build_email_forest(emails: List[EmailNode]) -> EmailForest:
    """构建邮件森林的便捷函数"""
    builder = TreeBuilder()
    return builder.build_email_forest(emails)


def test_tree_building():
    """测试树形结构构建"""
    print("🧪 测试树形结构构建...")
    
    from email_parser import extract_emails_by_date_range
    from lore_links import LoreLinksManager
    
    # 获取测试邮件
    emails = extract_emails_by_date_range(None, limit=50)
    
    if not emails:
        print("   ⚠️  没有找到测试邮件")
        return
    
    # 添加lore链接
    lore_manager = LoreLinksManager()
    for email in emails:
        email.lore_url = lore_manager.generate_lore_url(email.message_id)
    
    # 构建森林
    forest = build_email_forest(emails)
    
    assert len(forest.threads) > 0
    print(f"   构建了 {len(forest.threads)} 个线程")
    print(f"   总邮件数: {forest.total_emails}")
    
    # 检查前3个线程
    for i, thread in enumerate(forest.threads[:3]):
        print(f"\n   📋 线程 {i+1}: {thread.subject[:60]}")
        print(f"      🔗 {thread.root_node.lore_url}")
        print(f"      📊 {len(thread.all_nodes)} 封邮件")
        print(f"      👥 {len(thread.statistics.contributors)} 位贡献者")
        print(f"      📐 最大深度: {thread.statistics.max_depth}")
        
        if thread.statistics.patch_series:
            print(f"      🔧 补丁系列: v{thread.statistics.patch_series['version']} " +
                  f"({thread.statistics.patch_series['completion_status']})")
    
    print("\n✅ 树形结构构建测试通过")