"""
管道集成测试

测试SessionPipe和DocumentPipe的功能。
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ame.foundation.llm.atomic import OpenAICaller, LLMResponse
from ame.foundation.llm.pipeline import SessionPipe, DocumentPipe, PipelineContext


class TestSessionPipe:
    """SessionPipe集成测试"""
    
    @pytest.fixture
    def mock_caller(self):
        """创建mock调用器"""
        caller = OpenAICaller(api_key="test-key")
        
        # Mock响应
        mock_response = LLMResponse(
            content="Test response",
            model="gpt-3.5-turbo",
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        )
        
        caller._client.chat.completions.create = AsyncMock(return_value=Mock(
            choices=[Mock(message=Mock(content="Test response"), finish_reason="stop")],
            model="gpt-3.5-turbo",
            id="test-id",
            created=1234567890,
            usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        ))
        
        return caller
    
    @pytest.mark.asyncio
    async def test_basic_process(self, mock_caller):
        """测试基本处理流程"""
        pipe = SessionPipe(mock_caller)
        
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        
        context = PipelineContext(messages=messages)
        result = await pipe.process(context)
        
        assert result is not None
        assert result.response is not None
        assert result.response.content == "Test response"
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, mock_caller):
        """测试缓存命中"""
        pipe = SessionPipe(mock_caller, cache_enabled=True)
        
        messages = [
            {"role": "user", "content": "Hello"},
        ]
        
        context = PipelineContext(messages=messages)
        
        # 第一次调用
        result1 = await pipe.process(context)
        assert not result1.cached
        
        # 第二次调用（应该命中缓存）
        result2 = await pipe.process(context)
        assert result2.cached
        assert result2.response.content == result1.response.content
    
    @pytest.mark.asyncio
    async def test_compression_trigger(self, mock_caller):
        """测试压缩触发"""
        pipe = SessionPipe(
            mock_caller,
            compress_threshold=0.5,  # 降低阈值以便触发
            keep_recent=1
        )
        
        # 创建大量消息
        messages = []
        for i in range(20):
            messages.append({
                "role": "user",
                "content": f"Message {i} " * 100
            })
            messages.append({
                "role": "assistant",
                "content": f"Response {i} " * 100
            })
        
        context = PipelineContext(messages=messages, max_tokens=1000)
        result = await pipe.process(context)
        
        # 应该触发压缩
        assert result.compressed
        assert result.compression_info is not None
        assert result.compression_info["removed_count"] > 0
    
    def test_cache_stats(self, mock_caller):
        """测试缓存统计"""
        pipe = SessionPipe(mock_caller, cache_enabled=True)
        
        stats = pipe.get_cache_stats()
        assert stats["enabled"] is True
        assert stats["size"] == 0
        assert stats["max_size"] == 1000


class TestDocumentPipe:
    """DocumentPipe集成测试"""
    
    @pytest.fixture
    def mock_caller(self):
        """创建mock调用器"""
        caller = OpenAICaller(api_key="test-key")
        
        caller._client.chat.completions.create = AsyncMock(return_value=Mock(
            choices=[Mock(message=Mock(content="Analysis result"), finish_reason="stop")],
            model="gpt-3.5-turbo",
            id="test-id",
            created=1234567890,
            usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        ))
        
        return caller
    
    @pytest.mark.asyncio
    async def test_basic_process(self, mock_caller):
        """测试基本处理流程"""
        pipe = DocumentPipe(mock_caller)
        
        messages = [
            {"role": "system", "content": "You are a document analyzer."},
            {"role": "user", "content": "Analyze this document..."},
        ]
        
        context = PipelineContext(messages=messages)
        result = await pipe.process(context)
        
        assert result is not None
        assert result.response is not None
        assert result.response.content == "Analysis result"
        assert not result.cached  # DocumentPipe不使用缓存
    
    @pytest.mark.asyncio
    async def test_aggressive_compression(self, mock_caller):
        """测试激进压缩"""
        pipe = DocumentPipe(
            mock_caller,
            compress_threshold=0.5  # 降低阈值以便触发
        )
        
        # 创建多轮分析历史
        messages = [
            {"role": "system", "content": "You are a document analyzer."},
        ]
        
        for i in range(10):
            messages.append({
                "role": "user",
                "content": f"Document chunk {i} " * 200
            })
            messages.append({
                "role": "assistant",
                "content": f"Analysis {i} " * 200
            })
        
        context = PipelineContext(messages=messages, max_tokens=1000)
        result = await pipe.process(context)
        
        # 应该触发压缩
        assert result.compressed
        assert result.compression_info is not None
        # 激进压缩应该移除更多内容
        assert result.compression_info["compression_ratio"] > 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
