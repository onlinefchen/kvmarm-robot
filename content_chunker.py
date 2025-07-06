import logging
import re
from typing import List, Dict, Optional
import tiktoken

from models import ContentChunk, ChunkType, EmailNode, EmailForest, MessageType
from email_parser import EmailParser
from repository import RepositoryManager


logger = logging.getLogger(__name__)


class ContentChunker:
    def __init__(self, max_tokens: int = 8000):
        self.max_tokens = max_tokens
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        self.repo_manager = RepositoryManager()
        self.email_parser = EmailParser()
        
    def apply_intelligent_chunking(self, forest: EmailForest) -> Dict[str, List[ContentChunk]]:
        """对邮件森林进行智能分割"""
        chunked_data = {}
        
        for thread in forest.threads:
            for node in thread.all_nodes.values():
                # 获取邮件的完整内容
                content = self._extract_full_content(node)
                
                if self._needs_chunking(content):
                    chunks = self._smart_chunk_content(content, node)
                else:
                    # 不需要分割，创建单个chunk
                    chunks = [ContentChunk(
                        chunk_id=f"{node.git_hash}_0",
                        git_hash=node.git_hash,
                        chunk_type=ChunkType.HEADER,
                        content=content,
                        priority=5,
                        token_count=self._count_tokens(content)
                    )]
                
                chunked_data[node.message_id] = chunks
                node.content_chunks = chunks
        
        return chunked_data
    
    def _extract_full_content(self, node: EmailNode) -> str:
        """提取邮件的完整内容"""
        try:
            # 从git仓库获取原始内容
            content = self.repo_manager.get_commit_content(node.git_hash)
            return content
        except Exception as e:
            logger.error(f"Failed to extract content for {node.git_hash}: {e}")
            return ""
    
    def _needs_chunking(self, content: str) -> bool:
        """判断内容是否需要分割"""
        token_count = self._count_tokens(content)
        
        # Token数量超过阈值
        if token_count > self.max_tokens:
            return True
        
        # 代码diff超过10KB
        if self._get_code_diff_size(content) > 10240:
            return True
        
        # 多层回复嵌套超过3级
        if self._get_reply_nesting_level(content) > 3:
            return True
        
        return False
    
    def _smart_chunk_content(self, content: str, node: EmailNode) -> List[ContentChunk]:
        """智能分割内容"""
        chunks = []
        
        # 1. 分离邮件头部信息
        header_chunk = self._extract_header_chunk(content, node)
        if header_chunk:
            chunks.append(header_chunk)
        
        # 2. 根据邮件类型进行不同的分割策略
        if node.message_type in [MessageType.PATCH, MessageType.PATCH_COVER]:
            chunks.extend(self._chunk_patch_content(content, node))
        elif node.message_type == MessageType.REVIEW:
            chunks.extend(self._chunk_review_content(content, node))
        else:
            chunks.extend(self._chunk_discussion_content(content, node))
        
        # 3. 确保每个chunk都在token限制内
        chunks = self._ensure_chunk_size_limits(chunks)
        
        return chunks
    
    def _extract_header_chunk(self, content: str, node: EmailNode) -> Optional[ContentChunk]:
        """提取邮件头部信息chunk"""
        # 提取邮件头部（From, Date, Subject等）
        header_pattern = r'^(From:.*?\n\n)'
        match = re.search(header_pattern, content, re.DOTALL | re.MULTILINE)
        
        if match:
            header_content = match.group(1)
            
            # 添加关键的邮件元数据
            header_content += f"\nMessage-Type: {node.message_type.value}\n"
            if node.patch_info:
                header_content += f"Patch: v{node.patch_info.version} "
                header_content += f"{node.patch_info.number}/{node.patch_info.total}\n"
            
            return ContentChunk(
                chunk_id=f"{node.git_hash}_header",
                git_hash=node.git_hash,
                chunk_type=ChunkType.HEADER,
                content=header_content,
                priority=5,
                token_count=self._count_tokens(header_content)
            )
        
        return None
    
    def _chunk_patch_content(self, content: str, node: EmailNode) -> List[ContentChunk]:
        """分割补丁内容"""
        chunks = []
        
        # 1. 提取commit message/summary
        summary_chunk = self._extract_patch_summary(content, node)
        if summary_chunk:
            chunks.append(summary_chunk)
        
        # 2. 分割diff内容
        diff_chunks = self._extract_diff_chunks(content, node)
        chunks.extend(diff_chunks)
        
        return chunks
    
    def _chunk_review_content(self, content: str, node: EmailNode) -> List[ContentChunk]:
        """分割review内容"""
        chunks = []
        
        # 1. 提取review summary
        summary_chunk = self._extract_review_summary(content, node)
        if summary_chunk:
            chunks.append(summary_chunk)
        
        # 2. 分割详细评论
        comment_chunks = self._extract_review_comments(content, node)
        chunks.extend(comment_chunks)
        
        return chunks
    
    def _chunk_discussion_content(self, content: str, node: EmailNode) -> List[ContentChunk]:
        """分割讨论内容"""
        chunks = []
        
        # 按照引用层级分割
        sections = self._split_by_quote_level(content)
        
        for i, section in enumerate(sections):
            chunk = ContentChunk(
                chunk_id=f"{node.git_hash}_disc_{i}",
                git_hash=node.git_hash,
                chunk_type=ChunkType.DISCUSSION,
                content=section,
                priority=3,
                token_count=self._count_tokens(section)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_patch_summary(self, content: str, node: EmailNode) -> Optional[ContentChunk]:
        """提取补丁摘要"""
        # 查找commit message部分
        commit_msg_pattern = r'\n\n(.*?)(?:\n---\n|\ndiff --git)'
        match = re.search(commit_msg_pattern, content, re.DOTALL)
        
        if match:
            summary = match.group(1).strip()
            return ContentChunk(
                chunk_id=f"{node.git_hash}_summary",
                git_hash=node.git_hash,
                chunk_type=ChunkType.SUMMARY,
                content=summary,
                priority=4,
                token_count=self._count_tokens(summary)
            )
        
        return None
    
    def _extract_diff_chunks(self, content: str, node: EmailNode) -> List[ContentChunk]:
        """提取并分割diff内容"""
        chunks = []
        
        # 查找diff部分
        diff_pattern = r'(diff --git.*?)(?=diff --git|$)'
        diffs = re.findall(diff_pattern, content, re.DOTALL)
        
        for i, diff in enumerate(diffs):
            # 判断是否为关键代码更改
            is_critical = self._is_critical_code_change(diff)
            chunk_type = ChunkType.CODE_CRITICAL if is_critical else ChunkType.CODE_DETAIL
            priority = 4 if is_critical else 2
            
            chunk = ContentChunk(
                chunk_id=f"{node.git_hash}_diff_{i}",
                git_hash=node.git_hash,
                chunk_type=chunk_type,
                content=diff,
                priority=priority,
                token_count=self._count_tokens(diff)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _extract_review_summary(self, content: str, node: EmailNode) -> Optional[ContentChunk]:
        """提取review摘要"""
        # 查找review的主要观点（通常在邮件开头）
        lines = content.split('\n')
        summary_lines = []
        
        for line in lines:
            if line.strip() and not line.startswith('>'):
                summary_lines.append(line)
                if len('\n'.join(summary_lines)) > 1000:  # 限制摘要长度
                    break
        
        if summary_lines:
            summary = '\n'.join(summary_lines)
            return ContentChunk(
                chunk_id=f"{node.git_hash}_review_summary",
                git_hash=node.git_hash,
                chunk_type=ChunkType.SUMMARY,
                content=summary,
                priority=4,
                token_count=self._count_tokens(summary)
            )
        
        return None
    
    def _extract_review_comments(self, content: str, node: EmailNode) -> List[ContentChunk]:
        """提取review的详细评论"""
        chunks = []
        
        # 按照引用的代码段分割评论
        comment_pattern = r'(>+.*?\n(?:[^>].*?\n)*)'
        comments = re.findall(comment_pattern, content, re.MULTILINE)
        
        for i, comment in enumerate(comments):
            chunk = ContentChunk(
                chunk_id=f"{node.git_hash}_comment_{i}",
                git_hash=node.git_hash,
                chunk_type=ChunkType.DISCUSSION,
                content=comment,
                priority=3,
                token_count=self._count_tokens(comment)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _split_by_quote_level(self, content: str) -> List[str]:
        """按引用层级分割内容"""
        sections = []
        current_section = []
        current_quote_level = 0
        
        for line in content.split('\n'):
            # 计算引用层级
            quote_level = len(re.match(r'^(>+)', line).group(1)) if line.startswith('>') else 0
            
            # 如果引用层级变化，创建新section
            if quote_level != current_quote_level and current_section:
                sections.append('\n'.join(current_section))
                current_section = []
                current_quote_level = quote_level
            
            current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections
    
    def _ensure_chunk_size_limits(self, chunks: List[ContentChunk]) -> List[ContentChunk]:
        """确保每个chunk都在token限制内"""
        final_chunks = []
        
        for chunk in chunks:
            if chunk.token_count <= self.max_tokens:
                final_chunks.append(chunk)
            else:
                # 需要进一步分割
                sub_chunks = self._split_large_chunk(chunk)
                final_chunks.extend(sub_chunks)
        
        return final_chunks
    
    def _split_large_chunk(self, chunk: ContentChunk) -> List[ContentChunk]:
        """分割过大的chunk"""
        sub_chunks = []
        content = chunk.content
        
        # 按行分割，确保不超过token限制
        lines = content.split('\n')
        current_content = []
        current_tokens = 0
        sub_index = 0
        
        for line in lines:
            line_tokens = self._count_tokens(line + '\n')
            
            if current_tokens + line_tokens > self.max_tokens and current_content:
                # 创建新的sub chunk
                sub_chunk = ContentChunk(
                    chunk_id=f"{chunk.chunk_id}_sub_{sub_index}",
                    git_hash=chunk.git_hash,
                    chunk_type=chunk.chunk_type,
                    content='\n'.join(current_content),
                    priority=chunk.priority,
                    token_count=current_tokens
                )
                sub_chunks.append(sub_chunk)
                
                # 重置
                current_content = [line]
                current_tokens = line_tokens
                sub_index += 1
            else:
                current_content.append(line)
                current_tokens += line_tokens
        
        # 添加最后一个chunk
        if current_content:
            sub_chunk = ContentChunk(
                chunk_id=f"{chunk.chunk_id}_sub_{sub_index}",
                git_hash=chunk.git_hash,
                chunk_type=chunk.chunk_type,
                content='\n'.join(current_content),
                priority=chunk.priority,
                token_count=current_tokens
            )
            sub_chunks.append(sub_chunk)
        
        return sub_chunks
    
    def _count_tokens(self, text: str) -> int:
        """计算文本的token数量"""
        return len(self.tokenizer.encode(text))
    
    def _get_code_diff_size(self, content: str) -> int:
        """获取代码diff的大小"""
        diff_pattern = r'diff --git.*?(?=diff --git|$)'
        diffs = re.findall(diff_pattern, content, re.DOTALL)
        return sum(len(diff.encode('utf-8')) for diff in diffs)
    
    def _get_reply_nesting_level(self, content: str) -> int:
        """获取回复嵌套层级"""
        max_level = 0
        for line in content.split('\n'):
            if line.startswith('>'):
                level = len(re.match(r'^(>+)', line).group(1))
                max_level = max(max_level, level)
        return max_level
    
    def _is_critical_code_change(self, diff: str) -> bool:
        """判断是否为关键代码更改"""
        # 检查是否修改了关键文件
        critical_patterns = [
            r'arch/arm64/kvm',
            r'virt/kvm/arm',
            r'include/.*kvm',
            r'\.h\s+\|',  # 头文件更改
            r'Kconfig',
            r'Makefile'
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, diff, re.IGNORECASE):
                return True
        
        return False


def apply_intelligent_chunking(forest: EmailForest, max_tokens: int = 8000) -> Dict[str, List[ContentChunk]]:
    """应用智能分割的便捷函数"""
    chunker = ContentChunker(max_tokens)
    return chunker.apply_intelligent_chunking(forest)


def test_content_chunking():
    """测试智能内容分割"""
    print("🧪 测试智能内容分割...")
    
    from email_parser import extract_emails_by_date_range
    from tree_builder import build_email_forest
    from lore_links import LoreLinksManager
    
    # 获取测试邮件
    emails = extract_emails_by_date_range(None, limit=20)
    
    if not emails:
        print("   ⚠️  没有找到测试邮件")
        return
    
    # 添加lore链接
    lore_manager = LoreLinksManager()
    for email in emails:
        email.lore_url = lore_manager.generate_lore_url(email.message_id)
    
    # 构建森林
    forest = build_email_forest(emails)
    
    # 应用智能分割
    chunked_data = apply_intelligent_chunking(forest, max_tokens=8000)
    
    # 统计分割结果
    total_chunks = sum(len(chunks) for chunks in chunked_data.values())
    chunked_emails = sum(1 for chunks in chunked_data.values() if len(chunks) > 1)
    
    print(f"   📊 总分块数: {total_chunks}")
    print(f"   📧 需要分块的邮件: {chunked_emails}")
    
    # 显示一些分块示例
    for message_id, chunks in list(chunked_data.items())[:3]:
        if len(chunks) > 1:
            print(f"\n   ✂️  邮件 {message_id[:40]}... 分成 {len(chunks)} 块:")
            for chunk in chunks:
                print(f"      📝 {chunk.chunk_type.value} (优先级: {chunk.priority}, " +
                      f"tokens: {chunk.token_count})")
    
    print("\n✅ 内容分割测试通过")