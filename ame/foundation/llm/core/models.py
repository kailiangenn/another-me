"""
LLM 核心数据模型

统一管理 LLM 模块中的所有数据类和枚举类型。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any, AsyncIterator, Callable
from datetime import datetime
from .history import ConversationHistory


# ============================================================================
# 枚举类型
# ============================================================================

class CallMode(Enum):
    """模型调用模式"""
    STREAM = "stream"      # 流式输出
    COMPLETE = "complete"  # 完整等待
    BATCH = "batch"        # 批量处理


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
# 管道相关数据模型
# ============================================================================

@dataclass
class PipelineContext:
    """管道执行上下文
    
    包含管道执行所需的所有信息。
    """
    messages: List[Dict[str, str]]
    max_tokens: int = 4000
    temperature: float = 0.7
    stream: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_api_messages(self) -> List[Dict[str, str]]:
        """转换为API消息格式
        
        从 messages 中移除 metadata 字段，只保留 role 和 content。
        
        Returns:
            适用于 LLM API 的消息列表
        """
        return [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            for msg in self.messages
        ]
    
    @classmethod
    def from_history(cls, history: "ConversationHistory", **kwargs) -> "PipelineContext":
        """从会话历史创建上下文
        
        Args:
            history: ConversationHistory 实例
            **kwargs: 其他参数（temperature, stream 等）
            
        Returns:
            PipelineContext 实例
        """        
        return cls(
            messages=history.messages.copy(),
            metadata=history.metadata.copy(),
            **kwargs
        )


@dataclass
class PipelineResult:
    """管道执行结果"""
    response: Optional[LLMResponse] = None
    stream_iterator: Optional[AsyncIterator[str]] = None
    compressed: bool = False
    cached: bool = False
    compression_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_stream(self) -> bool:
        """是否为流式响应"""
        return self.stream_iterator is not None
    
    def __str__(self) -> str:
        status = "stream" if self.is_stream else "complete"
        flags = []
        if self.cached:
            flags.append("cached")
        if self.compressed:
            flags.append("compressed")
        
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"PipelineResult({status}{flag_str})"


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
