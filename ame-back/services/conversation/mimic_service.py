"""
Mimic Service - 智能对话服务

整合 Capabilities Layer 完整能力,提供:
- 内容安全过滤(不健康内容检测与警告)
- 意图识别(聊天/搜索/记忆/分析)
- 智能路由(根据意图调用不同能力)
- 风格模仿(学习用户表达习惯)
- 记忆管理(自动分类保留)
"""

from typing import Dict, Any, Optional, AsyncIterator, List
from datetime import datetime
import logging

from ame.foundation.llm import LLMResponse
from ame.capabilities.memory import ConversationFilter
from ame.capabilities.intent import UserIntent
from ame.capabilities.factory import CapabilityFactory
from ame.models.domain import MemoryRetentionType

logger = logging.getLogger(__name__)


class MimicService:
    """
    智能对话服务 - 项目核心交互入口
    
    职责:
    1. 内容安全: 不健康内容检测与警告
    2. 意图识别: 自动判断用户意图
    3. 智能路由: 根据意图调用最合适的能力
    4. 风格模仿: 学习并模仿用户表达风格
    5. 记忆管理: 自动分类和存储对话记忆
    6. 知识检索: RAG 知识库问答
    """
    
    # 不健康内容关键词库
    UNSAFE_KEYWORDS = [
        "色情", "暴力", "赌博", "毒品", "自杀", "自残",
        "仇恨", "歧视", "恐怖", "政治敏感", "违法", "犯罪"
    ]
    
    def __init__(
        self,
        # 核心依赖: 使用已创建的 CapabilityFactory
        capability_factory: CapabilityFactory,
        # 配置选项
        enable_safety_filter: bool = True,
        enable_intent_recognition: bool = True,
        enable_memory: bool = True
    ):
        """
        初始化智能对话服务
        
        设计理念:
        - 通过依赖注入接收 CapabilityFactory，而非在内部创建
        - 利用 factory 的缓存机制，避免重复创建能力实例
        - 遵循单一职责原则，专注于对话服务逻辑
        
        Args:
            capability_factory: 能力工厂实例(由外部创建并注入)
            enable_safety_filter: 是否启用内容安全过滤
            enable_intent_recognition: 是否启用意图识别
            enable_memory: 是否启用记忆管理
        
        Example:
            >>> from ame.capabilities import CapabilityFactory
            >>> factory = CapabilityFactory(
            ...     llm_caller=llm,
            ...     vector_store=vector_store,
            ...     # ... 其他依赖
            ... )
            >>> mimic_service = MimicService(
            ...     capability_factory=factory,
            ...     enable_safety_filter=True
            ... )
        """
        self.factory = capability_factory
        self.llm = capability_factory.llm  # 从 factory 获取 LLM
        self.enable_safety = enable_safety_filter
        self.enable_intent = enable_intent_recognition
        self.enable_memory = enable_memory
        
        # 初始化核心能力(使用 factory 创建)
        self.conversation_filter = ConversationFilter(self.llm)
        
        # 意图识别能力
        if enable_intent_recognition:
            self.intent_recognizer = self.factory.create_intent_recognizer(
                cache_key="mimic_intent"
            )
        else:
            self.intent_recognizer = None
        
        # 记忆管理能力
        if enable_memory:
            self.memory_manager = self.factory.create_memory_manager(
                cache_key="mimic_memory"
            )
        else:
            self.memory_manager = None
        
        # 检索能力(高级混合检索)
        self.retriever = self.factory.create_retriever(
            pipeline_mode="advanced",
            cache_key="mimic_retriever"
        )
        
        # 生成能力
        self.rag_generator = self.factory.create_rag_generator(
            cache_key="mimic_rag"
        )
        
        self.style_generator = self.factory.create_style_generator(
            with_retriever=True,
            cache_key="mimic_style"
        )
        
        logger.info(
            f"MimicService 初始化完成 "
            f"(安全过滤={enable_safety_filter}, "
            f"意图识别={enable_intent_recognition}, "
            f"记忆管理={enable_memory})"
        )
    
    async def check_content_safety(self, message: str) -> Dict[str, Any]:
        """内容安全检测"""
        if not self.enable_safety:
            return {"is_safe": True, "warning": None, "severity": "low", "matched_keywords": []}
        
        # 关键词检测
        message_lower = message.lower()
        matched = [kw for kw in self.UNSAFE_KEYWORDS if kw in message_lower]
        
        if matched:
            return {
                "is_safe": False,
                "warning": f"检测到不当内容,请文明交流。匹配关键词:{', '.join(matched[:3])}",
                "severity": "high",
                "matched_keywords": matched
            }
        
        # LLM 语义检测(长文本)
        if len(message) > 100:
            try:
                prompt = f"""请判断以下内容是否包含不健康或不当信息(色情、暴力、仇恨、违法等)。

内容:{message}

只回答:安全 或 不安全"""
                
                response = await self.llm.generate(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                
                result = response.content.strip()
                
                if "不安全" in result:
                    return {
                        "is_safe": False,
                        "warning": "系统检测到内容可能不适合,请注意交流内容的健康性。",
                        "severity": "medium",
                        "matched_keywords": []
                    }
            except Exception as e:
                logger.warning(f"LLM 安全检测失败: {e}")
        
        return {"is_safe": True, "warning": None, "severity": "low", "matched_keywords": []}
    
    async def learn_from_conversation(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从对话中学习并存储"""
        retention_type = await self.conversation_filter.classify_conversation(
            user_message, context=context
        )
        
        should_store = self.conversation_filter.should_store(retention_type)
        
        if not should_store or not self.enable_memory or not self.memory_manager:
            return {"retention_type": retention_type, "stored": False, "memory_id": None}
        
        try:
            importance = 0.8 if retention_type == MemoryRetentionType.PERMANENT else 0.5
            
            memory_id = await self.memory_manager.store(
                content=user_message,
                importance=importance,
                category="conversation",
                tags=[retention_type.value],
                metadata={
                    "source": "user_conversation",
                    "retention_type": retention_type.value,
                    "context": context or {}
                }
            )
            
            logger.info(f"存储对话记忆: {memory_id} (类型={retention_type.value})")
            
            return {"retention_type": retention_type, "stored": True, "memory_id": memory_id}
        except Exception as e:
            logger.error(f"存储对话记忆失败: {e}")
            return {"retention_type": retention_type, "stored": False, "memory_id": None}
    
    async def chat(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        enable_safety_check: bool = True,
        enable_auto_route: bool = True
    ) -> Dict[str, Any]:
        """智能对话主入口"""
        # 1. 安全检测
        safety_result = {"is_safe": True, "warning": None}
        if enable_safety_check:
            safety_result = await self.check_content_safety(user_message)
            
            if not safety_result["is_safe"]:
                return {
                    "response": f"⚠️ {safety_result['warning']}\n\n我是你的AI分身,希望我们的对话是积极健康的。有什么我可以帮助你的吗?",
                    "intent": UserIntent.UNKNOWN,
                    "safety_check": safety_result,
                    "memory_stored": False,
                    "route": "safety_filter"
                }
        
        # 2. 意图识别
        intent = UserIntent.CHAT
        intent_confidence = 0.5
        
        if enable_auto_route and self.enable_intent:
            intent_result = await self.intent_recognizer.recognize(
                text=user_message, context=context
            )
            intent = intent_result.intent
            intent_confidence = intent_result.confidence
            
            logger.info(f"识别意图: {intent.value} (置信度={intent_confidence:.2f})")
        
        # 3. 智能路由
        response_text = ""
        route = "unknown"
        
        if intent == UserIntent.SEARCH:
            response_text, route = await self._handle_search(user_message, context)
        elif intent == UserIntent.RECALL:
            response_text, route = await self._handle_recall(user_message, context)
        elif intent == UserIntent.ANALYZE:
            response_text, route = await self._handle_analyze(user_message, context)
        else:
            response_text, route = await self._handle_chat(user_message, context)
        
        # 4. 存储记忆
        memory_result = await self.learn_from_conversation(user_message, context)
        
        return {
            "response": response_text,
            "intent": intent,
            "safety_check": safety_result,
            "memory_stored": memory_result["stored"],
            "route": route,
            "metadata": {
                "intent_confidence": intent_confidence,
                "retention_type": memory_result["retention_type"].value
            }
        }
    
    async def chat_stream(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        enable_safety_check: bool = True
    ) -> AsyncIterator[str]:
        """流式智能对话"""
        # 安全检测
        if enable_safety_check:
            safety_result = await self.check_content_safety(user_message)
            if not safety_result["is_safe"]:
                yield f"⚠️ {safety_result['warning']}\n\n"
                yield "我是你的AI分身,希望我们的对话是积极健康的。有什么我可以帮助你的吗?"
                return
        
        # 意图识别
        intent = UserIntent.CHAT
        if self.enable_intent:
            try:
                intent_result = await self.intent_recognizer.recognize(
                    text=user_message, context=context
                )
                intent = intent_result.intent
            except:
                pass
        
        # 检索历史
        relevant_history = []
        if self.retriever:
            try:
                results = await self.retriever.retrieve(query=user_message, top_k=3)
                relevant_history = [{"content": r.content, "score": r.score} for r in results]
            except:
                pass
        
        # 构建提示词并流式生成
        system_prompt = self._build_mimic_prompt(relevant_history, intent)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        async for chunk in self.llm.generate_stream(messages=messages, temperature=0.8):
            yield chunk
        
        # 后台存储记忆
        try:
            await self.learn_from_conversation(user_message, context)
        except Exception as e:
            logger.error(f"后台存储记忆失败: {e}")
    
    async def _handle_search(self, query: str, context: Optional[Dict]) -> tuple:
        """处理搜索意图"""
        try:
            result = await self.rag_generator.generate_with_citations(query=query, context=context, top_k=5)
            response = result["answer"]
            if result["citations"]:
                response += f"\n\n📚 参考了 {result['source_count']} 条知识"
            return response, "rag_search"
        except Exception as e:
            logger.error(f"搜索处理失败: {e}")
            return "抱歉,搜索功能暂时遇到问题。", "error"
    
    async def _handle_recall(self, query: str, context: Optional[Dict]) -> tuple:
        """处理回忆意图"""
        if not self.memory_manager:
            return "记忆功能尚未启用。", "no_memory"
        
        try:
            memories = await self.memory_manager.retrieve(query=query, top_k=5)
            if not memories:
                return "我暂时没有找到相关的记忆。", "recall_empty"
            
            response = "我回想起:\n\n"
            for i, mem in enumerate(memories[:3], 1):
                response += f"{i}. {mem.content[:100]}...\n"
            
            return response, "memory_recall"
        except Exception as e:
            logger.error(f"回忆处理失败: {e}")
            return "抱歉,回忆功能遇到问题。", "error"
    
    async def _handle_analyze(self, query: str, context: Optional[Dict]) -> tuple:
        """处理分析意图"""
        return "分析功能正在开发中,敬请期待。", "analyze_pending"
    
    async def _handle_chat(self, query: str, context: Optional[Dict]) -> tuple:
        """处理聊天意图"""
        try:
            # 检索历史风格
            relevant_history = []
            if self.retriever:
                results = await self.retriever.retrieve(query=query, top_k=3)
                relevant_history = [{"content": r.content} for r in results]
            
            # 生成回复
            system_prompt = self._build_mimic_prompt(relevant_history, UserIntent.CHAT)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
            
            response = await self.llm.generate(messages=messages, temperature=0.8)
            return response.content, "mimic_chat"
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            return "抱歉,我现在有点状况。", "error"
    
    def _build_mimic_prompt(self, relevant_history: list, intent: UserIntent = UserIntent.CHAT) -> str:
        """构建模仿提示词"""
        prompt = """你是用户的 AI 分身,任务是用用户的风格和方式回答问题。

**重要事项**:
1. 用第一人称"我"来表达,而不是"用户"或"他/她"
2. 模仿用户的说话风格、惯用词汇和表达习惯
3. 保持真实感,不要过于形式化
4. 如果不确定,可以说"我不太确定"或"我需要想想"
"""
        
        if relevant_history:
            prompt += "\n**参考用户的历史表达**(学习风格):\n"
            for i, h in enumerate(relevant_history[:3], 1):
                content = h.get('content', '')[:150]
                prompt += f"{i}. {content}...\n"
            prompt += "\n请模仿上述表达风格来回答。\n"
        
        return prompt
