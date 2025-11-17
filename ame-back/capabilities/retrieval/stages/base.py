"""
Capabilities Layer - Retrieval Stage Base

检索阶段抽象基类（责任链模式）
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ame.foundation.retrieval import RetrievalResult


class StageBase(ABC):
    """
    检索阶段抽象基类
    
    设计模式：责任链模式
    每个阶段接收前序结果，处理后输出新结果
    """
    
    @abstractmethod
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        处理检索阶段
        
        Args:
            query: 查询文本
            previous_results: 前序阶段结果（None 表示首阶段）
            context: 上下文信息（共享数据）
        
        Returns:
            当前阶段输出结果
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        阶段名称
        
        Returns:
            阶段标识名称
        """
        pass
