"""
会话管道 - Session Pipe

组合原子能力，适用于对话场景：
- StreamCaller: 流式调用
- CacheStrategy: 缓存响应
- SessionCompressStrategy: 保守压缩
- RetryStrategy: 失败重试
- ConversationHistory: 会话历史管理
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import PipelineBase
from ..core import (
    PipelineContext,
    PipelineResult,
    ConversationHistory,
    CompressContext,
    CallMode,
)
from ..atomic import (
    LLMCallerBase,
    StreamCaller,
    CacheStrategy,
    SessionCompressStrategy,
    RetryStrategy,
)

logger = logging.getLogger(__name__)


class SessionPipe(PipelineBase):
    """会话管道
    
    适用于多轮对话场景，提供：
    1. 智能缓存：避免重复调用
    2. 保守压缩：保留重要对话历史
    3. 自动重试：处理临时错误
    4. 流式输出：实时响应
    """
    
    def __init__(
        self,
        caller: LLMCallerBase,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        compress_threshold: float = 0.95,
        keep_recent: int = 5,
        max_retries: int = 3
    ):
        """初始化会话管道
        
        Args:
            caller: LLM调用器
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存过期时间（秒）
            compress_threshold: 压缩阈值
            keep_recent: 保留最近的对话轮数
            max_retries: 最大重试次数
        """
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.compress_threshold = compress_threshold
        self.keep_recent = keep_recent
        self.max_retries = max_retries
        
        super().__init__(caller)
    
    def _setup_strategies(self):
        """设置策略组件"""
        # 1. 流式调用器
        self.stream_caller = StreamCaller(self.caller)
        
        # 2. 缓存策略
        self.cache = CacheStrategy(
            max_size=1000,
            ttl=self.cache_ttl,
            enabled=self.cache_enabled
        )
        
        # 3. 压缩策略
        self.compressor = SessionCompressStrategy(
            threshold=self.compress_threshold,
            keep_recent=self.keep_recent,
            keep_system=True
        )
        
        # 4. 重试策略
        self.retry = RetryStrategy(
            max_retries=self.max_retries,
            backoff_factor=0.5,
            max_backoff=10.0
        )
    
    async def process(self, context: PipelineContext) -> PipelineResult:
        """处理请求
        
        流程：
        1. 检查缓存
        2. 检查并执行压缩
        3. 调用LLM（带重试）
        4. 更新缓存
        5. 记录历史
        6. 返回结果
        """
        logger.debug(f"SessionPipe处理请求: {self._get_context_summary(context)}")
        
        # 准备API消息
        api_messages = context.to_api_messages()
        
        # 1. 检查缓存（仅完整模式）
        cached = False
        cache_key = None
        if not context.stream and self.cache_enabled:
            cache_key = self.cache.get_cache_key(
                messages=api_messages,
                model=self.caller.model if hasattr(self.caller, 'model') else 'unknown',
                temperature=context.temperature
            )
            
            cached_response = self.cache.get(cache_key)
            if cached_response:
                logger.info(f"缓存命中: {cache_key[:8]}...")
                return PipelineResult(
                    response=cached_response,
                    cached=True,
                    metadata={"cache_key": cache_key}
                )
        
        # 2. 检查并执行压缩
        compressed = False
        compression_info = None
        
        current_tokens = self.caller.estimate_messages_tokens(api_messages)
        
        compress_ctx = CompressContext(
            messages=context.messages,
            max_tokens=context.max_tokens,
            token_estimator=self.caller.estimate_tokens,
            current_tokens=current_tokens
        )
        
        if self.compressor.should_compress(compress_ctx):
            logger.info(f"触发压缩: {current_tokens}/{context.max_tokens} tokens")
            
            result = self.compressor.compress(compress_ctx)
            context.messages = result.kept_messages
            api_messages = context.to_api_messages()
            compressed = True
            
            compression_info = {
                "tokens_before": result.tokens_before,
                "tokens_after": result.tokens_after,
                "compression_ratio": result.compression_ratio,
                "removed_count": len(result.removed_messages)
            }
            
            # 记录压缩事件
            self.history.record_compression(compression_info)
            
            logger.info(f"压缩完成: {result}")
        
        # 3. 调用LLM（带重试）
        try:
            if context.stream:
                # 流式模式
                stream_iterator = await self.retry.retry_with_backoff(
                    self.stream_caller.call,
                    messages=api_messages,
                    mode=CallMode.STREAM,
                    temperature=context.temperature,
                    **context.metadata
                )
                
                # 记录消息到历史（不包含assistant响应，需要手动添加）
                for msg in context.messages:
                    if msg not in self.history.messages:
                        self.history.add_message(
                            role=msg.get("role"),
                            content=msg.get("content"),
                            **msg.get("metadata", {})
                        )
                
                return PipelineResult(
                    stream_iterator=stream_iterator,
                    compressed=compressed,
                    compression_info=compression_info,
                    metadata={"mode": "stream"}
                )
            else:
                # 完整模式
                response = await self.retry.retry_with_backoff(
                    self.stream_caller.call,
                    messages=api_messages,
                    mode=CallMode.COMPLETE,
                    temperature=context.temperature,
                    **context.metadata
                )
                
                # 4. 更新缓存
                if self.cache_enabled and cache_key:
                    self.cache.set(cache_key, response)
                
                # 5. 记录历史
                for msg in context.messages:
                    if msg not in self.history.messages:
                        self.history.add_message(
                            role=msg.get("role"),
                            content=msg.get("content"),
                            **msg.get("metadata", {})
                        )
                
                # 记录 assistant 响应
                self.history.add_message(
                    role="assistant",
                    content=response.content,
                    timestamp=datetime.now().isoformat()
                )
                
                return PipelineResult(
                    response=response,
                    compressed=compressed,
                    cached=False,
                    compression_info=compression_info,
                    metadata={"mode": "complete"}
                )
        
        except Exception as e:
            logger.error(f"SessionPipe处理失败: {type(e).__name__}: {e}")
            raise
    
    def clear_history(self):
        """清空会话历史（开启新对话）
        
        清空历史消息和缓存，准备开始新的对话。
        """
        self.history.clear()
        self.clear_cache()
        logger.info("会话历史已清空，可以开始新对话")
    
    def export_session(self) -> Dict[str, Any]:
        """导出会话数据（用于存储和分析）
        
        Returns:
            包含完整会话信息的字典
        """
        return {
            "type": "session",
            "history": self.history.export(),
            "cache_stats": self.get_cache_stats(),
            "exported_at": datetime.now().isoformat()
        }
    
    @classmethod
    def from_export(cls, caller: LLMCallerBase, export_data: Dict[str, Any]) -> "SessionPipe":
        """从导出数据恢复会话
        
        使用场景：
        1. 从数据库恢复历史对话
        2. 跨会话继续分析
        
        Args:
            caller: LLM调用器
            export_data: 导出的会话数据
            
        Returns:
            恢复后的 SessionPipe 实例
        """
        pipe = cls(caller=caller)
        
        # 恢复历史数据
        history_data = export_data.get("history", {})
        pipe.history.load(history_data)
        
        logger.info(f"已从导出数据恢复会话，共 {len(pipe.history)} 条消息")
        
        return pipe
    
    def clear_cache(self):
        """清空缓存"""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("缓存已清空")
    
    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        return self.cache.get_stats()
