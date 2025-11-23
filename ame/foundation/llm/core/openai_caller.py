"""
OpenAI调用器 - 核心层

优化版OpenAI调用器，使用tiktoken精确估算token。
继承BaseLLMCaller，自动获得所有组件能力。
"""

from typing import Optional, List, Dict, AsyncIterator
from openai import AsyncOpenAI
from loguru import logger

try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    logger.warning("tiktoken未安装，将使用简单估算方法")

from .base import BaseLLMCaller
from ..utils import LLMResponse
from ..components import (
    HistoryManager,
    PromptBuilder,
    CacheStrategy,
    CompressStrategy,
    RetryStrategy,
)


class OpenAICaller(BaseLLMCaller):
    """OpenAI调用器（优化版）
    
    主要特点：
    1. 使用tiktoken精确估算token
    2. 继承BaseLLMCaller，自动获得所有组件能力
    3. 用户调用call()和stream_call()时，自动应用缓存、压缩、重试
    
    使用方法：
        # 创建调用器
        caller = OpenAICaller(api_key="sk-xxx", model="gpt-3.5-turbo")
        
        # 自动应用所有组件能力（推荐）
        response = await caller.call(messages)  # 自动缓存+压缩+重试
        
        # 灵活控制组件启用
        response = await caller.call(messages, use_cache=False)  # 禁用缓存
        response = await caller.call(messages, auto_compress=False)  # 禁用压缩
        response = await caller.call(messages, use_retry=False)  # 禁用重试
        
        # 流式调用
        async for chunk in caller.stream_call(messages):  # 自动压缩
            print(chunk, end='')
    
    可用组件方法（继承自BaseLLMCaller）：
    - manage_history(): 历史管理
    - build_prompt(): 提示词构建
    - build_with_history(): 带历史的提示词
    - build_few_shot(): Few-shot提示词
    - get_cache(): 获取缓存
    - set_cache(): 设置缓存
    - compress_messages(): 压缩消息
    - retry_execute(): 重试执行
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        organization: Optional[str] = None,
        max_tokens: int = 4000,
        # 组件配置（可选）
        history_manager: Optional[HistoryManager] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        cache_strategy: Optional[CacheStrategy] = None,
        compress_strategy: Optional[CompressStrategy] = None,
        retry_strategy: Optional[RetryStrategy] = None,
    ):
        """初始化OpenAI调用器
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            base_url: API基础URL（可选，用于代理）
            timeout: 超时时间（秒）
            organization: 组织ID（可选）
            max_tokens: 最大token数
            history_manager: 历史管理器（可选）
            prompt_builder: 提示词构建器（可选）
            cache_strategy: 缓存策略（可选）
            compress_strategy: 压缩策略（可选）
            retry_strategy: 重试策略（可选）
        """
        # 初始化基类（集成组件能力）
        super().__init__(
            model=model,
            max_tokens=max_tokens,
            history_manager=history_manager,
            prompt_builder=prompt_builder,
            cache_strategy=cache_strategy,
            compress_strategy=compress_strategy,
            retry_strategy=retry_strategy,
        )
        
        # OpenAI特有配置
        self.api_key = api_key
        self.base_url = base_url
        self.timeout = timeout
        self.organization = organization
        
        # 创建异步客户端
        self._client = None
        if api_key:
            self._client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout,
                organization=organization,
                max_retries=0  # 重试由RetryStrategy处理
            )
        
        # 初始化tiktoken编码器
        self._encoding = None
        if TIKTOKEN_AVAILABLE:
            try:
                self._encoding = tiktoken.encoding_for_model(model)
            except KeyError:
                # 模型不在tiktoken支持列表中，使用默认编码
                logger.warning(f"模型 {model} 不在tiktoken支持列表中，使用cl100k_base编码")
                self._encoding = tiktoken.get_encoding("cl100k_base")
    
    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数
        
        使用tiktoken精确估算（如果可用），否则使用简单估算。
        
        Args:
            text: 待估算的文本
            
        Returns:
            int: 估算的token数
        """
        if not text:
            return 0
        
        if self._encoding:
            # 使用tiktoken精确估算
            return len(self._encoding.encode(text))
        else:
            # 简单估算：中文按1字符=1.5token，英文按1单词=1.3token
            chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            total_chars = len(text)
            english_chars = total_chars - chinese_chars
            
            return int(chinese_chars * 1.5 + english_chars * 0.25)
    
    def is_configured(self) -> bool:
        """检查调用器是否已正确配置
        
        Returns:
            bool: 是否已配置
        """
        return bool(self.api_key and self._client)
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs
    ) -> LLMResponse:
        """底层OpenAI调用实现
        
        注意：外部应使用call()方法，它会自动应用组件能力。
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数（0-2）
            max_tokens: 最大生成token数
            top_p: nucleus采样参数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
            **kwargs: 其他OpenAI参数
            
        Returns:
            LLMResponse: 完整的响应结果
            
        Raises:
            RuntimeError: 如果调用器未配置
        """
        if not self.is_configured():
            error_msg = "OpenAICaller未正确配置，请检查API密钥"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                **kwargs
            )
            
            # 提取响应内容
            content = response.choices[0].message.content or ""
            
            # 构建使用信息
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                metadata={
                    "id": response.id,
                    "created": response.created,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
        
        except Exception as e:
            error_msg = f"OpenAI生成失败: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise
    
    async def _stream_call_llm(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: float = 1.0,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        **kwargs
    ) -> AsyncIterator[str]:
        """底层OpenAI流式调用实现
        
        注意：外部应使用stream_call()方法，它会自动应用组件能力。
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            top_p: nucleus采样参数
            frequency_penalty: 频率惩罚
            presence_penalty: 存在惩罚
            **kwargs: 其他OpenAI参数
            
        Yields:
            str: 流式输出的文本片段
            
        Raises:
            RuntimeError: 如果调用器未配置
        """
        if not self.is_configured():
            error_msg = "OpenAICaller未正确配置，请检查API密钥"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stream=True,
                **kwargs
            )
            
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        
        except Exception as e:
            error_msg = f"OpenAI流式生成失败: {type(e).__name__}: {e}"
            logger.error(error_msg)
            raise
    
    @property
    def client(self) -> Optional[AsyncOpenAI]:
        """获取底层OpenAI客户端（仅在需要高级功能时使用）"""
        return self._client
