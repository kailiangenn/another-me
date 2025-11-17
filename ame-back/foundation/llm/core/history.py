"""
会话历史管理

提供会话记录、压缩追踪和导出功能。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any
from datetime import datetime


@dataclass
class ConversationHistory:
    """会话历史记录
    
    用于管道内部维护对话历史和元数据。
    支持完整的导出、清空和恢复功能。
    """
    messages: List[Dict[str, str]] = field(default_factory=list)
    compression_events: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, **meta):
        """添加消息到历史
        
        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
            **meta: 额外元数据
        """
        msg = {"role": role, "content": content}
        if meta:
            msg["metadata"] = meta
        self.messages.append(msg)
    
    def record_compression(self, compression_info: Dict[str, Any]):
        """记录压缩事件
        
        Args:
            compression_info: 压缩信息字典
        """
        self.compression_events.append({
            "timestamp": datetime.now().isoformat(),
            **compression_info
        })
    
    def clear(self):
        """清空所有历史记录
        
        保留 created_at，但清空消息和压缩事件。
        """
        self.messages.clear()
        self.compression_events.clear()
        self.metadata.clear()
    
    def export(self) -> Dict[str, Any]:
        """导出完整历史数据
        
        Returns:
            包含所有历史信息的字典，可用于存储或分析
        """
        return {
            "messages": self.messages.copy(),
            "compression_events": self.compression_events.copy(),
            "created_at": self.created_at.isoformat(),
            "total_messages": len(self.messages),
            "metadata": self.metadata.copy()
        }
    
    def load(self, data: Dict[str, Any]):
        """从导出数据加载历史
        
        Args:
            data: 导出的历史数据
        """
        self.messages = data.get("messages", [])
        self.compression_events = data.get("compression_events", [])
        self.metadata = data.get("metadata", {})
        
        # 恢复创建时间
        created_str = data.get("created_at")
        if created_str:
            try:
                self.created_at = datetime.fromisoformat(created_str)
            except (ValueError, TypeError):
                self.created_at = datetime.now()
    
    def __len__(self) -> int:
        """返回消息数量"""
        return len(self.messages)
    
    def __str__(self) -> str:
        return (
            f"ConversationHistory("
            f"messages={len(self.messages)}, "
            f"compressions={len(self.compression_events)})"
        )
