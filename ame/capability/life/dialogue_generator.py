"""
对话生成器 - 基于上下文和用户意图生成对话回复

结合LLM和检索到的上下文信息生成个性化回复。
"""

from typing import List, Dict, Optional, Any, AsyncIterator
from loguru import logger

from ame.foundation.llm import LLMCallerBase, create_system_message, create_user_message
from ame.foundation.nlp import IntentType


class DialogueGenerator:
    """对话生成器
    
    基于意图、上下文和对话历史生成个性化回复。
    """
    
    def __init__(self, llm_caller: LLMCallerBase):
        """初始化
        
        Args:
            llm_caller: LLM调用器
        """
        self.llm = llm_caller
        self._system_prompts = self._init_system_prompts()
        logger.debug("DialogueGenerator初始化完成")
    
    def _init_system_prompts(self) -> Dict[IntentType, str]:
        """初始化不同意图的系统提示词
        
        Returns:
            意图到系统提示词的映射
        """
        return {
            IntentType.CHAT: """你是一个亲切的AI助手，名叫Another Me。
你了解用户的兴趣爱好和性格特点，能够进行自然、友好的对话。
请用温暖、真诚的语气回复用户。""",
            
            IntentType.QUERY_SELF: """你是用户的AI分身，对用户非常了解。
当用户询问关于自己的信息时，你应该基于已知的用户画像和历史数据给出准确的回答。
回答要具体、详细，展现你对用户的深入了解。""",
            
            IntentType.COMFORT: """你是一个善解人意、充满同理心的倾听者。
当用户情绪低落或需要安慰时，请用温柔、理解的语气回应。
可以分享相似的经历（如果有），给予支持和鼓励。""",
            
            IntentType.ANALYZE: """你是一个客观、专业的分析师。
当用户请求分析时，请基于已知信息给出有见地的分析和建议。
分析要客观、全面，同时保持友好的语气。""",
        }
    
    def _build_context_prompt(self, contexts: List[Dict[str, Any]]) -> str:
        """构建上下文提示
        
        Args:
            contexts: 上下文信息列表
            
        Returns:
            上下文提示字符串
        """
        if not contexts:
            return ""
        
        context_parts = ["以下是相关的背景信息：\n"]
        
        for i, ctx in enumerate(contexts, 1):
            ctx_type = ctx.get("type", "unknown")
            content = ctx.get("content", "")
            
            if ctx_type == "interest":
                context_parts.append(f"{i}. 用户的兴趣：{content}")
            elif ctx_type == "personality":
                context_parts.append(f"{i}. 用户的性格：{content}")
            elif ctx_type == "emotion_memory":
                emotion = ctx.get("emotion", "")
                context_parts.append(f"{i}. 相似情绪经历：{content} (情绪:{emotion})")
            elif ctx_type == "behavior":
                context_parts.append(f"{i}. 用户行为：{content}")
            elif ctx_type == "recent_memory":
                summary = ctx.get("summary", content)
                context_parts.append(f"{i}. 最近对话：{summary}")
            else:
                context_parts.append(f"{i}. {content}")
        
        return "\n".join(context_parts)
    
    async def generate(
        self,
        user_input: str,
        intent: IntentType = IntentType.CHAT,
        contexts: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> str:
        """生成对话回复（完整输出）
        
        Args:
            user_input: 用户输入
            intent: 意图类型
            contexts: 上下文信息列表
            conversation_history: 对话历史
            **kwargs: LLM参数
            
        Returns:
            生成的回复文本
        """
        try:
            # 构建消息
            messages = self._build_messages(
                user_input=user_input,
                intent=intent,
                contexts=contexts or [],
                conversation_history=conversation_history or []
            )
            
            # 生成回复
            response = await self.llm.generate(messages, **kwargs)
            
            logger.debug(f"生成回复成功，长度: {len(response.content)}")
            return response.content
            
        except Exception as e:
            logger.error(f"对话生成失败: {e}")
            return "抱歉，我现在无法回复。请稍后再试。"
    
    async def generate_stream(
        self,
        user_input: str,
        intent: IntentType = IntentType.CHAT,
        contexts: Optional[List[Dict[str, Any]]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """生成对话回复（流式输出）
        
        Args:
            user_input: 用户输入
            intent: 意图类型
            contexts: 上下文信息列表
            conversation_history: 对话历史
            **kwargs: LLM参数
            
        Yields:
            回复文本片段
        """
        try:
            # 构建消息
            messages = self._build_messages(
                user_input=user_input,
                intent=intent,
                contexts=contexts or [],
                conversation_history=conversation_history or []
            )
            
            # 流式生成
            async for chunk in self.llm.generate_stream(messages, **kwargs):
                yield chunk
            
            logger.debug("流式生成回复完成")
            
        except Exception as e:
            logger.error(f"流式对话生成失败: {e}")
            yield "抱歉，我现在无法回复。请稍后再试。"
    
    def _build_messages(
        self,
        user_input: str,
        intent: IntentType,
        contexts: List[Dict[str, Any]],
        conversation_history: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """构建完整的消息列表
        
        Args:
            user_input: 用户输入
            intent: 意图类型
            contexts: 上下文信息
            conversation_history: 对话历史
            
        Returns:
            消息列表
        """
        messages = []
        
        # 1. 系统提示词
        system_prompt = self._system_prompts.get(
            intent,
            self._system_prompts[IntentType.CHAT]
        )
        
        # 2. 添加上下文信息
        if contexts:
            context_prompt = self._build_context_prompt(contexts)
            system_prompt += f"\n\n{context_prompt}"
        
        messages.append(create_system_message(system_prompt))
        
        # 3. 添加对话历史（最近N轮）
        max_history = 10
        recent_history = conversation_history[-max_history:] if conversation_history else []
        messages.extend(recent_history)
        
        # 4. 当前用户输入
        messages.append(create_user_message(user_input))
        
        return messages
    
    def set_system_prompt(self, intent: IntentType, prompt: str):
        """设置特定意图的系统提示词
        
        Args:
            intent: 意图类型
            prompt: 系统提示词
        """
        self._system_prompts[intent] = prompt
        logger.info(f"更新意图 {intent.value} 的系统提示词")
    
    def get_system_prompt(self, intent: IntentType) -> str:
        """获取特定意图的系统提示词
        
        Args:
            intent: 意图类型
            
        Returns:
            系统提示词
        """
        return self._system_prompts.get(
            intent,
            self._system_prompts[IntentType.CHAT]
        )
