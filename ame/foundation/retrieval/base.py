"""
Foundation Layer - Retrieval Base

提供检索器抽象基类和统一数据结构
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RetrievalResult:
    """
    统一检索结果数据结构
    
    Attributes:
        content: 文档内容
        metadata: 元数据（doc_id, timestamp 等）
        score: 相关性分数（0-1）
        source: 来源标识（vector/graph/hybrid）
    """
    content: str
    metadata: Dict[str, Any]
    score: float
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
            "source": self.source
        }


class RetrieverBase(ABC):
    """
    检索器抽象基类
    
    Foundation 层原子能力：
    - 无状态设计
    - 无业务逻辑
    - 可独立使用
    """
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件
            **kwargs: 其他参数
            
        Returns:
            检索结果列表
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取检索器名称
        
        Returns:
            检索器标识名称
        """
        pass
