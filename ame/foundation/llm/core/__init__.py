"""
LLM 核心模块

包含数据模型、会话历史和异常定义。
"""

from .models import (
    # 枚举
    CallMode,
    # 数据模型
    LLMResponse,
    CompressContext,
    CompressResult,
    PipelineContext,
    PipelineResult,
    # 辅助函数
    create_user_message,
    create_assistant_message,
    create_system_message,
)

from .history import ConversationHistory

from .exceptions import (
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
)

__all__ = [
    # 枚举
    "CallMode",
    # 响应
    "LLMResponse",
    # 压缩
    "CompressContext",
    "CompressResult",
    # 管道
    "PipelineContext",
    "PipelineResult",
    # 辅助函数
    "create_user_message",
    "create_assistant_message",
    "create_system_message",
    # 历史管理
    "ConversationHistory",
    # 异常
    "LLMError",
    "CallerNotConfiguredError",
    "TokenLimitExceededError",
    "CompressionError",
    "CacheError",
]
