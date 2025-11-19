"""
图数据库抽象基类

定义统一的图数据库接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..core.models import GraphNode, GraphEdge, SubGraph
from ..core.schema import NodeLabel, RelationType


class GraphStoreBase(ABC):
    """
    图数据库抽象接口 - 纯数据操作，无业务逻辑
    
    所有具体实现需要实现以下方法：
    - 连接管理
    - 节点CRUD
    - 边CRUD
    - 图查询
    """
    
    # ===== 连接管理 =====
    
    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    # ===== 节点基础操作 =====
    
    @abstractmethod
    async def create_node(self, node: GraphNode) -> str:
        """
        创建节点
        
        Args:
            node: 节点对象
        
        Returns:
            node_id: 创建的节点ID
        """
        pass
    
    @abstractmethod
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """
        根据ID获取节点
        
        Args:
            node_id: 节点ID
        
        Returns:
            node: 节点对象，不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """
        更新节点属性
        
        Args:
            node_id: 节点ID
            properties: 要更新的属性
        
        Returns:
            success: 是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """
        删除节点
        
        Args:
            node_id: 节点ID
        
        Returns:
            success: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def find_nodes(
        self,
        label: Optional[NodeLabel] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[GraphNode]:
        """
        查找节点
        
        Args:
            label: 节点标签（可选）
            properties: 属性过滤条件（可选）
            limit: 最大返回数量
        
        Returns:
            nodes: 节点列表
        """
        pass
    
    # ===== 边基础操作 =====
    
    @abstractmethod
    async def create_edge(self, edge: GraphEdge) -> str:
        """
        创建边
        
        Args:
            edge: 边对象
        
        Returns:
            edge_id: 创建的边ID
        """
        pass
    
    @abstractmethod
    async def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """
        获取边
        
        Args:
            edge_id: 边ID
        
        Returns:
            edge: 边对象，不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_edge(self, edge_id: str, properties: Dict[str, Any]) -> bool:
        """
        更新边属性
        
        Args:
            edge_id: 边ID
            properties: 要更新的属性
        
        Returns:
            success: 是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_edge(self, edge_id: str) -> bool:
        """
        删除边
        
        Args:
            edge_id: 边ID
        
        Returns:
            success: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation: Optional[RelationType] = None,
        only_valid: bool = False
    ) -> List[GraphEdge]:
        """
        查找边
        
        Args:
            source_id: 源节点ID（可选）
            target_id: 目标节点ID（可选）
            relation: 关系类型（可选）
            only_valid: 是否只返回当前有效的边
        
        Returns:
            edges: 边列表
        """
        pass
    
    # ===== 图查询（原子操作）===
    
    @abstractmethod
    async def get_neighbors(
        self,
        node_id: str,
        relation: Optional[RelationType] = None,
        direction: str = "outgoing"  # outgoing/incoming/both
    ) -> List[GraphNode]:
        """
        获取邻居节点（1跳）
        
        Args:
            node_id: 起始节点ID
            relation: 关系类型过滤（可选）
            direction: 遍历方向
        
        Returns:
            neighbors: 邻居节点列表
        """
        pass
    
    @abstractmethod
    async def get_edges_between(
        self,
        source_id: str,
        target_id: str
    ) -> List[GraphEdge]:
        """
        获取两个节点之间的所有边
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
        
        Returns:
            edges: 边列表
        """
        pass
    
    # ===== 时间范围查询 =====
    
    @abstractmethod
    async def find_valid_edges_at(
        self,
        timestamp: datetime,
        source_id: Optional[str] = None,
        relation: Optional[RelationType] = None
    ) -> List[GraphEdge]:
        """
        查找在指定时间点有效的边
        
        Args:
            timestamp: 目标时间点
            source_id: 源节点ID（可选）
            relation: 关系类型（可选）
        
        Returns:
            edges: 有效边列表
        """
        pass
    
    # ===== 原生查询 =====
    
    @abstractmethod
    async def execute_cypher(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        执行原生Cypher查询
        
        Args:
            query: Cypher查询语句
            params: 查询参数
        
        Returns:
            result: 查询结果
        """
        pass
