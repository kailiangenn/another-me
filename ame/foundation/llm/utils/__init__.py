"""LLM Utils - 通用工具

提供数据模型、辅助函数和异常定义。
"""

from .models import (
    # 数据模型
    LLMResponse,
    ConversationHistory,
    CompressContext,
    CompressResult,
    # 辅助函数
    create_user_message,
    create_assistant_message,
    create_system_message,
)

from .exceptions import (
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
)

__all__ = [
    # 数据模型
    "LLMResponse",
    "ConversationHistory",
    "CompressContext",
    "CompressResult",
    # 辅助函数
    "create_user_message",
    "create_assistant_message",
    "create_system_message",
    # 异常
    "LLMError",
    "CallerNotConfiguredError",
    "TokenLimitExceededError",
    "CompressionError",
    "CacheError",
]
