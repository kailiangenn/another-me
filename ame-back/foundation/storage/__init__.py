"""
Storage - 存储能力

提供统一的存储抽象接口，支持多种存储后端。

核心组件：
- StorageBase: 存储抽象基类
- VectorStoreBase: 向量存储基类 (别名)
- VectorStore: 向量存储（Faiss）
- GraphStore: 图谱存储（FalkorDB）
- MetadataStore: 元数据存储（SQLite）
- DocumentStore: 文档存储（统一CRUD接口）
"""

from .base import StorageBase, StorageConfig
from .vector_store import VectorStore
from .graph_store import GraphStore
from .metadata_store import MetadataStore
from .document_store import DocumentStore

# 别名导出
VectorStoreBase = StorageBase

__all__ = [
    "StorageBase",
    "VectorStoreBase",  # 别名
    "StorageConfig",
    "VectorStore",
    "GraphStore",
    "MetadataStore",
    "DocumentStore",
]
