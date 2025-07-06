import re
import email
from email import policy
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging
import git

from models import EmailNode, MessageType, PatchInfo


logger = logging.getLogger(__name__)


class EmailParser:
    def __init__(self):
        self.patch_pattern = re.compile(
            r'\[PATCH\s*(?:v(\d+))?\s*(?:(\d+)/(\d+))?\](.*)$',
            re.IGNORECASE
        )
        
    def parse_commit_to_email(self, commit: git.Commit) -> EmailNode:
        """将git commit解析为EmailNode"""
        # 获取commit的原始邮件内容
        raw_content = self._get_raw_email_content(commit)
        
        # 解析邮件头
        email_msg = email.message_from_string(raw_content, policy=policy.default)
        
        # 提取基本信息
        message_id = self._extract_message_id(email_msg)
        subject = email_msg.get("Subject", "").strip()
        sender = email_msg.get("From", "").strip()
        date = self._parse_date(email_msg.get("Date", ""))
        
        # 解析邮件类型和补丁信息
        message_type, patch_info = self._analyze_message_type(subject)
        
        # 提取父邮件ID
        parent_id = self._extract_parent_id(email_msg)
        
        return EmailNode(
            git_hash=commit.hexsha,
            message_id=message_id,
            subject=subject,
            sender=sender,
            date=date,
            message_type=message_type,
            parent_id=parent_id,
            patch_info=patch_info,
            in_reply_to=email_msg.get("In-Reply-To", "").strip('<>')
        )
    
    def _get_raw_email_content(self, commit: git.Commit) -> str:
        """获取commit的原始邮件内容"""
        try:
            # 对于lore.kernel.org的git仓库，邮件内容存储在文件'm'中
            # 我们需要获取最新版本的'm'文件内容
            tree = commit.tree
            if 'm' in tree:
                mail_file = tree['m']
                return mail_file.data_stream.read().decode('utf-8', errors='ignore')
            else:
                # 如果没有'm'文件，返回commit message作为fallback
                return commit.message
                
        except Exception as e:
            logger.error(f"Failed to get raw content for {commit.hexsha}: {e}")
            return commit.message
    
    def _extract_message_id(self, email_msg: email.message.Message) -> str:
        """提取并清理Message-ID"""
        message_id = email_msg.get("Message-ID", "")
        # 移除尖括号
        return message_id.strip('<>')
    
    def _parse_date(self, date_str: str) -> datetime:
        """解析邮件日期"""
        try:
            # 使用email.utils解析RFC2822格式的日期
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_str)
        except:
            # 如果解析失败，返回当前时间
            logger.warning(f"Failed to parse date: {date_str}")
            return datetime.now()
    
    def _analyze_message_type(self, subject: str) -> tuple[MessageType, Optional[PatchInfo]]:
        """分析邮件类型和补丁信息"""
        # 检查是否为补丁
        match = self.patch_pattern.search(subject)
        if match:
            version = int(match.group(1)) if match.group(1) else 1
            patch_num = int(match.group(2)) if match.group(2) else 0
            total_patches = int(match.group(3)) if match.group(3) else 1
            series_name = match.group(4).strip()
            
            patch_info = PatchInfo(
                version=version,
                number=patch_num,
                total=total_patches,
                series_name=series_name
            )
            
            if patch_num == 0:
                return MessageType.PATCH_COVER, patch_info
            else:
                return MessageType.PATCH, patch_info
        
        # 检查其他类型
        subject_lower = subject.lower()
        if subject_lower.startswith("re:"):
            if "reviewed-by" in subject_lower or "review" in subject_lower:
                return MessageType.REVIEW, None
            elif "acked-by" in subject_lower:
                return MessageType.ACK, None
            else:
                return MessageType.REPLY, None
        
        return MessageType.OTHER, None
    
    def _extract_parent_id(self, email_msg: email.message.Message) -> Optional[str]:
        """提取父邮件ID"""
        # 首先尝试In-Reply-To
        in_reply_to = email_msg.get("In-Reply-To", "").strip('<>')
        if in_reply_to:
            return in_reply_to
        
        # 然后尝试References的最后一个
        references = email_msg.get("References", "")
        if references:
            # References可能包含多个Message-ID，取最后一个
            ref_ids = re.findall(r'<([^>]+)>', references)
            if ref_ids:
                return ref_ids[-1]
        
        return None
    
    def extract_full_content(self, commit: git.Commit) -> str:
        """提取邮件的完整内容"""
        raw_content = self._get_raw_email_content(commit)
        email_msg = email.message_from_string(raw_content, policy=policy.default)
        
        # 提取邮件正文
        body = ""
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    body += part.get_content()
        else:
            body = email_msg.get_content()
        
        return body


def extract_emails_by_date_range(
    repo_path: str,
    date_range: Optional[tuple[datetime, datetime]] = None,
    limit: Optional[int] = None,
    verify_completeness: bool = True
) -> List[EmailNode]:
    """按时间范围提取邮件，支持完整性验证"""
    from repository import RepositoryManager
    
    manager = RepositoryManager()
    parser = EmailParser()
    
    if date_range:
        since, until = date_range
        commits = manager.get_commits_in_range(since, until)
        print(f"📅 时间范围: {since.strftime('%Y-%m-%d')} 到 {until.strftime('%Y-%m-%d')}")
    else:
        # 默认获取最近的commits
        commits = manager.get_recent_commits(limit=limit or 100)
        print(f"📊 获取最近 {limit or 100} 个 commits")
    
    print(f"🔍 找到 {len(commits)} 个 commits 需要处理")
    
    emails = []
    failed_commits = []
    
    for i, commit in enumerate(commits):
        try:
            email_node = parser.parse_commit_to_email(commit)
            
            # 验证邮件内容是否有效
            if _is_valid_email(email_node):
                emails.append(email_node)
            else:
                logger.warning(f"Invalid email content in commit {commit.hexsha}")
                failed_commits.append((commit.hexsha, "Invalid content"))
                
        except Exception as e:
            logger.error(f"Failed to parse commit {commit.hexsha}: {e}")
            failed_commits.append((commit.hexsha, str(e)))
        
        # 显示进度
        if (i + 1) % 50 == 0:
            print(f"   📊 已处理: {i + 1}/{len(commits)} commits")
    
    # 完整性验证报告
    if verify_completeness:
        print(f"\n📋 邮件提取完整性报告:")
        print(f"   ✅ 成功提取: {len(emails)} 封邮件")
        print(f"   ❌ 解析失败: {len(failed_commits)} 个 commits")
        
        if failed_commits:
            print(f"   ⚠️  失败详情:")
            for commit_hash, error in failed_commits[:5]:  # 只显示前5个
                print(f"      {commit_hash[:8]}: {error}")
            if len(failed_commits) > 5:
                print(f"      ... 还有 {len(failed_commits) - 5} 个")
        
        # 检查时间连续性
        if len(emails) > 1:
            _verify_temporal_continuity(emails)
    
    return emails


def _is_valid_email(email_node: EmailNode) -> bool:
    """验证邮件节点是否有效"""
    # 基本字段检查
    if not email_node.message_id or not email_node.subject or not email_node.sender:
        return False
    
    # Message-ID格式检查
    if not re.match(r'^[a-zA-Z0-9\.\-_@]+$', email_node.message_id.replace('<', '').replace('>', '')):
        return False
    
    # 主题合理性检查（不应该只是空白或无意义字符）
    if len(email_node.subject.strip()) < 3:
        return False
    
    return True


def _verify_temporal_continuity(emails: List[EmailNode]) -> None:
    """验证邮件时间连续性"""
    # 按时间排序
    sorted_emails = sorted(emails, key=lambda x: x.date)
    
    gaps = []
    for i in range(1, len(sorted_emails)):
        time_diff = (sorted_emails[i].date - sorted_emails[i-1].date).days
        if time_diff > 7:  # 如果间隔超过7天，可能有遗漏
            gaps.append((sorted_emails[i-1].date, sorted_emails[i].date, time_diff))
    
    if gaps:
        print(f"   ⚠️  发现 {len(gaps)} 个可能的时间间隙:")
        for start_date, end_date, days in gaps[:3]:
            print(f"      {start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')} ({days} 天)")
        if len(gaps) > 3:
            print(f"      ... 还有 {len(gaps) - 3} 个间隙")
    else:
        print(f"   ✅ 时间连续性良好，无明显间隙")


def test_email_parsing():
    """测试邮件解析功能"""
    print("🧪 测试邮件解析...")
    
    from repository import RepositoryManager
    
    manager = RepositoryManager()
    repo_path = manager.ensure_repository_updated()
    
    # 获取最近10个commits进行测试
    emails = extract_emails_by_date_range(str(repo_path), limit=10)
    
    assert len(emails) > 0
    print(f"   提取了 {len(emails)} 封邮件")
    
    # 检查邮件基本信息
    for i, email_node in enumerate(emails[:5]):
        print(f"\n   📧 邮件 {i+1}:")
        print(f"      主题: {email_node.subject[:60]}...")
        print(f"      发送者: {email_node.sender}")
        print(f"      类型: {email_node.message_type.value}")
        print(f"      Message-ID: {email_node.message_id}")
        
        if email_node.patch_info:
            print(f"      补丁: v{email_node.patch_info.version} " +
                  f"{email_node.patch_info.number}/{email_node.patch_info.total}")
    
    print("\n✅ 邮件解析测试通过")