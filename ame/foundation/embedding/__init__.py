"""
Embedding 模块 - 文本向量化
Foundation Layer
"""
from .base import EmbeddingBase
from .openai_embedding import OpenAIEmbedding

__all__ = [
    "EmbeddingBase",
    "OpenAIEmbedding",
]
