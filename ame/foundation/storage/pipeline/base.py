"""
管道基类

提供通用工具方法:
- 数据验证
- 批量操作
- 时间相关便捷方法
"""

from abc import ABC
from typing import List, Optional
from datetime import datetime

from ..atomic.base import GraphStoreBase
from ..core.validators import GraphDataValidator
from ..core.models import GraphNode, GraphEdge
from ..core.schema import RelationType
from ..core.exceptions import ValidationError


class GraphPipelineBase(ABC):
    """
    图谱管道基类
    
    职责：
    - 提供验证工具
    - 提供批量操作工具
    - 提供时间相关便捷方法
    - 不包含业务逻辑
    """
    
    def __init__(self, store: GraphStoreBase):
        self.store = store
        self.validator = GraphDataValidator()
    
    async def validate_and_create_node(self, node: GraphNode) -> str:
        """验证并创建节点"""
        if not self.validator.validate_node(node):
            raise ValidationError(f"节点验证失败: {node}", node)
        return await self.store.create_node(node)
    
    async def validate_and_create_edge(self, edge: GraphEdge) -> str:
        """验证并创建边"""
        if not self.validator.validate_edge(edge):
            raise ValidationError(f"边验证失败: {edge}", edge)
        return await self.store.create_edge(edge)
    
    async def batch_create_nodes(self, nodes: List[GraphNode], validate: bool = True) -> List[str]:
        """
        批量创建节点
        
        Args:
            nodes: 节点列表
            validate: 是否验证
        
        Returns:
            node_ids: 创建的节点ID列表
        """
        node_ids = []
        for node in nodes:
            if validate:
                node_id = await self.validate_and_create_node(node)
            else:
                node_id = await self.store.create_node(node)
            node_ids.append(node_id)
        return node_ids
    
    async def batch_create_edges(self, edges: List[GraphEdge], validate: bool = True) -> List[str]:
        """
        批量创建边
        
        Args:
            edges: 边列表
            validate: 是否验证
        
        Returns:
            edge_ids: 创建的边ID列表
        """
        edge_ids = []
        for edge in edges:
            if validate:
                edge_id = await self.validate_and_create_edge(edge)
            else:
                edge_id = await self.store.create_edge(edge)
            edge_ids.append(edge_id)
        return edge_ids
    
    async def merge_or_create_node(
        self,
        node: GraphNode,
        merge_keys: List[str]
    ) -> str:
        """
        Merge节点（存在则更新，不存在则创建）
        
        Args:
            node: 待创建/合并的节点
            merge_keys: 用于去重的属性键（如['name']）
        
        Returns:
            node_id: 节点ID
        """
        # 1. 查找是否存在
        search_props = {k: node.properties.get(k) for k in merge_keys if k in node.properties}
        
        if not search_props:
            # 如果没有merge_keys，直接创建
            return await self.validate_and_create_node(node)
        
        existing = await self.store.find_nodes(
            label=node.label,
            properties=search_props,
            limit=1
        )
        
        # 2. 存在则更新，不存在则创建
        if existing:
            await self.store.update_node(existing[0].id, node.properties)
            return existing[0].id
        else:
            return await self.validate_and_create_node(node)
    
    async def batch_merge_nodes(
        self,
        nodes: List[GraphNode],
        merge_keys: List[str]
    ) -> List[str]:
        """
        批量Merge节点
        
        Args:
            nodes: 节点列表
            merge_keys: 去重键
        
        Returns:
            node_ids: 节点ID列表
        """
        node_ids = []
        for node in nodes:
            node_id = await self.merge_or_create_node(node, merge_keys)
            node_ids.append(node_id)
        return node_ids
    
    # ===== 时间相关便捷方法 =====
    
    async def mark_edge_as_invalid(
        self,
        edge_id: str,
        end_time: Optional[datetime] = None
    ) -> bool:
        """
        标记边为失效（设置 valid_until）
        
        应用场景：
        - 生活：不再喜欢某个兴趣
        - 工作：任务完成
        
        Args:
            edge_id: 边ID
            end_time: 失效时间（默认当前时间）
        
        Returns:
            success: 是否更新成功
        """
        if end_time is None:
            end_time = datetime.now()
        
        return await self.store.update_edge(
            edge_id,
            {'valid_until': end_time.isoformat()}
        )
    
    async def get_active_relationships(
        self,
        node_id: str,
        relation: Optional[RelationType] = None,
        at_time: Optional[datetime] = None
    ) -> List[GraphEdge]:
        """
        获取节点的活跃关系（当前或指定时间点有效的关系）
        
        应用场景：
        - 查询用户当前的兴趣
        - 查询正在进行的任务
        
        Args:
            node_id: 节点ID
            relation: 关系类型（可选）
            at_time: 时间点（默认当前时间）
        
        Returns:
            edges: 活跃关系列表
        """
        if at_time is None:
            at_time = datetime.now()
        
        return await self.store.find_valid_edges_at(
            timestamp=at_time,
            source_id=node_id,
            relation=relation
        )
