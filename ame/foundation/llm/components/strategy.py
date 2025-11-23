"""
统一策略模块 - Strategy Module

集中管理所有LLM策略：缓存、压缩、重试。
根据设计文档，将原来分散在strategy/目录下的策略统一到此文件中。
"""

import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Callable, Optional, Type, Tuple, Dict, Any, List
from functools import wraps

try:
    from cachetools import TTLCache
    CACHETOOLS_AVAILABLE = True
except ImportError:
    CACHETOOLS_AVAILABLE = False
    TTLCache = None

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from ..utils import LLMResponse, CompressContext, CompressResult


# ============================================================================
# 缓存策略 - Cache Strategy
# ============================================================================

class CacheStrategy:
    """缓存策略
    
    使用带过期时间的LRU缓存，防止无限制增长。
    
    功能：
    - 基于消息内容和参数生成缓存键
    - TTL机制自动过期
    - LRU淘汰策略
    - 缓存统计信息
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        ttl: int = 3600,
        enabled: bool = True
    ):
        """初始化缓存策略
        
        Args:
            max_size: 最大缓存数量
            ttl: 缓存过期时间（秒）
            enabled: 是否启用缓存
        """
        self.enabled = enabled
        self.max_size = max_size
        self.ttl = ttl
        
        if not CACHETOOLS_AVAILABLE:
            logger.warning("cachetools未安装，缓存功能将被禁用。请运行: pip install cachetools")
            self.enabled = False
            self.cache = None
        elif enabled:
            self.cache = TTLCache(maxsize=max_size, ttl=ttl)
        else:
            self.cache = None
    
    def get_cache_key(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """生成缓存键
        
        基于消息内容、模型参数生成唯一哈希键。
        
        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            **kwargs: 其他参数
            
        Returns:
            str: MD5哈希键
        """
        # 构建缓存数据
        cache_data = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
        }
        
        # 添加其他关键参数
        for key in ["max_tokens", "top_p", "frequency_penalty", "presence_penalty"]:
            if key in kwargs:
                cache_data[key] = kwargs[key]
        
        # 序列化并生成哈希
        cache_str = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(cache_str.encode('utf-8')).hexdigest()
    
    def get(self, cache_key: str) -> Optional[LLMResponse]:
        """获取缓存
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Optional[LLMResponse]: 缓存的响应，不存在则返回None
        """
        if not self.enabled or self.cache is None:
            return None
        
        return self.cache.get(cache_key)
    
    def set(self, cache_key: str, response: LLMResponse):
        """设置缓存
        
        Args:
            cache_key: 缓存键
            response: LLM响应
        """
        if self.enabled and self.cache is not None:
            self.cache[cache_key] = response
    
    def clear(self):
        """清空所有缓存"""
        if self.cache is not None:
            self.cache.clear()
    
    def remove(self, cache_key: str) -> bool:
        """删除指定缓存
        
        Args:
            cache_key: 缓存键
            
        Returns:
            bool: 是否删除成功
        """
        if not self.enabled or self.cache is None:
            return False
        
        try:
            del self.cache[cache_key]
            return True
        except KeyError:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            dict: 统计信息
        """
        if not self.enabled:
            return {
                "enabled": False,
                "size": 0,
                "max_size": 0,
                "ttl": 0,
                "hit_rate": 0.0
            }
        
        return {
            "enabled": True,
            "size": len(self.cache) if self.cache else 0,
            "max_size": self.max_size,
            "ttl": self.ttl,
            "current_size": len(self.cache) if self.cache else 0
        }
    
    def __len__(self) -> int:
        """获取当前缓存数量"""
        if self.cache is None:
            return 0
        return len(self.cache)
    
    def __contains__(self, cache_key: str) -> bool:
        """检查缓存键是否存在"""
        if self.cache is None:
            return False
        return cache_key in self.cache


# ============================================================================
# 压缩策略 - Compress Strategy
# ============================================================================

class CompressStrategy:
    """统一的压缩策略（原子能力）
    
    最小化的压缩能力，不内置任何模式，所有行为由参数控制。
    外部可以通过组合参数实现不同的压缩策略。
    
    基础压缩逻辑:
    1. 根据threshold判断是否需要压缩
    2. 保留系统消息（如果keep_system=True）
    3. 保留标记为重要的消息（如果keep_important=True）
    4. 保留最近N条消息（keep_recent）
    5. 移除其余消息
    
    参数:
        threshold: 压缩阈值 (current_tokens / max_tokens >= threshold 时触发)
        keep_recent: 保留最近N条消息
        keep_system: 是否保留系统消息
        keep_important: 是否保留标记为重要的消息
    
    使用示例:
        # 保守策略（对话场景）
        strategy = CompressStrategy(
            threshold=0.95,
            keep_recent=10,
            keep_system=True,
            keep_important=True
        )
        
        # 激进策略（文档分析）
        strategy = CompressStrategy(
            threshold=0.8,
            keep_recent=5,
            keep_system=True,
            keep_important=False
        )
    """
    
    def __init__(
        self,
        threshold: float = 0.9,
        keep_recent: int = 10,
        keep_system: bool = True,
        keep_important: bool = True
    ):
        """初始化压缩策略
        
        Args:
            threshold: 压缩阈值 (0.0-1.0)
            keep_recent: 保留最近N条消息
            keep_system: 是否保留系统消息
            keep_important: 是否保留标记为重要的消息
        """
        self.threshold = threshold
        self.keep_recent = keep_recent
        self.keep_system = keep_system
        self.keep_important = keep_important
    
    def should_compress(self, context: CompressContext) -> bool:
        """判断是否需要压缩
        
        Args:
            context: 压缩上下文
            
        Returns:
            bool: 是否需要压缩
        """
        return context.current_tokens >= context.max_tokens * self.threshold
    
    def compress(self, context: CompressContext) -> CompressResult:
        """执行压缩
        
        压缩逻辑:
        1. 保留系统消息（如果启用）
        2. 保留重要消息（如果启用）
        3. 保留最近N条消息
        4. 移除其余消息
        
        Args:
            context: 压缩上下文
            
        Returns:
            CompressResult: 压缩结果
        """
        tokens_before = context.current_tokens
        kept_messages = []
        removed_messages = []
        
        # 1. 分离系统消息和其他消息
        system_messages = []
        other_messages = []
        
        for msg in context.messages:
            if self.keep_system and msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # 2. 标记需要保留的消息索引
        keep_indices = set()
        
        # 2.1 标记重要消息
        if self.keep_important:
            for i, msg in enumerate(other_messages):
                metadata = msg.get("metadata", {})
                if metadata.get("important", False):
                    keep_indices.add(i)
        
        # 2.2 标记最近N条消息
        if self.keep_recent > 0:
            start_idx = max(0, len(other_messages) - self.keep_recent)
            for i in range(start_idx, len(other_messages)):
                keep_indices.add(i)
        
        # 3. 分离保留和移除的消息
        for i, msg in enumerate(other_messages):
            if i in keep_indices:
                kept_messages.append(msg)
            else:
                removed_messages.append(msg)
        
        # 4. 组合最终消息列表（系统消息在前）
        final_messages = system_messages + kept_messages
        
        # 5. 计算压缩后的token数
        tokens_after = self._calculate_total_tokens(
            final_messages,
            context.token_estimator
        )
        
        compression_ratio = (
            (tokens_before - tokens_after) / tokens_before 
            if tokens_before > 0 else 0
        )
        
        # 6. 记录压缩信息
        logger.info(
            f"Compress: {len(context.messages)} -> {len(final_messages)} messages, "
            f"tokens: {tokens_before} -> {tokens_after} ({compression_ratio:.1%}), "
            f"removed: {len(removed_messages)}"
        )
        
        # 7. 如果压缩比较大，警告用户
        if compression_ratio > 0.3:  # 压缩超过30%
            logger.warning(
                f"上下文压缩警告: 移除了{len(removed_messages)}条消息 "
                f"(压缩比{compression_ratio:.1%})，"
                f"保留了最近{self.keep_recent}条消息"
            )
        
        return CompressResult(
            kept_messages=final_messages,
            removed_messages=removed_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio
        )
    
    def _calculate_total_tokens(
        self,
        messages: List[Dict[str, str]],
        token_estimator: Callable[[str], int]
    ) -> int:
        """计算消息列表的总token数"""
        total = 0
        for msg in messages:
            total += token_estimator(msg.get("content", "")) + 4
        return total


# ============================================================================
# 重试策略 - Retry Strategy
# ============================================================================

class RetryStrategy:
    """重试策略
    
    提供带指数退避的重试机制，适用于处理临时性错误。
    
    功能：
    - 指数退避算法
    - 可配置重试次数和退避参数
    - 可指定需要重试的异常类型
    - 支持装饰器模式
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
                    error_msg = f"遇到不可重试的错误: {type(e).__name__}: {e}"
                    logger.warning(error_msg)
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
                    error_msg = f"达到最大重试次数 {self.max_retries}，最后错误: {type(e).__name__}: {e}"
                    logger.error(error_msg)
        
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
    
    @classmethod
    def from_preset(cls, preset: str) -> "RetryStrategy":
        """从预设配置创建重试策略
        
        Args:
            preset: 预设名称（network/rate_limit/default）
            
        Returns:
            RetryStrategy实例
        """
        if preset == "network":
            return NetworkRetryStrategy()
        elif preset == "rate_limit":
            return RateLimitRetryStrategy()
        else:
            return cls()


# ============================================================================
# 预定义重试策略
# ============================================================================

class NetworkRetryStrategy(RetryStrategy):
    """网络错误重试策略
    
    针对常见的网络错误（超时、连接错误等）进行重试。
    """
    
    def __init__(self, max_retries: int = 3):
        try:
            import aiohttp
            retry_on = (
                aiohttp.ClientError,
                asyncio.TimeoutError,
                ConnectionError,
            )
        except ImportError:
            # aiohttp未安装，只重试通用网络错误
            retry_on = (
                asyncio.TimeoutError,
                ConnectionError,
            )
        
        super().__init__(
            max_retries=max_retries,
            backoff_factor=1.0,
            max_backoff=30.0,
            retry_on=retry_on
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
