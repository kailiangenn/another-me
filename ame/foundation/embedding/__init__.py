"""
Embedding模块 - 文本向量化

提供文本向量化能力,支持多种Embedding后端。
"""

from .atomic.base import EmbeddingBase
from .core.models import EmbeddingResult, EmbeddingConfig
from .core.exceptions import EmbeddingError

__all__ = [
    "EmbeddingBase",
    "EmbeddingResult",
    "EmbeddingConfig",
    "EmbeddingError",
]
