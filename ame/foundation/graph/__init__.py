"""
Graph 图谱模块
基于模板方法模式，内化组件能力
"""

# Utils - 数据类 + 枚举
from .utils.models import (
    # 枚举
    NodeLabel,
    RelationType,
    GraphType,
    # 数据类
    GraphNode,
    GraphEdge,
    QueryResult,
)

# Utils - 异常
from .utils.exceptions import (
    StorageError,
    ConnectionError,
    ValidationError,
    QueryError,
    GraphStoreError,
)

# Core - 抽象基类和实现
from .core.base import GraphStoreBase
from .core.falkordb_store import FalkorDBStore

# Components 不对外暴露，仅供内部使用

__all__ = [
    # 枚举
    "NodeLabel",
    "RelationType",
    "GraphType",
    # 数据类
    "GraphNode",
    "GraphEdge",
    "QueryResult",
    # 异常
    "StorageError",
    "ConnectionError",
    "ValidationError",
    "QueryError",
    "GraphStoreError",
    # Core
    "GraphStoreBase",
    "FalkorDBStore",
]
