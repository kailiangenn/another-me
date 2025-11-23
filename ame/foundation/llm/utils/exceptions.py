"""
LLM 模块自定义异常

提供统一的异常处理机制。
"""


class LLMError(Exception):
    """LLM 模块基础异常
    
    所有 LLM 相关异常的基类。
    """
    pass


class CallerNotConfiguredError(LLMError):
    """调用器未配置异常
    
    当 LLM 调用器缺少必要配置（如 API Key）时抛出。
    """
    pass


class TokenLimitExceededError(LLMError):
    """Token 超限异常
    
    当消息长度超过模型的最大 token 限制时抛出。
    """
    pass


class CompressionError(LLMError):
    """压缩失败异常
    
    当上下文压缩过程发生错误时抛出。
    """
    pass


class CacheError(LLMError):
    """缓存错误异常
    
    当缓存操作失败时抛出。
    """
    pass
