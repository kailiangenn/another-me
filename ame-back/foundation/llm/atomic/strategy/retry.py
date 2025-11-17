"""
重试策略 - Retry Strategy

提供带指数退避的智能重试机制。
"""

import asyncio
import logging
from typing import Callable, Optional, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RetryStrategy:
    """重试策略
    
    提供带指数退避的重试机制，适用于处理临时性错误。
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        max_backoff: float = 10.0,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None
    ):
        """初始化重试策略
        
        Args:
            max_retries: 最大重试次数
            backoff_factor: 退避因子（秒）
            max_backoff: 最大退避时间（秒）
            retry_on: 需要重试的异常类型元组，None表示所有异常
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.max_backoff = max_backoff
        self.retry_on = retry_on
    
    def _should_retry(self, error: Exception) -> bool:
        """判断是否应该重试
        
        Args:
            error: 捕获的异常
            
        Returns:
            bool: 是否应该重试
        """
        if self.retry_on is None:
            return True
        return isinstance(error, self.retry_on)
    
    def _calculate_backoff(self, attempt: int) -> float:
        """计算退避时间
        
        使用指数退避：wait_time = min(backoff_factor * (2 ^ attempt), max_backoff)
        
        Args:
            attempt: 当前尝试次数（0-based）
            
        Returns:
            float: 退避时间（秒）
        """
        wait_time = self.backoff_factor * (2 ** attempt)
        return min(wait_time, self.max_backoff)
    
    async def retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs
    ):
        """执行带重试的函数调用
        
        Args:
            func: 要执行的异步函数
            *args: 函数位置参数
            **kwargs: 函数关键字参数
            
        Returns:
            函数的返回值
            
        Raises:
            最后一次尝试的异常
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                
                # 判断是否应该重试
                if not self._should_retry(e):
                    logger.warning(f"遇到不可重试的错误: {type(e).__name__}: {e}")
                    raise
                
                # 如果还有重试机会
                if attempt < self.max_retries - 1:
                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(
                        f"尝试 {attempt + 1}/{self.max_retries} 失败: {type(e).__name__}: {e}. "
                        f"将在 {wait_time:.2f}秒后重试..."
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(
                        f"达到最大重试次数 {self.max_retries}，最后错误: {type(e).__name__}: {e}"
                    )
        
        # 所有重试都失败了，抛出最后一个错误
        raise last_error
    
    def __call__(self, func: Callable) -> Callable:
        """装饰器模式
        
        使用方式:
            @RetryStrategy(max_retries=3)
            async def my_function():
                ...
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self.retry_with_backoff(func, *args, **kwargs)
        
        return wrapper


# 预定义的常用重试策略
class NetworkRetryStrategy(RetryStrategy):
    """网络错误重试策略
    
    针对常见的网络错误（超时、连接错误等）进行重试。
    """
    
    def __init__(self, max_retries: int = 3):
        import aiohttp
        
        super().__init__(
            max_retries=max_retries,
            backoff_factor=1.0,
            max_backoff=30.0,
            retry_on=(
                aiohttp.ClientError,
                asyncio.TimeoutError,
                ConnectionError,
            )
        )


class RateLimitRetryStrategy(RetryStrategy):
    """速率限制重试策略
    
    针对API速率限制错误进行重试，使用更长的退避时间。
    """
    
    def __init__(self, max_retries: int = 5):
        super().__init__(
            max_retries=max_retries,
            backoff_factor=2.0,
            max_backoff=60.0,
        )
