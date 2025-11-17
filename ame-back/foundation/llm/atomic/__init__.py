"""
Atomic Layer - 原子能力层

提供不可再分的基础能力单元：
- 模型调用器（Caller）
- 策略组件（Strategy）
"""

from .caller import LLMCallerBase, StreamCaller
from .openai_caller import OpenAICaller
from .strategy import (
    CacheStrategy,
    CompressStrategy,
    SessionCompressStrategy,
    DocumentCompressStrategy,
    ChunkingCompressStrategy,
    RetryStrategy,
)

__all__ = [
    # 调用器
    "LLMCallerBase",
    "StreamCaller",
    "OpenAICaller",
    # 策略
    "CacheStrategy",
    "CompressStrategy",
    "SessionCompressStrategy",
    "DocumentCompressStrategy",
    "ChunkingCompressStrategy",
    "RetryStrategy",
]
