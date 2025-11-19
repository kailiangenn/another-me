"""
数据验证器
"""

from typing import Tuple
from .models import GraphNode, GraphEdge
from .schema import GraphSchema, NodeLabel, RelationType


class GraphDataValidator:
    """图数据验证器"""
    
    @staticmethod
    def validate_node(node: GraphNode) -> bool:
        """
        验证节点数据有效性
        
        Args:
            node: 待验证的节点
        
        Returns:
            is_valid: 是否有效
        """
        # 1. 验证label是否是NodeLabel枚举
        if not isinstance(node.label, NodeLabel):
            return False
        
        # 2. 验证必需属性
        is_valid, _ = GraphSchema.validate_node(node.label, node.properties)
        return is_valid
    
    @staticmethod
    def validate_edge(edge: GraphEdge) -> bool:
        """
        验证边数据有效性
        
        Args:
            edge: 待验证的边
        
        Returns:
            is_valid: 是否有效
        """
        # 1. 验证relation是否是RelationType枚举
        if not isinstance(edge.relation, RelationType):
            return False
        
        # 2. 验证source_id和target_id不为空
        if not edge.source_id or not edge.target_id:
            return False
        
        # 3. 验证时间属性
        if edge.valid_until and edge.valid_until < edge.valid_from:
            return False  # 失效时间不能早于生效时间
        
        return True
    
    @staticmethod
    def validate_properties(properties: dict) -> bool:
        """
        验证属性字典
        
        Args:
            properties: 属性字典
        
        Returns:
            is_valid: 是否有效
        """
        if not isinstance(properties, dict):
            return False
        
        # 检查属性值类型是否合法（基本类型）
        for key, value in properties.items():
            if not isinstance(key, str):
                return False
            
            # 允许的值类型
            if not isinstance(value, (str, int, float, bool, type(None))):
                return False
        
        return True
