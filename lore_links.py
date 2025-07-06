import urllib.parse
import requests
import re
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
import email

from models import EmailNode, EmailForest


logger = logging.getLogger(__name__)


class LoreLinksManager:
    def __init__(self, mailing_list: str = "kvmarm"):
        self.mailing_list = mailing_list
        self.base_url = "https://lore.kernel.org"
        
    def generate_lore_url(self, message_id: str) -> str:
        """从Message-ID生成lore.kernel.org链接"""
        # 移除尖括号
        clean_id = message_id.strip('<>')
        
        # URL编码特殊字符
        encoded_id = urllib.parse.quote(clean_id, safe='@.-_')
        
        # 构建lore URL
        lore_url = f"{self.base_url}/{self.mailing_list}/{encoded_id}/"
        
        return lore_url
    
    def validate_lore_url_with_atom(self, url: str, email_node: EmailNode) -> Dict[str, Any]:
        """使用atom feed验证lore链接并匹配内容"""
        try:
            # 构建atom feed URL（获取原始邮件内容）
            atom_url = url.rstrip('/') + '/raw'
            
            # 获取atom内容
            response = requests.get(atom_url, timeout=10, headers={
                'User-Agent': 'ARM-KVM-Analyzer/1.0'
            })
            
            if response.status_code != 200:
                return {
                    "valid": False,
                    "error": f"HTTP {response.status_code}",
                    "match_score": 0
                }
            
            # 解析atom内容
            atom_content = response.text
            atom_data = self._parse_atom_email_content(atom_content)
            
            # 与本地邮件进行匹配验证
            match_result = self._fuzzy_match_email_content(atom_data, email_node)
            
            return {
                "valid": True,
                "match_score": match_result["score"],
                "matched_fields": match_result["matched_fields"],
                "atom_data": atom_data,
                "verification_timestamp": datetime.now().isoformat(),
                "confidence": match_result["confidence"]
            }
            
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "match_score": 0
            }
    
    def _parse_atom_email_content(self, atom_content: str) -> Dict[str, str]:
        """解析atom格式的邮件内容"""
        try:
            # 使用email parser解析原始邮件内容
            email_msg = email.message_from_string(atom_content)
            
            # 提取邮件正文预览
            content_preview = ""
            if email_msg.is_multipart():
                for part in email_msg.walk():
                    if part.get_content_type() == "text/plain":
                        content_preview = part.get_payload(decode=True).decode('utf-8', errors='ignore')[:500]
                        break
            else:
                content_preview = email_msg.get_payload(decode=True).decode('utf-8', errors='ignore')[:500]
            
            return {
                "subject": email_msg.get("Subject", "").strip(),
                "from": email_msg.get("From", "").strip(),
                "date": email_msg.get("Date", "").strip(),
                "message_id": email_msg.get("Message-ID", "").strip('<>'),
                "content_preview": content_preview
            }
        except Exception as e:
            # 如果email解析失败，尝试正则表达式提取
            return self._extract_email_fields_with_regex(atom_content)
    
    def _extract_email_fields_with_regex(self, content: str) -> Dict[str, str]:
        """使用正则表达式提取邮件字段"""
        fields = {}
        
        # 提取Subject
        subject_match = re.search(r'^Subject:\s*(.+)$', content, re.MULTILINE)
        fields["subject"] = subject_match.group(1) if subject_match else ""
        
        # 提取From
        from_match = re.search(r'^From:\s*(.+)$', content, re.MULTILINE)
        fields["from"] = from_match.group(1) if from_match else ""
        
        # 提取Date
        date_match = re.search(r'^Date:\s*(.+)$', content, re.MULTILINE)
        fields["date"] = date_match.group(1) if date_match else ""
        
        # 提取Message-ID
        msgid_match = re.search(r'^Message-I[Dd]:\s*<?([^>]+)>?$', content, re.MULTILINE)
        fields["message_id"] = msgid_match.group(1) if msgid_match else ""
        
        # 提取内容预览
        fields["content_preview"] = content[:500]
        
        return fields
    
    def _fuzzy_match_email_content(self, atom_data: Dict[str, str], email_node: EmailNode) -> Dict[str, Any]:
        """模糊匹配atom数据和本地邮件数据"""
        match_scores = {}
        matched_fields = []
        
        # 1. Message-ID匹配 (最重要)
        if atom_data.get("message_id") == email_node.message_id:
            match_scores["message_id"] = 1.0
            matched_fields.append("message_id")
        else:
            match_scores["message_id"] = 0.0
        
        # 2. Subject相似度匹配
        atom_subject = self._normalize_subject_for_matching(atom_data.get("subject", ""))
        local_subject = self._normalize_subject_for_matching(email_node.subject)
        
        subject_similarity = self._calculate_string_similarity(atom_subject, local_subject)
        match_scores["subject"] = subject_similarity
        
        if subject_similarity > 0.8:
            matched_fields.append("subject")
        
        # 3. 发送者匹配
        atom_sender = self._extract_email_address(atom_data.get("from", ""))
        local_sender = self._extract_email_address(email_node.sender)
        
        if atom_sender and local_sender and atom_sender.lower() == local_sender.lower():
            match_scores["sender"] = 1.0
            matched_fields.append("sender")
        else:
            sender_similarity = self._calculate_string_similarity(atom_sender, local_sender)
            match_scores["sender"] = sender_similarity
            if sender_similarity > 0.8:
                matched_fields.append("sender")
        
        # 4. 日期匹配 (可选)
        if atom_data.get("date") and email_node.date:
            date_match = self._compare_email_dates(atom_data["date"], email_node.date)
            match_scores["date"] = date_match
            if date_match > 0.9:
                matched_fields.append("date")
        
        # 计算总体匹配分数
        weights = {
            "message_id": 0.4,
            "subject": 0.3,
            "sender": 0.2,
            "date": 0.1
        }
        
        total_score = sum(
            match_scores.get(field, 0) * weight
            for field, weight in weights.items()
        )
        
        return {
            "score": total_score,
            "matched_fields": matched_fields,
            "individual_scores": match_scores,
            "confidence": "high" if total_score > 0.8 else "medium" if total_score > 0.6 else "low"
        }
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """计算两个字符串的相似度"""
        if not str1 or not str2:
            return 0.0
        
        # 基本相似度
        basic_sim = SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        
        # 去除常见前缀后的相似度
        clean_str1 = re.sub(r'^(re:|fwd:|\[patch[^\]]*\])\s*', '', str1.lower())
        clean_str2 = re.sub(r'^(re:|fwd:|\[patch[^\]]*\])\s*', '', str2.lower())
        clean_sim = SequenceMatcher(None, clean_str1, clean_str2).ratio()
        
        # 返回较高的相似度
        return max(basic_sim, clean_sim)
    
    def _normalize_subject_for_matching(self, subject: str) -> str:
        """标准化主题用于匹配"""
        # 移除常见的前缀和后缀
        normalized = re.sub(r'^(re:|fwd:)\s*', '', subject.lower())
        normalized = re.sub(r'\[patch[^\]]*\]\s*', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized
    
    def _extract_email_address(self, from_field: str) -> str:
        """从From字段提取纯邮箱地址"""
        # 匹配邮箱地址
        email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        match = re.search(email_pattern, from_field)
        
        return match.group(1) if match else ""
    
    def _compare_email_dates(self, date_str: str, date_obj: datetime) -> float:
        """比较邮件日期"""
        try:
            from email.utils import parsedate_to_datetime
            atom_date = parsedate_to_datetime(date_str)
            
            # 计算时间差（秒）
            time_diff = abs((atom_date - date_obj).total_seconds())
            
            # 如果时间差在1小时内，认为匹配
            if time_diff < 3600:
                return 1.0
            elif time_diff < 86400:  # 1天内
                return 0.8
            else:
                return 0.5
        except:
            return 0.0
    
    def batch_validate_lore_urls(self, email_nodes: List[EmailNode], max_workers: int = 5) -> Dict[str, Dict]:
        """批量验证lore链接"""
        validation_results = {}
        
        def validate_single_email(email_node):
            """验证单个邮件的lore链接"""
            try:
                # 添加延迟避免请求过于频繁
                time.sleep(0.5)
                
                result = self.validate_lore_url_with_atom(email_node.lore_url, email_node)
                return email_node.message_id, result
            except Exception as e:
                return email_node.message_id, {
                    "valid": False,
                    "error": f"Validation failed: {str(e)}",
                    "match_score": 0
                }
        
        print(f"🔍 开始批量验证 {len(email_nodes)} 个lore链接...")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有验证任务
            future_to_email = {
                executor.submit(validate_single_email, email_node): email_node
                for email_node in email_nodes
            }
            
            # 收集验证结果
            for i, future in enumerate(as_completed(future_to_email)):
                message_id, result = future.result()
                validation_results[message_id] = result
                
                # 显示进度
                if (i + 1) % 10 == 0:
                    print(f"   已验证: {i + 1}/{len(email_nodes)}")
        
        # 统计验证结果
        valid_count = sum(1 for r in validation_results.values() if r["valid"])
        high_confidence = sum(1 for r in validation_results.values() 
                             if r.get("match_score", 0) > 0.8)
        
        print(f"✅ 验证完成: {valid_count}/{len(email_nodes)} 有效")
        print(f"🎯 高置信度匹配: {high_confidence}/{len(email_nodes)}")
        
        return validation_results


def add_lore_links(forest: EmailForest):
    """为所有邮件添加lore链接"""
    manager = LoreLinksManager()
    
    for thread in forest.threads:
        for node in thread.all_nodes.values():
            node.lore_url = manager.generate_lore_url(node.message_id)


def validate_lore_links(forest: EmailForest, debug: bool = False):
    """验证所有lore链接"""
    manager = LoreLinksManager()
    
    all_nodes = []
    for thread in forest.threads:
        all_nodes.extend(thread.all_nodes.values())
    
    # 批量验证
    validation_results = manager.batch_validate_lore_urls(all_nodes, max_workers=3)
    
    # 将验证结果添加到节点
    for thread in forest.threads:
        for node in thread.all_nodes.values():
            node.lore_validation = validation_results.get(node.message_id)
            
            if debug and node.lore_validation:
                match_score = node.lore_validation.get("match_score", 0)
                if match_score < 0.6:
                    print(f"⚠️  低匹配度: {node.subject[:50]}... (分数: {match_score:.2f})")


def test_lore_link_generation():
    """测试lore链接生成"""
    print("🧪 测试lore链接生成...")
    
    manager = LoreLinksManager()
    
    # 测试用例
    test_cases = [
        ("20250705071717.5062-1-ankita@nvidia.com", 
         "https://lore.kernel.org/kvmarm/20250705071717.5062-1-ankita@nvidia.com/"),
        ("<test-message-id@example.com>",
         "https://lore.kernel.org/kvmarm/test-message-id@example.com/"),
    ]
    
    for message_id, expected_url in test_cases:
        generated_url = manager.generate_lore_url(message_id)
        assert generated_url == expected_url, f"Expected {expected_url}, got {generated_url}"
        print(f"   ✅ {message_id} -> {generated_url}")
    
    print("✅ Lore链接生成测试通过")


def test_lore_link_validation():
    """测试lore链接验证"""
    print("🧪 测试lore链接验证...")
    
    from email_parser import extract_emails_by_date_range
    
    # 获取测试邮件
    emails = extract_emails_by_date_range(None, limit=5)
    
    if not emails:
        print("   ⚠️  没有找到测试邮件")
        return
    
    manager = LoreLinksManager()
    
    for email in emails[:3]:  # 只测试前3封
        email.lore_url = manager.generate_lore_url(email.message_id)
        
        print(f"\n   📧 测试邮件: {email.subject[:40]}...")
        print(f"      🆔 Message-ID: {email.message_id}")
        print(f"      🔗 Lore URL: {email.lore_url}")
        
        # 验证链接
        validation_result = manager.validate_lore_url_with_atom(email.lore_url, email)
        
        if validation_result["valid"]:
            match_score = validation_result["match_score"]
            confidence = validation_result.get("confidence", "unknown")
            matched_fields = validation_result.get("matched_fields", [])
            
            print(f"      ✅ 验证成功 - 匹配度: {match_score:.2f} ({confidence})")
            print(f"      🎯 匹配字段: {', '.join(matched_fields)}")
        else:
            error = validation_result.get("error", "Unknown error")
            print(f"      ❌ 验证失败: {error}")
    
    print("\n✅ Lore链接验证测试完成")