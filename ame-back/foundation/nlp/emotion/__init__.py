"""
Emotion - 情绪识别

提供多层级情绪识别能力

核心组件：
- EmotionDetectorBase: 情绪识别抽象基类
- EmotionResult: 情绪识别结果
- RuleEmotionDetector: 规则情绪识别（词典匹配）
- LLMEmotionDetector: LLM 情绪识别
- HybridEmotionDetector: 混合情绪识别（规则 → LLM 级联）
"""

from .base import EmotionDetectorBase, EmotionResult, EmotionType
from .rule_emotion import RuleEmotionDetector
from .llm_emotion import LLMEmotionDetector
from .hybrid_emotion import HybridEmotionDetector

__all__ = [
    "EmotionDetectorBase",
    "EmotionResult",
    "EmotionType",
    "RuleEmotionDetector",
    "LLMEmotionDetector",
    "HybridEmotionDetector",
]
