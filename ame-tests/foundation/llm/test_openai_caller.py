"""
OpenAICaller 单元测试

测试原子能力层的OpenAI调用器实现。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ame.foundation.llm.atomic import OpenAICaller, LLMResponse


class TestOpenAICaller:
    """OpenAICaller单元测试"""
    
    def test_init_without_api_key(self):
        """测试无API密钥初始化"""
        caller = OpenAICaller(api_key="")
        assert not caller.is_configured()
    
    def test_init_with_api_key(self):
        """测试带API密钥初始化"""
        caller = OpenAICaller(api_key="test-key")
        assert caller.is_configured()
        assert caller.model == "gpt-3.5-turbo"
    
    def test_estimate_tokens_simple(self):
        """测试token估算（无tiktoken）"""
        with patch('ame.foundation.llm.atomic.openai_caller.TIKTOKEN_AVAILABLE', False):
            caller = OpenAICaller(api_key="test-key")
            
            # 测试英文
            tokens = caller.estimate_tokens("Hello world")
            assert tokens > 0
            
            # 测试中文
            tokens = caller.estimate_tokens("你好世界")
            assert tokens > 0
            
            # 测试空字符串
            tokens = caller.estimate_tokens("")
            assert tokens == 0
    
    @pytest.mark.asyncio
    async def test_generate_without_config(self):
        """测试未配置时调用generate"""
        caller = OpenAICaller(api_key="")
        
        with pytest.raises(RuntimeError, match="未正确配置"):
            await caller.generate([{"role": "user", "content": "test"}])
    
    @pytest.mark.asyncio
    async def test_generate_with_mock(self):
        """测试generate方法（使用mock）"""
        caller = OpenAICaller(api_key="test-key")
        
        # Mock响应
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.model = "gpt-3.5-turbo"
        mock_response.id = "test-id"
        mock_response.created = 1234567890
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        
        # Mock客户端
        caller._client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        # 调用generate
        response = await caller.generate([{"role": "user", "content": "test"}])
        
        assert isinstance(response, LLMResponse)
        assert response.content == "Test response"
        assert response.model == "gpt-3.5-turbo"
        assert response.total_tokens == 30
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 20
    
    @pytest.mark.asyncio
    async def test_generate_stream_without_config(self):
        """测试未配置时调用generate_stream"""
        caller = OpenAICaller(api_key="")
        
        with pytest.raises(RuntimeError, match="未正确配置"):
            async for _ in caller.generate_stream([{"role": "user", "content": "test"}]):
                pass
    
    @pytest.mark.asyncio
    async def test_generate_stream_with_mock(self):
        """测试generate_stream方法（使用mock）"""
        caller = OpenAICaller(api_key="test-key")
        
        # Mock流式响应
        async def mock_stream():
            chunks = ["Hello", " ", "world", "!"]
            for chunk in chunks:
                mock_chunk = Mock()
                mock_chunk.choices = [Mock()]
                mock_chunk.choices[0].delta.content = chunk
                yield mock_chunk
        
        caller._client.chat.completions.create = AsyncMock(return_value=mock_stream())
        
        # 调用generate_stream
        full_text = ""
        async for chunk in caller.generate_stream([{"role": "user", "content": "test"}]):
            full_text += chunk
        
        assert full_text == "Hello world!"
    
    def test_estimate_messages_tokens(self):
        """测试消息列表token估算"""
        caller = OpenAICaller(api_key="test-key")
        
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        
        tokens = caller.estimate_messages_tokens(messages)
        assert tokens > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
