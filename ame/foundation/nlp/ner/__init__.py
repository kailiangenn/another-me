"""
NER - 命名实体识别

提供多层级命名实体识别能力

核心组件：
- NERBase: NER 抽象基类
- Entity: 实体数据结构
- SimpleNER: 基于 jieba 的快速实体识别
- LLMNER: 基于 LLM 的精确实体识别
- HybridNER: 混合实体识别（jieba → LLM 级联）
"""

from .base import NERBase, Entity
from .simple_ner import SimpleNER
from .llm_ner import LLMNER
from .hybrid_ner import HybridNER

__all__ = [
    "NERBase",
    "Entity",
    "SimpleNER",
    "LLMNER",
    "HybridNER",
]
