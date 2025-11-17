"""
Capabilities Layer - Fusion Stage

融合阶段（RRF + 加权求和）
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .base import StageBase
from ame.foundation.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class FusionStage(StageBase):
    """
    融合阶段
    
    职责：
    1. 合并多源结果（向量 + 图谱）
    2. 按 doc_id 去重
    3. 分数融合（加权求和 / RRF）
    """
    
    def __init__(self, fusion_method: str = "weighted_sum"):
        """
        初始化融合阶段
        
        Args:
            fusion_method: 融合方法
                - weighted_sum: 加权求和
                - rrf: Reciprocal Rank Fusion
        """
        self.fusion_method = fusion_method
        
        logger.debug(f"FusionStage 初始化 (method={fusion_method})")
    
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        执行融合
        
        Args:
            query: 查询文本
            previous_results: 前序结果（必须包含多源数据）
            context: 上下文信息
        
        Returns:
            融合后的结果
        """
        if not previous_results:
            logger.warning("FusionStage: 没有前序结果，跳过融合")
            return []
        
        logger.debug(f"FusionStage: 融合 {len(previous_results)} 个结果")
        
        if self.fusion_method == "rrf":
            fused = self._rrf_fusion(previous_results)
        else:
            fused = self._weighted_sum_fusion(previous_results)
        
        # 排序
        fused.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"FusionStage: 融合后 {len(fused)} 个结果")
        
        return fused
    
    def _weighted_sum_fusion(
        self,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        加权求和融合
        
        规则：
        1. 按 doc_id 聚合
        2. 同文档的不同来源分数累加
        3. 去重
        """
        # 按 doc_id 聚合
        score_map: Dict[str, Dict] = defaultdict(lambda: {
            "score": 0.0,
            "result": None,
            "sources": []
        })
        
        for result in results:
            doc_id = result.metadata.get("doc_id", "")
            
            if not doc_id:
                # 没有 doc_id 的结果独立处理
                doc_id = f"unknown_{id(result)}"
            
            score_map[doc_id]["score"] += result.score
            score_map[doc_id]["sources"].append(result.metadata.get("stage", "unknown"))
            
            # 保留第一个结果的内容
            if score_map[doc_id]["result"] is None:
                score_map[doc_id]["result"] = result
        
        # 构建融合结果
        fused = []
        for doc_id, data in score_map.items():
            result = data["result"]
            result.score = data["score"]
            result.metadata["fusion_method"] = self.fusion_method
            result.metadata["fused_sources"] = list(set(data["sources"]))
            result.metadata["stage"] = self.get_name()
            fused.append(result)
        
        return fused
    
    def _rrf_fusion(
        self,
        results: List[RetrievalResult],
        k: int = 60
    ) -> List[RetrievalResult]:
        """
        RRF (Reciprocal Rank Fusion) 融合
        
        算法：
        score = sum(1 / (k + rank))
        
        优势：不依赖原始分数，更鲁棒
        
        Args:
            results: 输入结果
            k: RRF 参数（默认 60）
        """
        # 按来源分组
        source_groups = defaultdict(list)
        for result in results:
            source = result.metadata.get("stage", "unknown")
            source_groups[source].append(result)
        
        # 计算 RRF 分数
        rrf_scores = defaultdict(float)
        doc_map = {}
        
        for source, group in source_groups.items():
            # 按原始分数排序
            group.sort(key=lambda x: x.score, reverse=True)
            
            for rank, result in enumerate(group):
                doc_id = result.metadata.get("doc_id", f"unknown_{id(result)}")
                rrf_scores[doc_id] += 1.0 / (k + rank + 1)
                
                if doc_id not in doc_map:
                    doc_map[doc_id] = result
        
        # 构建融合结果
        fused = []
        for doc_id, score in rrf_scores.items():
            result = doc_map[doc_id]
            result.score = score
            result.metadata["fusion_method"] = "rrf"
            result.metadata["stage"] = self.get_name()
            fused.append(result)
        
        return fused
    
    def get_name(self) -> str:
        return "Fusion"
