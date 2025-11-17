"""
压缩策略 - Compress Strategy

提供不同场景下的对话历史压缩策略。
"""

from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Dict, Any
import logging

from ...core import CompressContext, CompressResult

logger = logging.getLogger(__name__)


class CompressStrategy(ABC):
    """压缩策略基类
    
    定义压缩策略的通用接口。
    """
    
    @abstractmethod
    def should_compress(self, context: CompressContext) -> bool:
        """判断是否需要压缩
        
        Args:
            context: 压缩上下文
            
        Returns:
            bool: 是否需要压缩
        """
        pass
    
    @abstractmethod
    def compress(self, context: CompressContext) -> CompressResult:
        """执行压缩
        
        Args:
            context: 压缩上下文
            
        Returns:
            CompressResult: 压缩结果
        """
        pass
    
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


class SessionCompressStrategy(CompressStrategy):
    """会话模式压缩策略
    
    保守压缩策略，适用于对话场景：
    1. 保留系统消息
    2. 保留标记为重要的消息
    3. 保留最近N轮对话
    4. 压缩或移除旧消息
    """
    
    def __init__(
        self,
        threshold: float = 0.95,
        keep_recent: int = 5,
        keep_system: bool = True
    ):
        """初始化
        
        Args:
            threshold: 压缩阈值（当前token/最大token）
            keep_recent: 保留最近的消息对数
            keep_system: 是否保留系统消息
        """
        self.threshold = threshold
        self.keep_recent = keep_recent
        self.keep_system = keep_system
    
    def should_compress(self, context: CompressContext) -> bool:
        """判断是否需要压缩"""
        return context.current_tokens >= context.max_tokens * self.threshold
    
    def compress(self, context: CompressContext) -> CompressResult:
        """执行压缩
        
        压缩策略：
        1. 保留系统消息
        2. 保留重要消息（metadata中标记）
        3. 保留最近N轮对话
        4. 移除旧消息
        """
        tokens_before = context.current_tokens
        kept_messages = []
        removed_messages = []
        
        # 1. 保留系统消息
        system_messages = []
        other_messages = []
        
        for msg in context.messages:
            if self.keep_system and msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # 2. 标记重要消息和最近消息
        important_indices = set()
        
        for i, msg in enumerate(other_messages):
            # 重要消息
            metadata = msg.get("metadata", {})
            if metadata.get("important", False):
                important_indices.add(i)
        
        # 最近N轮对话（user+assistant为一轮）
        if self.keep_recent > 0:
            recent_count = self.keep_recent * 2
            for i in range(max(0, len(other_messages) - recent_count), len(other_messages)):
                important_indices.add(i)
        
        # 3. 分离保留和移除的消息
        for i, msg in enumerate(other_messages):
            if i in important_indices:
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
        
        compression_ratio = (tokens_before - tokens_after) / tokens_before if tokens_before > 0 else 0
        
        return CompressResult(
            kept_messages=final_messages,
            removed_messages=removed_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio
        )


class DocumentCompressStrategy(CompressStrategy):
    """文档模式压缩策略
    
    激进压缩策略，适用于文档分析场景：
    1. 保留系统消息
    2. 保留最新的用户输入
    3. 保留最新的AI分析结果
    4. 移除所有旧分析结果
    """
    
    def __init__(self, threshold: float = 0.8):
        """初始化
        
        Args:
            threshold: 压缩阈值（更激进）
        """
        self.threshold = threshold
    
    def should_compress(self, context: CompressContext) -> bool:
        """判断是否需要压缩"""
        return context.current_tokens >= context.max_tokens * self.threshold
    
    def compress(self, context: CompressContext) -> CompressResult:
        """执行压缩
        
        压缩策略：
        1. 保留系统消息
        2. 保留最新用户输入
        3. 保留最新AI分析
        4. 移除所有旧内容
        """
        tokens_before = context.current_tokens
        kept_messages = []
        removed_messages = []
        
        # 1. 分离系统消息和其他消息
        system_messages = []
        other_messages = []
        
        for msg in context.messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # 2. 保留最新的用户输入和AI响应（最多2条）
        if len(other_messages) > 0:
            # 从后往前查找最新的user消息
            for i in range(len(other_messages) - 1, -1, -1):
                if other_messages[i].get("role") == "user":
                    kept_messages.append(other_messages[i])
                    # 查找对应的assistant响应
                    if i + 1 < len(other_messages) and other_messages[i + 1].get("role") == "assistant":
                        kept_messages.append(other_messages[i + 1])
                    break
            
            # 其他消息都移除
            for msg in other_messages:
                if msg not in kept_messages:
                    removed_messages.append(msg)
        
        # 3. 组合最终消息列表
        final_messages = system_messages + kept_messages
        
        # 4. 计算压缩后的token数
        tokens_after = self._calculate_total_tokens(
            final_messages,
            context.token_estimator
        )
        
        compression_ratio = (tokens_before - tokens_after) / tokens_before if tokens_before > 0 else 0
        
        return CompressResult(
            kept_messages=final_messages,
            removed_messages=removed_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio
        )


class ChunkingCompressStrategy(CompressStrategy):
    """分块压缩策略
    
    用于处理单条消息超长的情况，将超长消息分块。
    """
    
    def __init__(self, chunk_size: int = 2000):
        """初始化
        
        Args:
            chunk_size: 每块的目标字符数
        """
        self.chunk_size = chunk_size
    
    def should_compress(self, context: CompressContext) -> bool:
        """判断是否需要分块
        
        检查是否有单条消息超过最大token限制的70%
        """
        threshold = context.max_tokens * 0.7
        
        for msg in context.messages:
            msg_tokens = context.token_estimator(msg.get("content", ""))
            if msg_tokens > threshold:
                return True
        
        return False
    
    def compress(self, context: CompressContext) -> CompressResult:
        """执行分块
        
        将超长消息分成多个较小的消息块。
        """
        tokens_before = context.current_tokens
        kept_messages = []
        removed_messages = []
        
        threshold = context.max_tokens * 0.7
        
        for msg in context.messages:
            msg_tokens = context.token_estimator(msg.get("content", ""))
            
            if msg_tokens > threshold:
                # 需要分块
                removed_messages.append(msg)
                
                # 简单分块（按字符）
                content = msg.get("content", "")
                chunks = []
                
                for i in range(0, len(content), self.chunk_size):
                    chunk = content[i:i + self.chunk_size]
                    chunks.append(chunk)
                
                # 创建分块消息
                msg_metadata = msg.get("metadata", {})
                for idx, chunk in enumerate(chunks):
                    chunk_msg = {
                        "role": msg.get("role", "user"),
                        "content": chunk,
                        "metadata": {
                            **msg_metadata,
                            "chunked": True,
                            "chunk_index": idx,
                            "total_chunks": len(chunks)
                        }
                    }
                    kept_messages.append(chunk_msg)
            else:
                # 不需要分块
                kept_messages.append(msg)
        
        # 计算压缩后的token数
        tokens_after = self._calculate_total_tokens(
            kept_messages,
            context.token_estimator
        )
        
        compression_ratio = (tokens_before - tokens_after) / tokens_before if tokens_before > 0 else 0
        
        return CompressResult(
            kept_messages=kept_messages,
            removed_messages=removed_messages,
            tokens_before=tokens_before,
            tokens_after=tokens_after,
            compression_ratio=compression_ratio
        )