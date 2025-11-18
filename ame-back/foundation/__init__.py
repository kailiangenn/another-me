"""
Foundation Layer - 基础能力层

提供原子化的技术能力，无业务逻辑，可独立使用和测试。

模块：
- storage: 存储能力（向量、图谱、元数据）
- nlp: NLP 基础能力（NER、情绪识别、文本处理）
- llm: LLM 调用能力
- embedding: 向量化能力
- inference: 推理框架能力（级联推理、规则引擎）
- utils: 工具函数
"""

__version__ = "0.1.0"

# Inference
from .inference import CascadeInferenceEngine, InferenceLevel, InferenceResult

# LLM
from .llm import LLMCallerBase, OpenAICaller

# Storage
from .storage import StorageBase, VectorStore, GraphStore, MetadataStore

# Embedding
from .embedding import EmbeddingBase, OpenAIEmbedding

# Retrieval
from .retrieval import RetrieverBase, RetrievalResult, VectorRetriever, GraphRetriever

# NLP
from .nlp.emotion import EmotionDetectorBase, HybridEmotionDetector
from .nlp.ner import NERBase, HybridNER, Entity

# Utils
from .utils import (
    now, to_iso, from_iso,
    clean_text, truncate_text, count_tokens,
    validate_doc_id, validate_text, validate_score,
)

__all__ = [
    # Inference
    "CascadeInferenceEngine",
    "InferenceLevel",
    "InferenceResult",
    
    # LLM
    "LLMCallerBase",
    "OpenAICaller",
    
    # Storage
    "StorageBase",
    "VectorStore",
    "GraphStore",
    "MetadataStore",
    
    # Embedding
    "EmbeddingBase",
    "OpenAIEmbedding",
    
    # Retrieval
    "RetrieverBase",
    "RetrievalResult",
    "VectorRetriever",
    "GraphRetriever",
    
    # NLP
    "EmotionDetectorBase",
    "HybridEmotionDetector",
    "NERBase",
    "HybridNER",
    "Entity",
    
    # Utils
    "now",
    "to_iso",
    "from_iso",
    "clean_text",
    "truncate_text",
    "count_tokens",
    "validate_doc_id",
    "validate_text",
    "validate_score",
]
