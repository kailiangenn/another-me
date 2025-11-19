"""
存储模块 - 图数据库抽象与实现

架构设计:
- core/: 核心层（数据模型、Schema、异常定义）
- atomic/: 原子层（具体数据库实现）
- pipeline/: 管道层（轻量数据操作编排）

提供统一的图数据库接口，支持：
- 节点和边的CRUD操作
- 图遍历和路径查询
- 时间范围查询（关系演化分析）
- 生活图谱和工作图谱隔离

特性:
- 基于FalkorDB实现
- 支持关系时间属性（valid_from/valid_until）
- 预定义Schema（封闭节点和关系类型）
- 自动创建Graph（不存在则创建）
"""

# 核心模型
from .core.models import (
    GraphNode,
    GraphEdge,
    GraphPath,
    SubGraph,
    QueryResult,
)

# Schema定义
from .core.schema import (
    NodeLabel,
    RelationType,
    GraphSchema,
    RelationTimeSemantics,
)

# 异常
from .core.exceptions import (
    StorageError,
    ConnectionError,
    ValidationError,
    QueryError,
)

# 原子存储
from .atomic.base import GraphStoreBase
from .atomic.falkordb_store import FalkorDBStore

# 管道
from .pipeline.base import GraphPipelineBase
from .pipeline.life_graph_pipeline import LifeGraphPipeline
from .pipeline.work_graph_pipeline import WorkGraphPipeline

__all__ = [
    # 核心数据模型
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
    
    # 原子存储
    "GraphStoreBase",
    "FalkorDBStore",
    
    # 管道
    "GraphPipelineBase",
    "LifeGraphPipeline",
    "WorkGraphPipeline",
]
