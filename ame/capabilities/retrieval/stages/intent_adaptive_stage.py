"""
Capabilities Layer - Intent Adaptive Stage

意图自适应阶段
"""

import logging
from typing import List, Dict, Any, Optional

from .base import StageBase
from ame.foundation.retrieval import RetrievalResult
from ame.foundation.nlp.ner import NERBase

logger = logging.getLogger(__name__)


class IntentAdaptiveStage(StageBase):
    """
    意图自适应阶段
    
    职责：
    1. 识别查询意图（事实性/时序性/关系性）
    2. 动态调整分数权重
    3. 优化召回质量
    """
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        "factual": ["是什么", "定义", "含义", "概念", "介绍"],
        "temporal": ["什么时候", "何时", "最近", "之前", "历史", "时间"],
        "relational": ["关系", "联系", "影响", "相关", "关联", "导致"]
    }
    
    # 意图权重调整策略
    WEIGHT_ADJUSTMENTS = {
        "factual": {"vector": 1.2, "graph": 0.8},
        "temporal": {"vector": 1.0, "graph": 1.0},
        "relational": {"vector": 0.8, "graph": 1.2}
    }
    
    def __init__(self, ner_extractor: Optional[NERBase] = None):
        """
        初始化意图自适应阶段
        
        Args:
            ner_extractor: NER 提取器（用于实体密度计算）
        """
        self.ner = ner_extractor
        
        logger.debug("IntentAdaptiveStage 初始化")
    
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        执行意图自适应调整
        """
        if not previous_results:
            logger.warning("IntentAdaptiveStage: 没有前序结果")
            return []
        
        logger.debug(f"IntentAdaptiveStage: 处理 {len(previous_results)} 个结果")
        
        # 1. 识别查询意图
        intent = await self._classify_intent(query)
        
        logger.info(f"IntentAdaptiveStage: 识别意图为 {intent}")
        
        # 2. 获取权重调整策略
        adjustments = self.WEIGHT_ADJUSTMENTS.get(
            intent,
            {"vector": 1.0, "graph": 1.0}
        )
        
        # 3. 应用调整
        for result in previous_results:
            stage = result.metadata.get("stage", "")
            
            if "Vector" in stage:
                result.score *= adjustments["vector"]
                result.metadata["intent_adjustment"] = adjustments["vector"]
            elif "Graph" in stage:
                result.score *= adjustments["graph"]
                result.metadata["intent_adjustment"] = adjustments["graph"]
        
        # 4. 重新排序
        previous_results.sort(key=lambda x: x.score, reverse=True)
        
        # 5. 更新元数据
        for result in previous_results:
            result.metadata["detected_intent"] = intent
        
        logger.info(f"IntentAdaptiveStage: 完成意图自适应调整")
        
        return previous_results
    
    async def _classify_intent(self, query: str) -> str:
        """
        意图分类
        
        规则：
        - 事实性（factual）：包含 "是什么"、"如何" 等
        - 时序性（temporal）：包含时间词
        - 关系性（relational）：包含 "关系"、"联系" 等，或实体密度高
        """
        query_lower = query.lower()
        
        # 规则1: 关键词匹配
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in query_lower for kw in keywords):
                logger.debug(f"通过关键词匹配识别意图: {intent_type}")
                return intent_type
        
        # 规则2: 实体密度检测（高实体密度 → 关系性查询）
        if self.ner:
            try:
                entities = await self.ner.extract(query)
                entity_count = len(entities)
                
                if entity_count >= 3:
                    logger.debug(f"通过实体密度识别意图: relational (实体数={entity_count})")
                    return "relational"
                
            except Exception as e:
                logger.warning(f"实体提取失败: {e}")
        
        # 默认：事实性
        logger.debug("默认意图: factual")
        return "factual"
    
    def get_name(self) -> str:
        return "IntentAdaptive"
