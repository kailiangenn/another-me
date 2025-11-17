"""
Capabilities Layer - Vector Retrieval Stage

向量召回阶段
"""

import logging
from typing import List, Dict, Any, Optional

from .base import StageBase
from ame.foundation.retrieval import RetrievalResult, VectorRetriever

logger = logging.getLogger(__name__)


class VectorRetrievalStage(StageBase):
    """
    向量召回阶段
    
    职责：
    1. 向量化查询
    2. Faiss 检索
    3. 返回候选集（通常 top_k * 2）
    """
    
    def __init__(self, vector_retriever: VectorRetriever, weight: float = 1.0):
        """
        初始化向量召回阶段
        
        Args:
            vector_retriever: 向量检索器实例
            weight: 分数权重（默认 1.0）
        """
        self.retriever = vector_retriever
        self.weight = weight
        
        logger.debug(f"VectorRetrievalStage 初始化 (weight={weight})")
    
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        执行向量召回
        
        Args:
            query: 查询文本
            previous_results: 前序结果（向量阶段通常是首阶段，忽略此参数）
            context: 上下文信息
        
        Returns:
            向量检索结果
        """
        top_k = context.get("top_k", 10)
        
        # 召回更多用于后续融合
        recall_k = top_k * 2
        
        logger.debug(f"VectorRetrievalStage: 召回 top_{recall_k} 结果")
        
        try:
            results = await self.retriever.retrieve(
                query=query,
                top_k=recall_k
            )
            
            # 应用权重
            for r in results:
                r.score *= self.weight
                r.metadata["stage"] = self.get_name()
                r.metadata["original_score"] = r.score / self.weight if self.weight != 0 else 0
            
            logger.info(f"VectorRetrievalStage: 检索到 {len(results)} 个结果")
            
            return results
            
        except Exception as e:
            logger.error(f"VectorRetrievalStage 执行失败: {e}", exc_info=True)
            return []
    
    def get_name(self) -> str:
        return "VectorRetrieval"
