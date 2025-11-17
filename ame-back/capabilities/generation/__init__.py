"""
Generation - 生成能力

提供基于检索的生成、风格化生成等能力

核心组件：
- RAGGenerator: RAG 生成器（检索增强生成）
- StyleGenerator: 风格化文本生成器
"""

from .rag_generator import RAGGenerator
from .style_generator import StyleGenerator

__all__ = [
    "RAGGenerator",
    "StyleGenerator",
]
