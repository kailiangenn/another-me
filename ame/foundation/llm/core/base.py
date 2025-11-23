"""
LLM调用器 - 核心层

提供统一的LLM调用抽象和组件能力集成。

设计原则:
1. 子类必须实现_call_llm和_stream_call_llm，保证返回格式统一
2. 对外只暴露chat、chat_stream、agent三个方法
3. ConversationHistory负责数据存储，HistoryManager负责功能管理
4. 组件能力可配置，适配不同场景
"""

from abc import ABC, abstractmethod
from typing import List, Dict, AsyncIterator, Optional, Callable, Any
from loguru import logger

from ..utils import LLMResponse, CompressContext, CompressResult, ConversationHistory
from ..components import (
    HistoryManager,
    PromptBuilder,
    CacheStrategy,
    CompressStrategy,
    RetryStrategy,
    CompressionStrategy
)


class BaseLLMCaller(ABC):
    """LLM调用器抽象基类
    
    设计原则:
    1. 强制实现规范: 子类必须实现_call_llm和_stream_call_llm
    2. 对外接口简化: 只暴露chat、chat_stream、agent三个方法
    3. 职责分离明确:
       - ConversationHistory: 数据存储（消息记录）
       - HistoryManager: 功能管理（压缩、截断等）
    4. 组件能力内置: 缓存、压缩、重试等自动应用
    
    对外接口:
    - chat() - 对话模式（自动管理历史）
    - chat_stream() - 流式对话
    - agent() - Agent任务（NER、分词等）
    
    子类必须实现:
    1. _call_llm() - 底层LLM调用
    2. _stream_call_llm() - 底层流式调用
    3. is_configured() - 配置检查
    """
    
    def __init__(
        self,
        model: str,
        max_tokens: int = 4000,
        # 组件实例（可选）
        history_manager: Optional[HistoryManager] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        cache_strategy: Optional[CacheStrategy] = None,
        compress_strategy: Optional[CompressStrategy] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        # 组件配置参数（用于创建默认实例）
        cache_enabled: bool = True,
        cache_max_size: int = 1000,
        cache_ttl: int = 3600,
        compress_threshold: float = 0.95,
        compress_keep_recent: int = 5,
        compress_keep_system: bool = True,
        retry_max_retries: int = 3,
        retry_backoff_factor: float = 0.5,
        retry_max_backoff: float = 10.0,
    ):
        """初始化LLM调用器
        
        Args:
            model: 模型名称
            max_tokens: 最大token数
            
            # 组件实例（直接传入，优先级最高）
            history_manager: 历史管理器
            prompt_builder: 提示词构建器
            cache_strategy: 缓存策略
            compress_strategy: 压缩策略
            retry_strategy: 重试策略
            
            # 缓存组件配置
            cache_enabled: 是否启用缓存
            cache_max_size: 缓存最大数量
            cache_ttl: 缓存过期时间(秒)
            
            # 压缩组件配置
            compress_threshold: 压缩阈值(0-1)
            compress_keep_recent: 保留最近N条消息
            compress_keep_system: 是否保留系统消息
            
            # 重试组件配置
            retry_max_retries: 最大重试次数
            retry_backoff_factor: 退避因子
            retry_max_backoff: 最大退避时间(秒)
        """
        self.model = model
        self.max_tokens = max_tokens
        
        # 初始化组件（优先使用传入的实例，否则根据参数创建）
        self.history_manager = history_manager or HistoryManager(
            max_tokens=max_tokens,
            token_estimator=self.estimate_tokens
        )
        
        self.prompt_builder = prompt_builder or PromptBuilder()
        
        self.cache_strategy = cache_strategy or CacheStrategy(
            max_size=cache_max_size,
            ttl=cache_ttl,
            enabled=cache_enabled
        )
        
        self.compress_strategy = compress_strategy or CompressStrategy(
            threshold=compress_threshold,
            keep_recent=compress_keep_recent,
            keep_system=compress_keep_system,
            keep_important=True  # 默认保留重要消息
        )
        
        self.retry_strategy = retry_strategy or RetryStrategy(
            max_retries=retry_max_retries,
            backoff_factor=retry_backoff_factor,
            max_backoff=retry_max_backoff
        )
        
        # 内置会话历史数据（ConversationHistory只负责数据存储）
        self._conversation = ConversationHistory()
    
    # ========================================================================
    # 抽象方法 - 子类必须实现（底层调用）
    # ========================================================================
    
    @abstractmethod
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """底层LLM调用（子类实现）
        
        这是内部方法，外部应使用chat()或agent()。
        
        Args:
            messages: 消息列表（已经过压缩处理）
            **kwargs: 额外参数
            
        Returns:
            LLMResponse: 响应结果
        """
        pass
    
    @abstractmethod
    async def _stream_call_llm(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """底层LLM流式调用（子类实现）
        
        这是内部方法，外部应使用chat_stream()。
        
        Args:
            messages: 消息列表（已经过压缩处理）
            **kwargs: 额外参数
            
        Yields:
            str: 文本片段
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """检查调用器是否已正确配置
        
        Returns:
            bool: 是否已配置
        """
        pass
    
    # ========================================================================
    # 对外接口 - 用户主要调用方法
    # ========================================================================
    
    async def chat(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        use_cache: bool = True,
        use_retry: bool = True,
        **kwargs
    ) -> LLMResponse:
        """对话模式（自动管理历史）
        
        特点:
        - 自动添加用户消息到会话历史
        - 自动应用历史管理（压缩、截断）
        - 支持缓存和重试
        - 自动记录助手响应
        
        流程:
        1. 添加用户消息到会话历史
        2. 获取完整消息列表（包含历史）
        3. 应用历史管理（HistoryManager）
        4. 缓存检查
        5. 消息压缩（如果需要）
        6. LLM调用（带重试）
        7. 记录助手响应
        8. 缓存设置
        
        Args:
            user_message: 用户消息内容
            system_message: 系统消息（可选，设置后会更新）
            use_cache: 是否使用缓存
            use_retry: 是否使用重试
            **kwargs: 传递给LLM的参数
            
        Returns:
            LLMResponse: 响应结果
            
        示例:
            # 基础对话
            response = await caller.chat("你好")
            
            # 带系统提示的对话
            response = await caller.chat(
                "解释量子力学",
                system_message="你是一个物理学教授"
            )
        """
        logger.debug(f"Chat - User: {user_message[:50]}...")
        
        # 1. 更新系统消息（如果提供）
        if system_message:
            self._conversation.system_message = system_message
        
        # 2. 添加用户消息到会话历史
        self._conversation.add_user_message(user_message)
        
        # 3. 获取完整消息列表（ConversationHistory提供数据）
        messages = self._conversation.get_messages(include_system=True)
        
        # 4. 应用历史管理（HistoryManager提供功能）
        managed_messages = self.history_manager.manage(
            messages,
            strategy=CompressionStrategy.TRUNCATE,
            keep_system=True
        )
        logger.debug(f"历史管理: {len(messages)} -> {len(managed_messages)} 条消息")
        
        # 5. 缓存检查
        if use_cache and self.cache_strategy.enabled:
            cache_key = self.cache_strategy.get_cache_key(
                managed_messages,
                self.model,
                **kwargs
            )
            cached = self.cache_strategy.get(cache_key)
            if cached:
                logger.debug("缓存命中")
                # 缓存命中也要记录到历史
                self._conversation.add_assistant_message(cached.content)
                return cached
        
        # 6. 消息压缩（如果需要）
        compress_context = CompressContext(
            messages=managed_messages,
            max_tokens=self.max_tokens,
            current_tokens=self.estimate_messages_tokens(managed_messages),
            token_estimator=self.estimate_tokens
        )
        
        final_messages = managed_messages
        if self.compress_strategy.should_compress(compress_context):
            compress_result = self.compress_strategy.compress(compress_context)
            final_messages = compress_result.kept_messages
            logger.debug(
                f"消息压缩: {compress_result.tokens_before} -> "
                f"{compress_result.tokens_after} tokens "
                f"(压缩比: {compress_result.compression_ratio:.1%})"
            )
        
        # 7. LLM调用（带重试）
        async def _execute():
            return await self._call_llm(final_messages, **kwargs)
        
        if use_retry:
            response = await self.retry_strategy.retry_with_backoff(_execute)
        else:
            response = await _execute()
        
        logger.debug(f"LLM响应: {len(response.content)} 字符")
        
        # 8. 记录助手响应到会话历史
        self._conversation.add_assistant_message(response.content)
        
        # 9. 缓存设置
        if use_cache and self.cache_strategy.enabled:
            self.cache_strategy.set(cache_key, response)
        
        return response
    
    async def chat_stream(
        self,
        user_message: str,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """流式对话模式
        
        特点:
        - 自动添加用户消息到会话历史
        - 自动应用历史管理
        - 流式返回响应
        - 自动记录完整助手响应
        
        注意: 流式调用不支持缓存
        
        Args:
            user_message: 用户消息内容
            system_message: 系统消息（可选）
            **kwargs: 传递给LLM的参数
            
        Yields:
            str: 文本片段
            
        示例:
            async for chunk in caller.chat_stream("讲个故事"):
                print(chunk, end='')
        """
        logger.debug(f"Chat Stream - User: {user_message[:50]}...")
        
        # 1. 更新系统消息
        if system_message:
            self._conversation.system_message = system_message
        
        # 2. 添加用户消息
        self._conversation.add_user_message(user_message)
        
        # 3. 获取完整消息列表
        messages = self._conversation.get_messages(include_system=True)
        
        # 4. 应用历史管理
        managed_messages = self.history_manager.manage(
            messages,
            strategy=CompressionStrategy.TRUNCATE,
            keep_system=True
        )
        
        # 5. 消息压缩
        compress_context = CompressContext(
            messages=managed_messages,
            max_tokens=self.max_tokens,
            current_tokens=self.estimate_messages_tokens(managed_messages),
            token_estimator=self.estimate_tokens
        )
        
        final_messages = managed_messages
        if self.compress_strategy.should_compress(compress_context):
            compress_result = self.compress_strategy.compress(compress_context)
            final_messages = compress_result.kept_messages
        
        # 6. 流式调用，收集完整响应
        full_response = ""
        async for chunk in self._stream_call_llm(final_messages, **kwargs):
            full_response += chunk
            yield chunk
        
        # 7. 记录完整助手响应
        self._conversation.add_assistant_message(full_response)
        logger.debug(f"Stream完成: {len(full_response)} 字符")
    
    async def agent(
        self,
        prompt: Optional[str] = None,
        task_type: str = "general",
        task_description: Optional[str] = None,
        few_shot_examples: Optional[List[Dict[str, str]]] = None,
        query: Optional[str] = None,
        instruction: Optional[str] = None,
        template: Optional[str] = None,
        variables: Optional[Dict[str, Any]] = None,
        use_cache: bool = False,
        use_retry: bool = True,
        **kwargs
    ) -> LLMResponse:
        """Agent模式调用（自动构建提示词）
        
        针对Agent任务的专用调用方法，如NER、分词、实体推理等。
        支持多种提示词构建方式：
        1. 直接传入prompt
        2. 使用few_shot_examples自动构建
        3. 使用template+variables构建
        
        特点:
        - 默认禁用缓存（Agent任务通常需要实时结果）
        - 不管理历史（Agent任务通常是单次调用）
        - 支持重试（提高任务成功率）
        
        Args:
            prompt: 直接传入的提示词（优先级最高）
            task_type: 任务类型（ner/tokenize/reasoning/general）
            task_description: 任务描述（用于few-shot）
            few_shot_examples: Few-shot示例列表 [{"input": "...", "output": "..."}]
            query: 查询内容（用于few-shot）
            instruction: 额外指令（用于few-shot）
            template: 提示词模板
            variables: 模板变量
            use_cache: 是否使用缓存（默认False）
            use_retry: 是否使用重试（默认True）
            **kwargs: 传递给LLM的参数
            
        Returns:
            LLMResponse: 响应结果
            
        示例:
            # 方式1: 直接传入prompt
            response = await caller.agent(
                prompt="从以下文本中提取人名: 张三在北京大学学习",
                task_type="ner"
            )
            
            # 方式2: 使用few-shot自动构建
            response = await caller.agent(
                task_description="命名实体识别",
                few_shot_examples=[
                    {"input": "李四在清华大学", "output": "[人名: 李四, 机构: 清华大学]"},
                ],
                query="张三在北京大学学习",
                task_type="ner"
            )
            
            # 方式3: 使用模板构建
            response = await caller.agent(
                template="对以下文本进行{task}: {text}",
                variables={"task": "分词", "text": "我爱自然语言处理"},
                task_type="tokenize"
            )
        """
        logger.debug(f"Agent - Task: {task_type}")
        
        # 构建最终的prompt
        final_prompt = None
        
        # 优先级 1: 直接传入的prompt
        if prompt:
            final_prompt = prompt
            logger.debug("使用直接传入的prompt")
        
        # 优先级 2: Few-shot构建
        elif few_shot_examples and query:
            if not task_description:
                task_description = f"{task_type} task"
            final_prompt = self.prompt_builder.build_few_shot(
                task_description=task_description,
                examples=few_shot_examples,
                query=query,
                instruction=instruction
            )
            logger.debug(f"few-shot构建 prompt, {len(few_shot_examples)} 个示例")
        
        # 优先级 3: 模板构建
        elif template:
            final_prompt = self.prompt_builder.build(
                template=template,
                variables=variables or {}
            )
            logger.debug("使用模板构建 prompt")
        
        # 如果没有任何构建方式，报错
        if not final_prompt:
            raise ValueError(
                "agent() 必须提供以下之一: "
                "1) prompt, 2) few_shot_examples+query, 3) template"
            )
        
        # 构建消息（Agent任务通常是单轮）
        messages = [{"role": "user", "content": final_prompt}]
        
        # 缓存检查
        cache_key = None
        if use_cache and self.cache_strategy.enabled:
            cache_key = self.cache_strategy.get_cache_key(
                messages,
                self.model,
                task_type=task_type,
                **kwargs
            )
            cached = self.cache_strategy.get(cache_key)
            if cached:
                logger.debug("缓存命中")
                return cached
        
        # LLM调用（带重试）
        async def _execute():
            return await self._call_llm(messages, **kwargs)
        
        if use_retry:
            response = await self.retry_strategy.retry_with_backoff(_execute)
        else:
            response = await _execute()
        
        # 缓存设置
        if use_cache and self.cache_strategy.enabled and cache_key:
            self.cache_strategy.set(cache_key, response)
        
        return response
    
    # ========================================================================
    # Token估算 - 提供默认实现，子类可覆盖
    # ========================================================================
    
    def estimate_tokens(self, text: str) -> int:
        """默认Token估算实现
        
        子类可选择覆盖此方法以提供更精确的估算。
        默认实现：
        - 中文：1字符 ≈ 1.5 token
        - 英文：1字符 ≈ 0.25 token
        
        Args:
            text: 待估算的文本
            
        Returns:
            int: 估算的token数
        """
        if not text:
            return 0
        
        # 统计中英文字符
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        english_chars = total_chars - chinese_chars
        
        return int(chinese_chars * 1.5 + english_chars * 0.25)
    
    def estimate_messages_tokens(self, messages: List[Dict[str, str]]) -> int:
        """估算消息列表的总token数
        
        考虑格式化开销（每条消息+4，对话标记+2）
        
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
    
    # ========================================================================
    # 会话历史数据访问接口（暴露ConversationHistory的数据能力）
    # ========================================================================
    
    def get_conversation_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """获取会话消息列表
        
        Args:
            include_system: 是否包含系统消息
            
        Returns:
            消息列表
        """
        return self._conversation.get_messages(include_system)
    
    def export_conversation(self) -> Dict[str, Any]:
        """导出完整会话数据
        
        Returns:
            包含消息、元数据和时间戳的完整数据
        """
        return self._conversation.export()
    
    def clear_conversation(self, clear_system: bool = False):
        """清空会话历史
        
        Args:
            clear_system: 是否也清空系统消息
        """
        self._conversation.clear(clear_system)
        logger.info("会话历史已清空")
    
    def set_system_message(self, content: str):
        """设置系统消息
        
        Args:
            content: 系统消息内容
        """
        self._conversation.system_message = content
    
    def get_system_message(self) -> Optional[str]:
        """获取系统消息
        
        Returns:
            系统消息内容
        """
        return self._conversation.system_message
