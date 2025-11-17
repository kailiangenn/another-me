"""
LLM - LLM 调用能力

提供统一的 LLM 调用接口，支持多种 LLM 提供商。

三层架构：
- Core Layer (核心层): 数据模型、会话管理和异常
- Atomic Layer (原子能力层): 基础不可分的能力单元
- Pipeline Layer (管道能力层): 场景化组合能力

使用指南：
- 对话场景: 使用 SessionPipe
- 文档分析: 使用 DocumentPipe
"""

# ===== Core Layer - 核心层 =====
from .core import (
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
    # 历史管理
    ConversationHistory,
    # 异常
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
)

# ===== Atomic Layer - 原子能力层 =====
from .atomic import (
    # 调用器
    LLMCallerBase,
    StreamCaller,
    OpenAICaller,
    # 策略
    CacheStrategy,
    CompressStrategy,
    SessionCompressStrategy,
    DocumentCompressStrategy,
    ChunkingCompressStrategy,
    RetryStrategy,
)

# ===== Pipeline Layer - 管道能力层 =====
from .pipeline import (
    PipelineBase,
    SessionPipe,
    DocumentPipe,
)

__all__ = [
    # ===== Core =====
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
    
    # ===== Atomic Layer =====
    "LLMCallerBase",
    "StreamCaller",
    "OpenAICaller",
    "CacheStrategy",
    "CompressStrategy",
    "SessionCompressStrategy",
    "DocumentCompressStrategy",
    "ChunkingCompressStrategy",
    "RetryStrategy",
    
    # ===== Pipeline Layer =====
    "PipelineBase",
    "SessionPipe",
    "DocumentPipe",
]
