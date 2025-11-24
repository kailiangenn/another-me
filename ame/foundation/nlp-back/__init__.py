"""
NLP - 自然语言处理层

提供意图识别、实体提取、情感分析、摘要生成等NLP能力。
"""

from .core import (
    # Enums
    IntentType,
    EntityType,
    EmotionType,
    # Models
    IntentResult,
    Entity,
    EmotionResult,
    Summary,
    NLPAnalysisResult,
    # Exceptions
    NLPError,
    IntentRecognitionError,
    EntityExtractionError,
    EmotionAnalysisError,
    SummarizationError,
    ModelNotLoadedError,
    DependencyMissingError,
)

from .atomic import (
    IntentRecognizer,
    EntityExtractor,
    EmotionAnalyzer,
    Summarizer,
)

__all__ = [
    # Core - Enums
    "IntentType",
    "EntityType",
    "EmotionType",
    # Core - Models
    "IntentResult",
    "Entity",
    "EmotionResult",
    "Summary",
    "NLPAnalysisResult",
    # Core - Exceptions
    "NLPError",
    "IntentRecognitionError",
    "EntityExtractionError",
    "EmotionAnalysisError",
    "SummarizationError",
    "ModelNotLoadedError",
    "DependencyMissingError",
    # Atomic
    "IntentRecognizer",
    "EntityExtractor",
    "EmotionAnalyzer",
    "Summarizer",
]
