"""
Embedding异常定义
"""


class EmbeddingError(Exception):
    """Embedding基础异常"""
    pass


class EmbeddingAPIError(EmbeddingError):
    """API调用异常"""
    pass


class EmbeddingConfigError(EmbeddingError):
    """配置错误"""
    pass


class EmbeddingDimensionError(EmbeddingError):
    """维度错误"""
    pass
