"""
对话过滤器 - 智能分类对话保留类型
职责：自动识别对话价值，决定保留策略（永久/临时/不存储）
"""
from typing import Dict, Any, Optional
from ame.models.domain import MemoryRetentionType
from ame.foundation.llm import LLMCallerBase
import re


class ConversationFilter:
    """
    对话过滤器 - 智能分类对话保留类型
    
    分类策略：
    1. 快速规则匹配（基于关键词）
    2. LLM 智能分类（复杂情况）
    3. 用户明确标记（context 中指定）
    """
    
    def __init__(self, llm_caller: Optional[LLMCallerBase] = None):
        """
        Args:
            llm_caller: LLM 调用器（用于复杂分类）
        """
        self.llm = llm_caller
        
        # 关键词规则（快速分类）
        self.permanent_keywords = [
            "学习", "笔记", "总结", "重要", "记录", "保存",
            "经验", "教训", "思考", "反思", "项目", "计划",
            "决定", "决策", "会议", "讨论", "方案", "设计"
        ]
        
        self.casual_keywords = [
            "你好", "再见", "谢谢", "好的", "ok", "收到",
            "天气", "晚安", "早上好", "嗯", "哦", "啊",
            "test", "测试"
        ]
        
        self.temporary_keywords = [
            "今天", "明天", "待办", "提醒", "临时",
            "一会", "稍后", "马上", "现在"
        ]
    
    async def classify_conversation(
        self, 
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> MemoryRetentionType:
        """
        分类对话保留类型
        
        Args:
            user_message: 用户消息
            context: 上下文信息（可包含 retention_type 明确指定）
        
        Returns:
            retention_type: 保留类型
        """
        # 1. 用户明确指定
        if context and "retention_type" in context:
            return MemoryRetentionType(context["retention_type"])
        
        # 2. 快速规则匹配
        message_lower = user_message.lower()
        
        # 永久存储关键词
        if any(kw in message_lower for kw in self.permanent_keywords):
            return MemoryRetentionType.PERMANENT
        
        # 普通聊天关键词
        if any(kw in message_lower for kw in self.casual_keywords):
            # 短消息直接判断为闲聊
            if len(user_message.strip()) < 20:
                return MemoryRetentionType.CASUAL_CHAT
        
        # 临时记忆关键词
        if any(kw in message_lower for kw in self.temporary_keywords):
            return MemoryRetentionType.TEMPORARY
        
        # 3. 基于消息长度的启发式判断
        message_length = len(user_message.strip())
        
        # 很短的消息 (<10 字符) → 闲聊
        if message_length < 10:
            return MemoryRetentionType.CASUAL_CHAT
        
        # 中等长度 (10-50) → 临时
        if message_length < 50:
            return MemoryRetentionType.TEMPORARY
        
        # 长消息 (>50) → 可能重要，使用 LLM 分类
        if self.llm and message_length > 50:
            return await self._llm_classify(user_message)
        
        # 4. 默认为临时记忆
        return MemoryRetentionType.TEMPORARY
    
    async def _llm_classify(self, message: str) -> MemoryRetentionType:
        """
        使用 LLM 分类对话类型
        
        Args:
            message: 用户消息
        
        Returns:
            retention_type: 保留类型
        """
        prompt = f"""请分析以下对话并判断其保留类型：

对话内容：{message}

保留类型：
- permanent: 重要内容，需要长期学习和记忆（如：学习笔记、工作经验、重要决定、项目讨论）
- temporary: 临时信息，7天后可以清理（如：待办事项、短期提醒、临时想法）
- casual_chat: 普通聊天，无需存储（如：闲聊、问候、简单回复、测试消息）

只返回类型名称（permanent/temporary/casual_chat），不要解释。
"""
        
        try:
            # 调用 LLM
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            result = response.content.strip().lower()
            
            # 解析结果
            if "permanent" in result:
                return MemoryRetentionType.PERMANENT
            elif "casual" in result:
                return MemoryRetentionType.CASUAL_CHAT
            else:
                return MemoryRetentionType.TEMPORARY
        
        except Exception as e:
            # LLM 调用失败，降级为临时记忆
            return MemoryRetentionType.TEMPORARY
    
    def should_store(self, retention_type: MemoryRetentionType) -> bool:
        """
        判断是否应该存储该对话
        
        Args:
            retention_type: 保留类型
        
        Returns:
            should_store: 是否存储
        """
        return retention_type != MemoryRetentionType.CASUAL_CHAT
    
    def get_ttl_days(self, retention_type: MemoryRetentionType) -> Optional[int]:
        """
        获取存活时间（天）
        
        Args:
            retention_type: 保留类型
        
        Returns:
            ttl_days: 存活天数（None 表示永久）
        """
        if retention_type == MemoryRetentionType.PERMANENT:
            return None  # 永久存储
        elif retention_type == MemoryRetentionType.TEMPORARY:
            return 7  # 7天后删除
        else:  # CASUAL_CHAT
            return 1  # 1天后删除（如果存储了的话）
