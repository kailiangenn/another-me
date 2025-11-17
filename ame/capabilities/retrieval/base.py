"""
Retrieval 抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class RetrievalStrategy(Enum):
    """检索策略"""
    VECTOR_ONLY = "vector_only"
    GRAPH_ONLY = "graph_only"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


@dataclass
class RetrievalResult:
    """检索结果"""
    doc_id: str
    content: str
    score: float
    source: str  # "vector", "graph", "hybrid"
    
    # 额外信息
    metadata: Optional[Dict[str, Any]] = None
    matched_entities: Optional[List[str]] = None
    distance: Optional[int] = None  # 图谱跳数


class RetrieverBase(ABC):
    """检索器抽象基类"""
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        rerank: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        检索文档
        
        Args:
            query: 查询内容
            top_k: 返回数量
            strategy: 检索策略
            rerank: 是否重排序
            filters: 过滤条件
        
        Returns:
            List[RetrievalResult]: 检索结果
        """
        pass
