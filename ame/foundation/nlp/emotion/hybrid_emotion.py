"""
混合情绪识别器

整合规则和 LLM 识别器，使用级联推理框架

特性：
- 快速规则识别（优先）
- LLM 深度分析（兜底）
- 自动级联策略
- 成本优化（减少 60-70% LLM 调用）

算法：规则识别 → (置信度不足时) → LLM 识别
"""

import logging
from typing import Dict, Any, Optional

from ame.foundation.llm import LLMCallerBase
from ame.foundation.inference import (
    CascadeInferenceEngine,
    InferenceLevelBase,
    InferenceResult,
    InferenceLevel
)
from .base import EmotionDetectorBase, EmotionResult
from .rule_emotion import RuleEmotionDetector
from .llm_emotion import LLMEmotionDetector

logger = logging.getLogger(__name__)


class HybridEmotionDetector(EmotionDetectorBase):
    """
    混合情绪识别器
    
    使用级联推理引擎整合规则和 LLM 识别器
    
    工作流程：
    1. 规则识别（快速，置信度中等）
    2. 如果置信度 < 0.7，级联到 LLM 识别
    3. 返回最终结果
    """
    
    def __init__(
        self,
        llm_caller: LLMCallerBase,
        confidence_threshold: float = 0.7,
        enable_cache: bool = True
    ):
        """
        初始化混合情绪识别器
        
        Args:
            llm_caller: LLM 调用器
            confidence_threshold: 置信度阈值（低于此值级联到 LLM）
            enable_cache: 是否启用缓存
        """
        self.llm = llm_caller
        self.confidence_threshold = confidence_threshold
        
        # 创建规则和 LLM 识别器
        self.rule_detector = RuleEmotionDetector()
        self.llm_detector = LLMEmotionDetector(llm_caller)
        
        # 创建级联推理引擎
        self.engine = CascadeInferenceEngine(
            confidence_threshold=confidence_threshold,
            enable_cache=enable_cache,
            fallback_strategy="cascade"
        )
        
        # 添加推理层级
        self.engine.add_level(RuleEmotionLevel(self.rule_detector))
        self.engine.add_level(LLMEmotionLevel(self.llm_detector))
        
        logger.info(
            f"混合情绪识别器初始化 "
            f"(threshold={confidence_threshold}, cache={enable_cache})"
        )
    
    async def detect(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionResult:
        """
        混合情绪识别
        
        Args:
            text: 输入文本
            context: 上下文信息
        
        Returns:
            result: 情绪识别结果
        """
        if not text:
            return EmotionResult(
                type="neutral",
                intensity=0.5,
                confidence=0.5,
                metadata={"method": "hybrid", "reason": "empty_text"}
            )
        
        try:
            # 执行级联推理
            inference_result = await self.engine.infer(text, context or {})
            
            # 转换为 EmotionResult
            emotion_result = EmotionResult(
                type=inference_result.value["type"],
                intensity=inference_result.value["intensity"],
                confidence=inference_result.confidence,
                metadata={
                    **inference_result.value.get("metadata", {}),
                    "inference_level": inference_result.level.value
                }
            )
            
            logger.debug(
                f"混合情绪识别: {emotion_result.type} "
                f"(level={inference_result.level.value}, "
                f"confidence={emotion_result.confidence:.2f})"
            )
            
            return emotion_result
        
        except Exception as e:
            logger.error(f"混合情绪识别失败: {e}", exc_info=True)
            
            return EmotionResult(
                type="neutral",
                intensity=0.5,
                confidence=0.3,
                metadata={
                    "method": "hybrid",
                    "error": str(e),
                    "fallback": True
                }
            )
    
    def get_detector_name(self) -> str:
        """获取识别器名称"""
        return "HybridEmotionDetector"
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.engine.get_statistics()
    
    def clear_cache(self):
        """清空缓存"""
        self.engine.clear_cache()


# ==================== 推理层级实现 ====================

class RuleEmotionLevel(InferenceLevelBase):
    """规则情绪识别层级"""
    
    def __init__(self, detector: RuleEmotionDetector):
        self.detector = detector
    
    async def infer(self, input_data: str, context: Dict[str, Any]) -> InferenceResult:
        """执行规则情绪识别"""
        emotion_result = await self.detector.detect(input_data, context)
        
        # 转换为 InferenceResult
        return InferenceResult(
            value={
                "type": emotion_result.type,
                "intensity": emotion_result.intensity,
                "metadata": emotion_result.metadata
            },
            confidence=emotion_result.confidence,
            level=InferenceLevel.RULE,
            metadata={"detector": "RuleEmotionDetector"}
        )
    
    def get_level(self) -> InferenceLevel:
        return InferenceLevel.RULE
    
    def get_name(self) -> str:
        return "Rule Emotion"


class LLMEmotionLevel(InferenceLevelBase):
    """LLM 情绪识别层级"""
    
    def __init__(self, detector: LLMEmotionDetector):
        self.detector = detector
    
    async def infer(self, input_data: str, context: Dict[str, Any]) -> InferenceResult:
        """执行 LLM 情绪识别"""
        emotion_result = await self.detector.detect(input_data, context)
        
        # 转换为 InferenceResult
        return InferenceResult(
            value={
                "type": emotion_result.type,
                "intensity": emotion_result.intensity,
                "metadata": emotion_result.metadata
            },
            confidence=emotion_result.confidence,
            level=InferenceLevel.LLM,
            metadata={"detector": "LLMEmotionDetector"}
        )
    
    def get_level(self) -> InferenceLevel:
        return InferenceLevel.LLM
    
    def get_name(self) -> str:
        return "LLM Emotion"
