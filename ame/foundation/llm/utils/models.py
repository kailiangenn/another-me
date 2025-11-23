"""LLM 核心数据模型

统一管理 LLM 模块中的所有数据类。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime


# ============================================================================
# LLM调用相关数据模型
# ============================================================================

@dataclass
class LLMResponse:
    """LLM响应数据模型"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    metadata: Optional[Dict] = None
    
    @property
    def total_tokens(self) -> int:
        """获取总token数"""
        if self.usage:
            return self.usage.get("total_tokens", 0)
        return 0
    
    @property
    def prompt_tokens(self) -> int:
        """获取提示token数"""
        if self.usage:
            return self.usage.get("prompt_tokens", 0)
        return 0
    
    @property
    def completion_tokens(self) -> int:
        """获取完成token数"""
        if self.usage:
            return self.usage.get("completion_tokens", 0)
        return 0


# ============================================================================
# 会话历史数据模型
# ============================================================================

@dataclass
class ConversationHistory:
    """会话历史数据模型
    
    职责：只负责数据存储和基础操作
    不负责：压缩、截断等功能管理（由HistoryManager负责）
    """
    messages: List[Dict[str, str]] = field(default_factory=list)
    system_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, **extra) -> None:
        """添加消息
        
        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
            **extra: 额外元数据
        """
        if role == "system":
            self.system_message = content
        else:
            message = {"role": role, "content": content}
            if extra:
                message.update(extra)
            self.messages.append(message)
    
    def add_user_message(self, content: str, **extra) -> None:
        """添加用户消息"""
        self.add_message("user", content, **extra)
    
    def add_assistant_message(self, content: str, **extra) -> None:
        """添加助手消息"""
        self.add_message("assistant", content, **extra)
    
    def set_system_message(self, content: str) -> None:
        """设置系统消息"""
        self.system_message = content
    
    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """获取消息列表
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            消息列表
        """
        if include_system and self.system_message:
            return [
                {"role": "system", "content": self.system_message},
                *self.messages
            ]
        return self.messages.copy()
    
    def export(self) -> Dict[str, Any]:
        """导出完整会话数据
        
        Returns:
            包含所有信息的字典
        """
        return {
            "messages": self.get_messages(include_system=True),
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "message_count": len(self.messages)
        }
    
    def clear(self, clear_system: bool = False) -> None:
        """清空历史
        
        Args:
            clear_system: 是否清空系统消息
        """
        self.messages.clear()
        if clear_system:
            self.system_message = None
        self.metadata.clear()
    
    def __len__(self) -> int:
        """返回消息数量（不包含系统消息）"""
        return len(self.messages)
    
    def __str__(self) -> str:
        return f"ConversationHistory(messages={len(self.messages)}, system={'Yes' if self.system_message else 'No'})"


# ============================================================================
# 压缩策略相关数据模型
# ============================================================================

@dataclass
class CompressContext:
    """压缩上下文
    
    包含执行压缩所需的所有信息。
    """
    messages: List[Dict[str, str]]
    max_tokens: int
    token_estimator: Callable[[str], int]
    current_tokens: int
    metadata: Optional[Dict[str, Any]] = None
    
    def estimate_message_tokens(self, message: Dict[str, str]) -> int:
        """估算单条消息的token数"""
        content = message.get("content", "")
        return self.token_estimator(content) + 4  # 4为格式化开销


@dataclass
class CompressResult:
    """压缩结果
    
    记录压缩前后的状态和被移除的消息。
    """
    kept_messages: List[Dict[str, str]]
    removed_messages: List[Dict[str, str]]
    tokens_before: int
    tokens_after: int
    compression_ratio: float
    
    @property
    def saved_tokens(self) -> int:
        """节省的token数"""
        return self.tokens_before - self.tokens_after
    
    def __str__(self) -> str:
        return (
            f"CompressResult("
            f"kept={len(self.kept_messages)}, "
            f"removed={len(self.removed_messages)}, "
            f"tokens: {self.tokens_before}->{self.tokens_after}, "
            f"ratio={self.compression_ratio:.2%})"
        )


# ============================================================================
# 辅助函数
# ============================================================================

def create_user_message(content: str, **metadata) -> Dict[str, str]:
    """创建用户消息
    
    Args:
        content: 消息内容
        **metadata: 额外的元数据
        
    Returns:
        Dict: 消息字典
    """
    msg = {"role": "user", "content": content}
    if metadata:
        msg["metadata"] = metadata
    return msg


def create_assistant_message(content: str, **metadata) -> Dict[str, str]:
    """创建助手消息
    
    Args:
        content: 消息内容
        **metadata: 额外的元数据
        
    Returns:
        Dict: 消息字典
    """
    msg = {"role": "assistant", "content": content}
    if metadata:
        msg["metadata"] = metadata
    return msg


def create_system_message(content: str, **metadata) -> Dict[str, str]:
    """创建系统消息
    
    Args:
        content: 消息内容
        **metadata: 额外的元数据
        
    Returns:
        Dict: 消息字典
    """
    msg = {"role": "system", "content": content}
    if metadata:
        msg["metadata"] = metadata
    return msg
