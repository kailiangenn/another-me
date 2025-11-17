"""
文档管道 - Document Pipe

组合原子能力，适用于文档分析场景：
- StreamCaller: 流式调用
- DocumentCompressStrategy: 激进压缩
- RetryStrategy: 失败重试
- ConversationHistory: 分析历史管理
"""

import logging
from typing import Optional, Dict, Any
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
    DocumentCompressStrategy,
    RetryStrategy,
)

logger = logging.getLogger(__name__)


class DocumentPipe(PipelineBase):
    """文档管道
    
    适用于文档分析场景，提供：
    1. 激进压缩：仅保留最新分析上下文
    2. 自动重试：处理临时错误
    3. 流式输出：实时响应
    
    注意：文档模式不使用缓存（每次分析都是新内容）
    """
    
    def __init__(
        self,
        caller: LLMCallerBase,
        compress_threshold: float = 0.8,
        max_retries: int = 3
    ):
        """初始化文档管道
        
        Args:
            caller: LLM调用器
            compress_threshold: 压缩阈值（更激进）
            max_retries: 最大重试次数
        """
        self.compress_threshold = compress_threshold
        self.max_retries = max_retries
        
        # 初始化分析历史
        self.history = ConversationHistory(
            metadata={"pipeline": "document"}
        )
        
        super().__init__(caller)
    
    def _setup_strategies(self):
        """设置策略组件"""
        # 1. 流式调用器
        self.stream_caller = StreamCaller(self.caller)
        
        # 2. 压缩策略（激进）
        self.compressor = DocumentCompressStrategy(
            threshold=self.compress_threshold
        )
        
        # 3. 重试策略
        self.retry = RetryStrategy(
            max_retries=self.max_retries,
            backoff_factor=0.5,
            max_backoff=10.0
        )
    
    async def process(self, context: PipelineContext) -> PipelineResult:
        """处理请求
        
        流程：
        1. 检查并执行压缩（激进）
        2. 调用LLM（带重试）
        3. 记录分析历史
        4. 返回结果
        
        注意：不使用缓存
        """
        logger.debug(f"DocumentPipe处理请求: {self._get_context_summary(context)}")
        
        # 准备API消息
        api_messages = context.to_api_messages()
        
        # 1. 检查并执行压缩
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
        
        # 2. 调用LLM（带重试）
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
                
                # 3. 记录消息到历史
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
                    metadata={"mode": "stream", "pipeline": "document"}
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
                
                # 3. 记录历史
                for msg in context.messages:
                    if msg not in self.history.messages:
                        self.history.add_message(
                            role=msg.get("role"),
                            content=msg.get("content"),
                            **msg.get("metadata", {})
                        )
                
                # 记录 assistant 分析结果
                self.history.add_message(
                    role="assistant",
                    content=response.content,
                    timestamp=datetime.now().isoformat()
                )
                
                return PipelineResult(
                    response=response,
                    compressed=compressed,
                    compression_info=compression_info,
                    metadata={"mode": "complete", "pipeline": "document"}
                )
        
        except Exception as e:
            logger.error(f"DocumentPipe处理失败: {type(e).__name__}: {e}")
            raise
    
    def clear_history(self):
        """清空分析历史（开启新分析）
        
        清空历史消息，准备分析新文档。
        """
        self.history.clear()
        logger.info("分析历史已清空，可以开始新分析")
    
    def export_session(self) -> Dict[str, Any]:
        """导出分析数据（用于存储和分析）
        
        Returns:
            包含完整分析信息的字典
        """
        return {
            "type": "document",
            "history": self.history.export(),
            "exported_at": datetime.now().isoformat()
        }
    
    @classmethod
    def from_export(cls, caller: LLMCallerBase, export_data: Dict[str, Any]) -> "DocumentPipe":
        """从导出数据恢复分析
        
        使用场景：
        1. 从数据库恢复历史分析
        2. 继续之前的文档分析
        
        Args:
            caller: LLM调用器
            export_data: 导出的分析数据
            
        Returns:
            恢复后的 DocumentPipe 实例
        """
        pipe = cls(caller=caller)
        
        # 恢复历史数据
        history_data = export_data.get("history", {})
        pipe.history.load(history_data)
        
        logger.info(f"已从导出数据恢复分析，共 {len(pipe.history)} 条消息")
        
        return pipe
