"""
Capabilities Layer - Diversity Filter Stage

多样性过滤阶段（MMR算法）
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base import StageBase
from ame.foundation.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class DiversityFilterStage(StageBase):
    """
    多样性过滤阶段
    
    职责：
    1. 使用 MMR 算法控制多样性
    2. 避免结果冗余
    """
    
    def __init__(self, lambda_param: float = 0.7):
        """
        初始化多样性过滤阶段
        
        Args:
            lambda_param: 相关性权重（0.0-1.0）
                - 1.0: 完全相关性优先
                - 0.0: 完全多样性优先
                - 0.7: 平衡（推荐）
        """
        self.lambda_param = lambda_param
        
        logger.debug(f"DiversityFilterStage 初始化 (lambda={lambda_param})")
    
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        执行多样性过滤
        
        使用 MMR (Maximal Marginal Relevance) 算法
        """
        if not previous_results or len(previous_results) <= 1:
            logger.debug("DiversityFilterStage: 结果数量 <= 1，跳过多样性过滤")
            return previous_results if previous_results else []
        
        logger.debug(f"DiversityFilterStage: 过滤 {len(previous_results)} 个结果")
        
        try:
            filtered = self._mmr_filter(previous_results)
            
            logger.info(f"DiversityFilterStage: 过滤完成，保留 {len(filtered)} 个结果")
            
            return filtered
            
        except Exception as e:
            logger.error(f"DiversityFilterStage 执行失败: {e}", exc_info=True)
            return previous_results
    
    def _mmr_filter(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        MMR (Maximal Marginal Relevance) 算法
        
        算法流程：
        1. 选择最相关的文档
        2. 迭代选择：相关性高 且 与已选文档相似度低 的文档
        3. MMR 分数 = λ * relevance - (1-λ) * max_similarity
        """
        if len(results) <= 1:
            return results
        
        # 1. 选择最相关的文档
        selected = [results[0]]
        remaining = results[1:]
        
        # 2. 迭代选择
        while remaining and len(selected) < len(results):
            max_mmr = -float('inf')
            max_idx = 0
            
            for i, candidate in enumerate(remaining):
                # 相关性分数（归一化到 0-1）
                relevance = candidate.score
                
                # 与已选文档的最大相似度
                max_sim = max(
                    self._similarity(candidate, selected_doc)
                    for selected_doc in selected
                )
                
                # MMR 分数
                mmr = self.lambda_param * relevance - (1 - self.lambda_param) * max_sim
                
                if mmr > max_mmr:
                    max_mmr = mmr
                    max_idx = i
            
            # 选择 MMR 最高的文档
            selected_doc = remaining.pop(max_idx)
            selected_doc.metadata["mmr_score"] = max_mmr
            selected.append(selected_doc)
        
        return selected
    
    def _similarity(self, doc1: RetrievalResult, doc2: RetrievalResult) -> float:
        """
        计算文档相似度（简化版：词重叠 Jaccard 相似度）
        """
        words1 = set(re.findall(r'\w+', doc1.content.lower()))
        words2 = set(re.findall(r'\w+', doc2.content.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0
    
    def get_name(self) -> str:
        return "DiversityFilter"
