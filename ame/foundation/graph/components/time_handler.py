"""
时间属性处理器
"""
from typing import Optional, List
from datetime import datetime
from loguru import logger

from ..utils.models import GraphEdge


class TimeHandler:
    """
    时间属性处理器
    处理边的 create_time 和 invalid_time
    """
    
    @staticmethod
    def is_edge_valid(
        edge: GraphEdge, 
        at_time: Optional[datetime] = None
    ) -> bool:
        """判断边在指定时间是否有效"""
        return edge.is_valid(at_time)
    
    @staticmethod
    def filter_valid_edges(
        edges: List[GraphEdge],
        at_time: Optional[datetime] = None
    ) -> List[GraphEdge]:
        """过滤出有效的边"""
        check_time = at_time or datetime.now()
        valid_edges = [e for e in edges if e.is_valid(check_time)]
        logger.debug(f"Filtered {len(valid_edges)}/{len(edges)} valid edges at {check_time}")
        return valid_edges
    
    @staticmethod
    def invalidate_edge(
        edge: GraphEdge,
        invalid_time: Optional[datetime] = None
    ) -> GraphEdge:
        """
        使边失效（设置 invalid_time）
        用于关系演化：不删除边，而是标记失效
        """
        edge.invalid_time = invalid_time or datetime.now()
        edge.properties['invalid_time'] = edge.invalid_time.isoformat()
        logger.debug(f"Edge invalidated: {edge.source_id} -[{edge.relation_type}]-> {edge.target_id}")
        return edge
    
    @staticmethod
    def get_edge_history(
        edges: List[GraphEdge],
        node_id: str,
        relation_type: Optional[str] = None
    ) -> List[GraphEdge]:
        """
        获取边的演化历史
        按时间排序，包含已失效的边
        """
        filtered = [
            e for e in edges
            if (e.source_id == node_id or e.target_id == node_id)
            and (relation_type is None or e.relation_type.value == relation_type)
        ]
        
        # 按 create_time 排序
        sorted_edges = sorted(filtered, key=lambda e: e.create_time)
        logger.debug(f"Found {len(sorted_edges)} edges in history for node {node_id}")
        return sorted_edges
