"""
核心模块

包含:
- 数据模型定义
- Schema规范
- 异常定义
- 数据验证器
"""

from .models import GraphNode, GraphEdge, GraphPath, SubGraph, QueryResult
from .schema import NodeLabel, RelationType, GraphSchema, RelationTimeSemantics
from .exceptions import StorageError, ConnectionError, ValidationError, QueryError
from .validators import GraphDataValidator

__all__ = [
    # 数据模型
    "GraphNode",
    "GraphEdge",
    "GraphPath",
    "SubGraph",
    "QueryResult",
    
    # Schema
    "NodeLabel",
    "RelationType",
    "GraphSchema",
    "RelationTimeSemantics",
    
    # 异常
    "StorageError",
    "ConnectionError",
    "ValidationError",
    "QueryError",
    
    # 验证器
    "GraphDataValidator",
]
