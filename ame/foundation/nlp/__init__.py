"""
NLP - NLP 基础能力

提供自然语言处理的基础能力

核心组件：
- NER: 命名实体识别（Simple, LLM, Hybrid）
- Emotion: 情绪识别（Rule, LLM, Hybrid）
- TextProcessor: 文本处理（分词、停用词过滤等）
- KeywordExtractor: 关键词提取
"""

# Emotion Detection
from .emotion import (
    EmotionDetectorBase,
    RuleEmotionDetector,
    LLMEmotionDetector,
    HybridEmotionDetector,
)

# Named Entity Recognition
from .ner import (
    NERBase,
    SimpleNER,
    LLMNER,
    HybridNER,
    Entity,  # 导出Entity类型
)

__all__ = [
    # Emotion
    "EmotionDetectorBase",
    "RuleEmotionDetector",
    "LLMEmotionDetector",
    "HybridEmotionDetector",
    
    # NER
    "NERBase",
    "SimpleNER",
    "LLMNER",
    "HybridNER",
    "Entity",
]
