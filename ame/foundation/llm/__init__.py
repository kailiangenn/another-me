"""LLM - LLM 调用能力

三层结构：
- utils/ - 通用工具（数据模型和异常）
- core/ - 核心实现（调用器基类和具体实现）
- components/ - 组件层（提示词、历史管理、策略）

使用指南：
- 对话模式: caller.chat("你好")
- 流式对话: caller.chat_stream("讲个故事")
- Agent任务: caller.agent(prompt="提取人名", task_type="ner")
- 历史管理: ConversationHistory（数据）+ HistoryManager（功能）
"""

# ===== Utils Layer - 通用工具 =====
from .utils import (
    # 数据模型
    LLMResponse,
    ConversationHistory,
    CompressContext,
    CompressResult,
    # 辅助函数
    create_user_message,
    create_assistant_message,
    create_system_message,
    # 异常
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
)

# ===== Core Layer - 核心实现 =====
from .core import (
    BaseLLMCaller,
    OpenAICaller,
)

# ===== Components Layer - 组件层 =====
from .components import (
    # 提示词和管理器
    PromptBuilder,
    HistoryManager,
    CompressionStrategy,
    # 策略组件
    CacheStrategy,
    CompressStrategy,
    RetryStrategy,
)

__all__ = [
    # ===== Utils =====
    "LLMResponse",
    "ConversationHistory",
    "CompressContext",
    "CompressResult",
    "create_user_message",
    "create_assistant_message",
    "create_system_message",
    "LLMError",
    "CallerNotConfiguredError",
    "TokenLimitExceededError",
    "CompressionError",
    "CacheError",
    
    # ===== Core =====
    "BaseLLMCaller",
    "OpenAICaller",
    
    # ===== Components =====
    "PromptBuilder",
    "HistoryManager",
    "CompressionStrategy",
    "CacheStrategy",
    "CompressStrategy",
    "RetryStrategy",
]
