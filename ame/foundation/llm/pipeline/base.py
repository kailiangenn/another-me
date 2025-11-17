"""
管道基类 - Pipeline Base

定义管道的通用接口和数据结构。
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..core import PipelineContext, PipelineResult
from ..atomic import LLMCallerBase


class PipelineBase(ABC):
    """管道基类
    
    定义所有管道必须实现的接口。
    """
    
    def __init__(self, caller: LLMCallerBase):
        """初始化管道
        
        Args:
            caller: LLM调用器
        """
        if not isinstance(caller, LLMCallerBase):
            raise TypeError(f"caller必须是LLMCallerBase的子类实例")
        
        self.caller = caller
        self._setup_strategies()
    
    @abstractmethod
    def _setup_strategies(self):
        """设置策略组件
        
        子类需要实现此方法来配置所需的策略。
        """
        pass
    
    @abstractmethod
    async def process(
        self,
        context: PipelineContext
    ) -> PipelineResult:
        """处理请求
        
        Args:
            context: 管道上下文
            
        Returns:
            PipelineResult: 处理结果
        """
        pass
    
    def _get_context_summary(self, context: PipelineContext) -> str:
        """获取上下文摘要（用于日志）"""
        msg_count = len(context.messages)
        stream_mode = "stream" if context.stream else "complete"
        return f"{msg_count} messages, {stream_mode} mode"
