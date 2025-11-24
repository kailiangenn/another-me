"""
NLP异常定义
"""


class NLPError(Exception):
    """NLP基础异常"""
    pass


class IntentRecognitionError(NLPError):
    """意图识别异常"""
    pass


class EntityExtractionError(NLPError):
    """实体提取异常"""
    pass


class EmotionAnalysisError(NLPError):
    """情感分析异常"""
    pass


class SummarizationError(NLPError):
    """摘要生成异常"""
    pass


class ModelNotLoadedError(NLPError):
    """模型未加载异常"""
    pass


class DependencyMissingError(NLPError):
    """依赖缺失异常"""
    pass
