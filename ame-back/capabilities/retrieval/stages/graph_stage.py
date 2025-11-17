"""
Capabilities Layer - Graph Retrieval Stage

图谱召回阶段
"""

import logging
from typing import List, Dict, Any, Optional

from .base import StageBase
from ame.foundation.retrieval import RetrievalResult, GraphRetriever

logger = logging.getLogger(__name__)


class GraphRetrievalStage(StageBase):
    """
    图谱召回阶段
    
    职责：
    1. NER 提取实体
    2. 图谱检索
    3. 多跳推理（可选）
    """
    
    def __init__(self, graph_retriever: GraphRetriever, weight: float = 1.0):
        """
        初始化图谱召回阶段
        
        Args:
            graph_retriever: 图谱检索器实例
            weight: 分数权重（默认 1.0）
        """
        self.retriever = graph_retriever
        self.weight = weight
        
        logger.debug(f"GraphRetrievalStage 初始化 (weight={weight})")
    
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        执行图谱召回
        
        Args:
            query: 查询文本
            previous_results: 前序结果（可为None）
            context: 上下文信息
        
        Returns:
            图谱检索结果（与前序结果合并）
        """
        top_k = context.get("top_k", 10)
        recall_k = top_k * 2
        
        logger.debug(f"GraphRetrievalStage: 召回 top_{recall_k} 结果")
        
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
            
            logger.info(f"GraphRetrievalStage: 检索到 {len(results)} 个结果")
            
            # 如果有前序结果，合并
            if previous_results:
                results = previous_results + results
            
            return results
            
        except Exception as e:
            logger.error(f"GraphRetrievalStage 执行失败: {e}", exc_info=True)
            return previous_results if previous_results else []
    
    def get_name(self) -> str:
        return "GraphRetrieval"
