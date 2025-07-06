from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class MessageType(Enum):
    PATCH = "patch"
    PATCH_COVER = "patch_cover"
    REPLY = "reply"
    REVIEW = "review"
    ACK = "ack"
    OTHER = "other"


class ChunkType(Enum):
    HEADER = "header"
    SUMMARY = "summary"
    CODE_CRITICAL = "code_critical"
    DISCUSSION = "discussion"
    CODE_DETAIL = "code_detail"
    METADATA = "metadata"


@dataclass
class PatchInfo:
    version: int
    number: int
    total: int
    series_name: str = ""


@dataclass
class ContentChunk:
    chunk_id: str
    git_hash: str
    chunk_type: ChunkType
    content: str
    priority: int
    token_count: int
    start_line: int = 0
    end_line: int = 0


@dataclass
class EmailNode:
    git_hash: str
    message_id: str
    subject: str
    sender: str
    date: datetime
    message_type: MessageType
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    
    # Lore.kernel.org链接和验证
    lore_url: str = ""
    lore_validation: Optional[Dict[str, Any]] = None
    
    # ARM KVM特有
    is_arm_kvm_related: bool = True
    patch_info: Optional[PatchInfo] = None
    
    # 分析结果
    ai_analysis: Optional[Dict[str, Any]] = None
    content_chunks: List[ContentChunk] = field(default_factory=list)
    
    # Reply特有
    reply_level: int = 0
    in_reply_to: Optional[str] = None


@dataclass
class ThreadStats:
    total_messages: int
    patches: int
    replies: int
    reviews: int
    acks: int
    max_depth: int
    contributors: List[str]
    date_range: tuple[datetime, datetime]
    patch_series: Optional[Dict[str, Any]] = None


@dataclass
class EmailThread:
    thread_id: str
    root_node: EmailNode
    all_nodes: Dict[str, EmailNode]
    statistics: ThreadStats
    ai_summary: Optional[Dict[str, Any]] = None
    subject: str = ""
    
    def __post_init__(self):
        if not self.subject:
            self.subject = self.root_node.subject


@dataclass
class EmailForest:
    threads: List[EmailThread]
    total_emails: int
    date_range: tuple[datetime, datetime]
    metadata: Dict[str, Any] = field(default_factory=dict)