"""
图数据模型定义

包含:
- GraphNode: 图节点
- GraphEdge: 图边（包含时间属性）
- GraphPath: 图路径
- SubGraph: 子图
- QueryResult: 查询结果
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from .schema import NodeLabel, RelationType


@dataclass
class GraphNode:
    """
    图节点
    
    注意：label 必须是 NodeLabel 枚举值
    """
    label: NodeLabel                    # 节点类型（枚举）
    properties: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None           # FalkorDB生成的ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class GraphEdge:
    """
    图边
    
    时间属性说明：
    - valid_from: 关系生效时间（关系建立的时间）
    - valid_until: 关系失效时间（可选，None表示仍有效）
    
    生活场景示例：
    - INTERESTED_IN: valid_from=开始喜欢的时间, valid_until=不再喜欢的时间
    - KNOWS: valid_from=认识的时间, valid_until=失联时间
    
    工作场景示例：
    - WORKS_ON: valid_from=开始时间, valid_until=完成时间
    - DEPENDS_ON: valid_from=依赖建立时间, valid_until=依赖解除时间
    
    注意：relation 必须是 RelationType 枚举值
    """
    source_id: str                     # 源节点ID
    target_id: str                     # 目标节点ID
    relation: RelationType             # 关系类型（枚举）
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    
    # 时间属性
    valid_from: datetime = field(default_factory=datetime.now)  # 生效时间
    valid_until: Optional[datetime] = None                      # 失效时间（None=仍有效）
    
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def is_valid_at(self, timestamp: datetime) -> bool:
        """判断在指定时间点关系是否有效"""
        if timestamp < self.valid_from:
            return False
        if self.valid_until and timestamp > self.valid_until:
            return False
        return True
    
    def is_currently_valid(self) -> bool:
        """判断当前是否有效"""
        return self.is_valid_at(datetime.now())
    
    def duration(self) -> Optional[timedelta]:
        """计算关系持续时间"""
        if self.valid_until:
            return self.valid_until - self.valid_from
        return None


@dataclass
class GraphPath:
    """图路径（多跳查询结果）"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    length: int
    
    def __post_init__(self):
        if self.length == 0:
            self.length = len(self.edges)


@dataclass
class SubGraph:
    """子图"""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def node_count(self) -> int:
        """节点数量"""
        return len(self.nodes)
    
    def edge_count(self) -> int:
        """边数量"""
        return len(self.edges)


@dataclass
class QueryResult:
    """通用查询结果"""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    paths: List[GraphPath] = field(default_factory=list)
    subgraphs: List[SubGraph] = field(default_factory=list)
    aggregations: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
