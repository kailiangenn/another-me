"""
缓存策略 - Cache Strategy

使用TTL缓存机制，避免重复调用LLM。
"""

from cachetools import TTLCache
import hashlib
import json
from typing import Optional, Dict, Any, List

from ..caller import LLMResponse


class CacheStrategy:
    """缓存策略
    
    使用带过期时间的LRU缓存，防止无限制增长。
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
        
        if enabled:
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
