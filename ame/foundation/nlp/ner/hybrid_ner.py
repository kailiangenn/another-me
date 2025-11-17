"""
Hybrid NER - 混合实体识别

整合 Simple NER 和 LLM NER，使用级联策略

特性：
- 快速 jieba 识别（优先）
- LLM 深度分析（兜底）
- 自动融合去重
"""

import logging
from typing import List, Optional

from ame.foundation.llm import LLMCallerBase
from ame.foundation.inference import CascadeInferenceEngine, InferenceLevelBase, InferenceResult, InferenceLevel
from .base import NERBase, Entity
from .simple_ner import SimpleNER
from .llm_ner import LLMNER

logger = logging.getLogger(__name__)


class HybridNER(NERBase):
    """混合实体识别器"""
    
    def __init__(
        self,
        llm_caller: Optional[LLMCallerBase] = None,
        min_length: int = 2,
        llm_threshold: int = 100,
        confidence_threshold: float = 0.7
    ):
        self.llm = llm_caller
        self.llm_threshold = llm_threshold
        
        # 创建识别器
        self.simple_ner = SimpleNER(min_length=min_length)
        self.llm_ner = LLMNER(llm_caller) if llm_caller else None
        
        # 创建级联引擎
        if self.llm_ner:
            self.engine = CascadeInferenceEngine(
                confidence_threshold=confidence_threshold,
                enable_cache=True
            )
            self.engine.add_level(SimpleNERLevel(self.simple_ner))
            self.engine.add_level(LLMNERLevel(self.llm_ner))
        
        logger.info(f"HybridNER 初始化 (llm_threshold={llm_threshold})")
    
    async def extract(self, text: str) -> List[Entity]:
        """提取实体"""
        if not text:
            return []
        
        # 短文本直接用 Simple NER
        if len(text) < self.llm_threshold or not self.llm_ner:
            return await self.simple_ner.extract(text)
        
        # 长文本使用级联
        try:
            result = await self.engine.infer(text, {})
            entities = result.value.get("entities", [])
            return self.deduplicate_entities(entities)
        except Exception as e:
            logger.error(f"HybridNER 失败，回退到 Simple: {e}")
            return await self.simple_ner.extract(text)


class SimpleNERLevel(InferenceLevelBase):
    """Simple NER 推理层级"""
    
    def __init__(self, ner: SimpleNER):
        self.ner = ner
    
    async def infer(self, input_data: str, context: dict) -> InferenceResult:
        entities = await self.ner.extract(input_data)
        confidence = 0.8 if len(entities) > 0 else 0.5
        return InferenceResult(
            value={"entities": entities},
            confidence=confidence,
            level=InferenceLevel.RULE,
            metadata={"method": "simple"}
        )
    
    def get_level(self):
        return InferenceLevel.RULE
    
    def get_name(self):
        return "Simple NER"


class LLMNERLevel(InferenceLevelBase):
    """LLM NER 推理层级"""
    
    def __init__(self, ner: LLMNER):
        self.ner = ner
    
    async def infer(self, input_data: str, context: dict) -> InferenceResult:
        entities = await self.ner.extract(input_data)
        return InferenceResult(
            value={"entities": entities},
            confidence=0.95,
            level=InferenceLevel.LLM,
            metadata={"method": "llm"}
        )
    
    def get_level(self):
        return InferenceLevel.LLM
    
    def get_name(self):
        return "LLM NER"
