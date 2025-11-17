"""
LLM调用器 - 原子能力层

提供统一的LLM调用抽象和封装。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, AsyncIterator, Optional, Callable

from ..core import CallMode, LLMResponse


class LLMCallerBase(ABC):
    """LLM调用器抽象基类
    
    定义所有LLM调用器必须实现的接口。
    """
    
    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """完整生成（等待全部输出）
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数（temperature, max_tokens等）
            
        Returns:
            LLMResponse: 完整的响应结果
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """流式生成
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Yields:
            str: 流式输出的文本片段
        """
        pass
    
    @abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数
        
        Args:
            text: 待估算的文本
            
        Returns:
            int: 估算的token数
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """检查调用器是否已正确配置
        
        Returns:
            bool: 是否已配置
        """
        pass
    
    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """估算消息列表的总token数
        
        Args:
            messages: 消息列表
            
        Returns:
            int: 估算的总token数
        """
        total = 0
        for msg in messages:
            # 每条消息额外计算角色token
            total += self.estimate_tokens(msg.get("role", ""))
            total += self.estimate_tokens(msg.get("content", ""))
            total += 4  # 消息格式化开销
        total += 2  # 对话开始/结束标记
        return total


class StreamCaller:
    """流式调用封装器
    
    提供统一的调用入口，支持多种调用模式。
    """
    
    def __init__(self, caller: LLMCallerBase):
        """初始化
        
        Args:
            caller: LLM调用器实例
        """
        if not isinstance(caller, LLMCallerBase):
            raise TypeError(f"caller必须是LLMCallerBase的子类实例")
        self.caller = caller
    
    async def call(
        self,
        messages: List[Dict[str, str]],
        mode: CallMode = CallMode.COMPLETE,
        **kwargs
    ):
        """统一调用入口
        
        Args:
            messages: 消息列表
            mode: 调用模式（STREAM/COMPLETE/BATCH）
            **kwargs: 额外参数
            
        Returns:
            根据mode返回不同类型：
            - STREAM: AsyncIterator[str]
            - COMPLETE: LLMResponse
            - BATCH: 暂不支持
            
        Raises:
            ValueError: 不支持的调用模式
        """
        if mode == CallMode.STREAM:
            return self.caller.generate_stream(messages, **kwargs)
        elif mode == CallMode.COMPLETE:
            return await self.caller.generate(messages, **kwargs)
        elif mode == CallMode.BATCH:
            raise NotImplementedError("批量模式暂未实现")
        else:
            raise ValueError(f"不支持的调用模式: {mode}")
    
    async def stream_with_callback(
        self,
        messages: List[Dict[str, str]],
        on_chunk: Callable[[str], None],
        **kwargs
    ) -> str:
        """流式调用 + 回调
        
        在每个流式片段到达时调用回调函数。
        
        Args:
            messages: 消息列表
            on_chunk: 回调函数，接收每个文本片段
            **kwargs: 额外参数
            
        Returns:
            str: 完整的响应文本
        """
        full_response = ""
        async for chunk in self.caller.generate_stream(messages, **kwargs):
            full_response += chunk
            if on_chunk:
                # 回调可能是同步或异步的
                result = on_chunk(chunk)
                if hasattr(result, '__await__'):
                    await result
        return full_response
    
    async def batch_call(
        self,
        batch_messages: List[List[Dict[str, str]]],
        **kwargs
    ) -> List[LLMResponse]:
        """批量调用（并发执行）
        
        Args:
            batch_messages: 批量消息列表
            **kwargs: 额外参数
            
        Returns:
            List[LLMResponse]: 响应列表
        """
        import asyncio
        
        tasks = [
            self.caller.generate(messages, **kwargs)
            for messages in batch_messages
        ]
        
        return await asyncio.gather(*tasks)
