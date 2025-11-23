"""
测试LLM架构重构后的基本结构

验证：
1. 数据模型正确性
2. 组件独立可用性
3. BaseLLMCaller组件能力集成
4. OpenAICaller继承正确性
"""

import pytest
from typing import List, Dict, AsyncIterator

from ame.foundation.llm.utils import (
    CallMode,
    LLMResponse,
    CompressContext,
    CompressResult,
    create_user_message,
    create_assistant_message,
    create_system_message,
)

from ame.foundation.llm.utils.exceptions import (
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
)

from ame.foundation.llm.components import (
    HistoryManager,
    PromptBuilder,
    CacheStrategy,
    CompressStrategy,
    SessionCompressStrategy,
    DocumentCompressStrategy,
    ChunkingCompressStrategy,
    RetryStrategy,
)

from ame.foundation.llm.core import (
    BaseLLMCaller,
    OpenAICaller,
)


# ============================================================================
# 测试 Utils Layer
# ============================================================================

class TestDataModels:
    """测试数据模型"""
    
    def test_llm_response(self):
        """测试LLMResponse模型"""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop"
        )
        
        assert response.content == "Hello, world!"
        assert response.total_tokens == 15
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
    
    def test_compress_context(self):
        """测试CompressContext"""
        def token_estimator(text: str) -> int:
            return len(text)
        
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        context = CompressContext(
            messages=messages,
            max_tokens=100,
            token_estimator=token_estimator,
            current_tokens=50
        )
        
        assert context.max_tokens == 100
        assert context.current_tokens == 50
        assert len(context.messages) == 2
    
    def test_compress_result(self):
        """测试CompressResult"""
        result = CompressResult(
            kept_messages=[{"role": "user", "content": "Hello"}],
            removed_messages=[{"role": "assistant", "content": "Old message"}],
            tokens_before=100,
            tokens_after=50,
            compression_ratio=0.5
        )
        
        assert result.saved_tokens == 50
        assert result.compression_ratio == 0.5
    
    def test_message_helpers(self):
        """测试消息创建辅助函数"""
        user_msg = create_user_message("Hello", importance=1.0)
        assert user_msg["role"] == "user"
        assert user_msg["content"] == "Hello"
        assert user_msg["metadata"]["importance"] == 1.0
        
        assistant_msg = create_assistant_message("Hi!")
        assert assistant_msg["role"] == "assistant"
        
        system_msg = create_system_message("You are helpful")
        assert system_msg["role"] == "system"


class TestExceptions:
    """测试异常层次结构"""
    
    def test_exception_hierarchy(self):
        """测试异常继承关系"""
        assert issubclass(CallerNotConfiguredError, LLMError)
        assert issubclass(TokenLimitExceededError, LLMError)
        assert issubclass(CompressionError, LLMError)
        assert issubclass(CacheError, LLMError)
    
    def test_exception_raising(self):
        """测试异常抛出"""
        with pytest.raises(CallerNotConfiguredError):
            raise CallerNotConfiguredError("Not configured")
        
        with pytest.raises(LLMError):
            raise TokenLimitExceededError("Token limit exceeded")


# ============================================================================
# 测试 Components Layer
# ============================================================================

class TestComponents:
    """测试组件独立性"""
    
    def test_history_manager(self):
        """测试HistoryManager独立使用"""
        manager = HistoryManager(max_tokens=100)
        
        messages = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"},
        ]
        
        from ame.foundation.llm.components.history_manager import CompressionStrategy
        result = manager.manage(messages, CompressionStrategy.TRUNCATE)
        
        assert isinstance(result, list)
        assert len(result) <= len(messages)
    
    def test_prompt_builder(self):
        """测试PromptBuilder独立使用"""
        builder = PromptBuilder()
        
        # 基础构建
        prompt = builder.build("Hello ${name}", {"name": "World"})
        assert "World" in prompt
        
        # Few-shot
        examples = [
            {"input": "Good", "output": "Positive"},
            {"input": "Bad", "output": "Negative"}
        ]
        few_shot = builder.build_few_shot("Sentiment", examples, "Great")
        assert "Sentiment" in few_shot
        assert "Good" in few_shot
    
    def test_cache_strategy(self):
        """测试CacheStrategy独立使用"""
        cache = CacheStrategy(max_size=10, ttl=60)
        
        messages = [{"role": "user", "content": "test"}]
        cache_key = cache.get_cache_key(messages, "gpt-3.5-turbo")
        
        assert isinstance(cache_key, str)
        assert len(cache_key) == 32  # MD5 hash length
        
        # 测试缓存操作
        response = LLMResponse(content="test", model="gpt-3.5-turbo")
        cache.set(cache_key, response)
        
        cached = cache.get(cache_key)
        assert cached is not None
        assert cached.content == "test"
    
    def test_compress_strategies(self):
        """测试压缩策略"""
        def token_estimator(text: str) -> int:
            return len(text)
        
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "Good!"},
        ]
        
        # SessionCompressStrategy
        session_strategy = SessionCompressStrategy(threshold=0.5, keep_recent=1)
        context = CompressContext(
            messages=messages,
            max_tokens=50,
            token_estimator=token_estimator,
            current_tokens=100
        )
        
        assert session_strategy.should_compress(context)
        result = session_strategy.compress(context)
        assert len(result.kept_messages) < len(messages)
        
        # DocumentCompressStrategy
        doc_strategy = DocumentCompressStrategy(threshold=0.5)
        assert doc_strategy.should_compress(context)


# ============================================================================
# 测试 Core Layer
# ============================================================================

class MockLLMCaller(BaseLLMCaller):
    """模拟LLM调用器用于测试"""
    
    async def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        return LLMResponse(
            content="Mock response",
            model=self.model,
            usage={"total_tokens": 10}
        )
    
    async def stream_call(self, messages: List[Dict[str, str]], **kwargs) -> AsyncIterator[str]:
        for chunk in ["Hello", " ", "World"]:
            yield chunk
    
    def is_configured(self) -> bool:
        return True


class TestBaseLLMCaller:
    """测试BaseLLMCaller组件能力集成"""
    
    @pytest.fixture
    def caller(self):
        """创建测试调用器"""
        return MockLLMCaller(model="test-model", max_tokens=4000)
    
    def test_initialization(self, caller):
        """测试初始化和组件自动创建"""
        assert caller.model == "test-model"
        assert caller.max_tokens == 4000
        
        # 检查组件是否已创建
        assert isinstance(caller.history_manager, HistoryManager)
        assert isinstance(caller.prompt_builder, PromptBuilder)
        assert isinstance(caller.cache_strategy, CacheStrategy)
        assert isinstance(caller.compress_strategy, CompressStrategy)
        assert isinstance(caller.retry_strategy, RetryStrategy)
    
    def test_token_estimation(self, caller):
        """测试Token估算"""
        # 默认估算
        tokens = caller.estimate_tokens("Hello World")
        assert tokens > 0
        
        # 消息列表估算
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"}
        ]
        total_tokens = caller.estimate_messages_tokens(messages)
        assert total_tokens > 0
    
    def test_history_management(self, caller):
        """测试历史管理能力"""
        messages = [
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
        ]
        
        from ame.foundation.llm.components.history_manager import CompressionStrategy
        result = caller.manage_history(messages, CompressionStrategy.TRUNCATE)
        assert isinstance(result, list)
    
    def test_prompt_building(self, caller):
        """测试提示词构建能力"""
        # 基础构建
        prompt = caller.build_prompt("Hello ${name}", {"name": "Test"})
        assert "Test" in prompt
        
        # Few-shot构建
        examples = [{"input": "A", "output": "B"}]
        few_shot = caller.build_few_shot("Task", examples, "Query")
        assert "Task" in few_shot
    
    def test_cache_operations(self, caller):
        """测试缓存能力"""
        messages = [{"role": "user", "content": "test"}]
        
        # 缓存不存在
        cached = caller.get_cache(messages)
        assert cached is None
        
        # 设置缓存
        response = LLMResponse(content="cached", model="test")
        caller.set_cache(messages, response)
        
        # 获取缓存
        cached = caller.get_cache(messages)
        assert cached is not None
        assert cached.content == "cached"
    
    def test_compression(self, caller):
        """测试压缩能力"""
        messages = [
            {"role": "user", "content": "m" * 1000},
            {"role": "assistant", "content": "m" * 1000},
        ]
        
        result = caller.compress_messages(messages, max_tokens=100)
        assert isinstance(result, CompressResult)
    
    @pytest.mark.asyncio
    async def test_retry_execution(self, caller):
        """测试重试能力"""
        call_count = [0]
        
        async def flaky_func():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Temporary error")
            return "Success"
        
        result = await caller.retry_execute(flaky_func)
        assert result == "Success"
        assert call_count[0] == 2


class TestOpenAICaller:
    """测试OpenAICaller"""
    
    def test_initialization(self):
        """测试初始化"""
        caller = OpenAICaller(
            api_key="test-key",
            model="gpt-3.5-turbo",
            max_tokens=8000
        )
        
        assert caller.model == "gpt-3.5-turbo"
        assert caller.api_key == "test-key"
        assert caller.max_tokens == 8000
        
        # 检查组件能力继承
        assert hasattr(caller, 'manage_history')
        assert hasattr(caller, 'build_prompt')
        assert hasattr(caller, 'get_cache')
        assert hasattr(caller, 'compress_messages')
        assert hasattr(caller, 'retry_execute')
    
    def test_token_estimation_with_tiktoken(self):
        """测试使用tiktoken的Token估算"""
        caller = OpenAICaller(api_key="test-key")
        
        # 如果tiktoken可用，应该更准确
        tokens = caller.estimate_tokens("Hello, how are you?")
        assert tokens > 0
    
    def test_is_configured(self):
        """测试配置检查"""
        caller = OpenAICaller(api_key="test-key")
        assert caller.is_configured() is True
        
        caller_no_key = OpenAICaller(api_key="")
        assert caller_no_key.is_configured() is False


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
