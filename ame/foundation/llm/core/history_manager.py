"""
对话历史管理器

提供对话历史管理、压缩和Token控制功能。
"""

from typing import List, Dict, Optional, Callable, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CompressionStrategy(Enum):
    """压缩策略"""
    TRUNCATE = "truncate"        # 截断(保留最近N条)
    SUMMARIZE = "summarize"      # LLM摘要压缩
    SLIDING_WINDOW = "sliding"   # 滑动窗口
    IMPORTANCE = "importance"    # 重要性保留


class HistoryManager:
    """
    对话历史管理器
    
    Features:
    - 基于Token数的历史截断
    - LLM摘要压缩
    - 滑动窗口策略
    - 重要消息保留
    """
    
    def __init__(
        self,
        max_tokens: int = 4000,
        token_estimator: Optional[Callable[[str], int]] = None
    ):
        """
        初始化历史管理器
        
        Args:
            max_tokens: 最大允许的token数
            token_estimator: Token估算函数,接收文本返回token数
        """
        self.max_tokens = max_tokens
        self.token_estimator = token_estimator or self._default_token_estimator
        logger.debug(f"HistoryManager initialized with max_tokens={max_tokens}")
    
    def manage(
        self,
        messages: List[Dict[str, str]],
        strategy: CompressionStrategy = CompressionStrategy.TRUNCATE,
        keep_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        管理对话历史
        
        根据策略压缩历史到max_tokens以内。
        
        Args:
            messages: 消息列表
            strategy: 压缩策略
            keep_system: 是否保留系统消息
        
        Returns:
            处理后的消息列表
        """
        if not messages:
            return []
        
        # 估算当前token数
        current_tokens = self.estimate_tokens(messages)
        
        logger.debug(
            f"Current tokens: {current_tokens}/{self.max_tokens}, "
            f"strategy={strategy.value}"
        )
        
        # 如果未超限,直接返回
        if current_tokens <= self.max_tokens:
            return messages.copy()
        
        # 根据策略压缩
        if strategy == CompressionStrategy.TRUNCATE:
            return self._truncate(messages, keep_system)
        elif strategy == CompressionStrategy.SLIDING_WINDOW:
            return self._sliding_window(messages, keep_system)
        elif strategy == CompressionStrategy.IMPORTANCE:
            return self._importance_based(messages, keep_system)
        else:
            # 默认截断
            return self._truncate(messages, keep_system)
    
    async def summarize_history(
        self,
        messages: List[Dict[str, str]],
        llm_caller,
        max_summary_tokens: int = 200
    ) -> str:
        """
        使用LLM压缩历史为摘要
        
        Args:
            messages: 消息列表
            llm_caller: LLM调用器
            max_summary_tokens: 摘要最大token数
        
        Returns:
            摘要文本
        """
        if not messages:
            return ""
        
        # 构建摘要提示词
        history_text = self._format_messages(messages)
        
        summary_prompt = [
            {
                "role": "system",
                "content": "请用简洁的语言总结以下对话的核心内容,保留关键信息。"
            },
            {
                "role": "user",
                "content": f"对话内容:\n{history_text}\n\n请总结(不超过{max_summary_tokens}字):"
            }
        ]
        
        try:
            # 调用LLM生成摘要
            response = await llm_caller.generate(summary_prompt)
            summary = response.content
            
            logger.info(f"History summarized: {len(messages)} messages -> {len(summary)} chars")
            return summary
        
        except Exception as e:
            logger.error(f"Failed to summarize history: {e}")
            # 失败时返回简单截断
            return history_text[:max_summary_tokens]
    
    def estimate_tokens(self, messages: List[Dict[str, str]]) -> int:
        """
        估算消息列表的token数
        
        Args:
            messages: 消息列表
        
        Returns:
            估算的token总数
        """
        total = 0
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            total += self.token_estimator(role)
            total += self.token_estimator(content)
            total += 4  # 消息格式化开销
        
        total += 2  # 对话开始/结束标记
        return total
    
    def _truncate(
        self,
        messages: List[Dict[str, str]],
        keep_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        截断策略: 保留最近的消息
        
        Args:
            messages: 消息列表
            keep_system: 是否保留系统消息
        
        Returns:
            截断后的消息列表
        """
        # 分离系统消息和其他消息
        system_messages = []
        other_messages = []
        
        for msg in messages:
            if msg.get("role") == "system":
                system_messages.append(msg)
            else:
                other_messages.append(msg)
        
        # 从后往前保留消息直到达到token限制
        kept_messages = []
        current_tokens = 0
        
        # 如果保留系统消息,先计算其token
        if keep_system and system_messages:
            kept_messages.extend(system_messages)
            current_tokens = self.estimate_tokens(system_messages)
        
        # 从后往前添加其他消息
        for msg in reversed(other_messages):
            msg_tokens = self.token_estimator(msg.get("content", "")) + 6
            
            if current_tokens + msg_tokens <= self.max_tokens:
                kept_messages.insert(
                    len(system_messages) if keep_system else 0,
                    msg
                )
                current_tokens += msg_tokens
            else:
                # 如果一条都没保留,至少保留最近1条
                if len(kept_messages) == len(system_messages):
                    kept_messages.append(msg)
                break
        
        logger.info(
            f"Truncated: {len(messages)} -> {len(kept_messages)} messages, "
            f"tokens: {current_tokens}/{self.max_tokens}"
        )
        
        return kept_messages
    
    def _sliding_window(
        self,
        messages: List[Dict[str, str]],
        keep_system: bool = True,
        window_ratio: float = 0.5
    ) -> List[Dict[str, str]]:
        """
        滑动窗口策略: 保留开始和最近的消息
        
        Args:
            messages: 消息列表
            keep_system: 是否保留系统消息
            window_ratio: 窗口比例(保留前N%和后N%的消息)
        
        Returns:
            处理后的消息列表
        """
        # 分离系统消息
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]
        
        if not other_messages:
            return system_messages
        
        # 计算窗口大小
        window_size = max(1, int(len(other_messages) * window_ratio))
        
        # 保留开始和结尾的消息(按索引保留原始顺序)
        kept_indices = set(range(window_size))  # 前窗口索引
        kept_indices.update(range(len(other_messages) - window_size, len(other_messages)))  # 后窗口索引
        
        # 按原始顺序保留消息
        kept_other_messages = [other_messages[i] for i in sorted(kept_indices)]
        
        # 添加系统消息到开头
        kept_messages = []
        if keep_system and system_messages:
            kept_messages.extend(system_messages)
        kept_messages.extend(kept_other_messages)
        
        # 估算token,如果仍超限,使用截断
        if self.estimate_tokens(kept_messages) > self.max_tokens:
            return self._truncate(kept_messages, keep_system=False)
        
        logger.info(
            f"Sliding window: {len(messages)} -> {len(kept_messages)} messages "
            f"(window_size={window_size})"
        )
        
        return kept_messages
    
    def _importance_based(
        self,
        messages: List[Dict[str, str]],
        keep_system: bool = True
    ) -> List[Dict[str, str]]:
        """
        基于重要性的保留策略
        
        简化实现:
        - 系统消息(高)
        - 用户消息(中)
        - 助手消息(低)
        - 较长的消息更重要
        
        Args:
            messages: 消息列表
            keep_system: 是否保留系统消息
        
        Returns:
            处理后的消息列表
        """
        # 计算每条消息的重要性分数
        scored_messages = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # 基础分数
            base_score = {
                "system": 100,
                "user": 50,
                "assistant": 30
            }.get(role, 10)
            
            # 长度加成
            length_score = min(len(content) / 100, 20)
            
            # 位置加成(最近的消息更重要)
            position_score = (i / len(messages)) * 30
            
            total_score = base_score + length_score + position_score
            
            scored_messages.append((total_score, msg))
        
        # 按分数排序
        scored_messages.sort(key=lambda x: x[0], reverse=True)
        
        # 从高分到低分添加消息
        kept_messages = []
        current_tokens = 0
        
        for score, msg in scored_messages:
            msg_tokens = self.token_estimator(msg.get("content", "")) + 6
            
            if current_tokens + msg_tokens <= self.max_tokens:
                kept_messages.append(msg)
                current_tokens += msg_tokens
            else:
                break
        
        # 恢复原始顺序
        kept_messages_ordered = []
        for msg in messages:
            if msg in kept_messages:
                kept_messages_ordered.append(msg)
        
        logger.info(
            f"Importance-based: {len(messages)} -> {len(kept_messages_ordered)} messages"
        )
        
        return kept_messages_ordered
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> str:
        """
        格式化消息列表为文本
        
        Args:
            messages: 消息列表
        
        Returns:
            格式化的文本
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            role_name = {
                "user": "用户",
                "assistant": "助手",
                "system": "系统"
            }.get(role, role)
            
            lines.append(f"{role_name}: {content}")
        
        return "\n".join(lines)
    
    def _default_token_estimator(self, text: str) -> int:
        """
        默认token估算器(简单估算)
        
        英文: ~4字符/token
        中文: ~2字符/token
        
        Args:
            text: 文本
        
        Returns:
            估算的token数
        """
        if not text:
            return 0
        
        # 统计中英文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        # 估算
        chinese_tokens = chinese_chars // 2
        other_tokens = other_chars // 4
        
        return max(1, chinese_tokens + other_tokens)
    
    def set_max_tokens(self, max_tokens: int):
        """
        设置最大token数
        
        Args:
            max_tokens: 最大token数
        """
        self.max_tokens = max_tokens
        logger.info(f"Updated max_tokens to {max_tokens}")
    
    def set_token_estimator(self, estimator: Callable[[str], int]):
        """
        设置token估算器
        
        Args:
            estimator: token估算函数
        """
        self.token_estimator = estimator
        logger.info("Updated token estimator")
