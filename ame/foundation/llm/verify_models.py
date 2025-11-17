#!/usr/bin/env python3
"""
数据模型验证脚本

验证models.py中的所有数据类和函数是否正常工作。
"""

import sys
import os

# 直接导入models模块，避免触发其他依赖
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 单独加载models模块
import importlib.util
spec = importlib.util.spec_from_file_location(
    "models", 
    os.path.join(os.path.dirname(__file__), "models.py")
)
models = importlib.util.module_from_spec(spec)
spec.loader.exec_module(models)

print("=" * 60)
print("数据模型验证")
print("=" * 60)

# 测试枚举
print("\n1. 测试枚举类型:")
print(f"   CallMode.STREAM = {models.CallMode.STREAM.value}")
print(f"   CallMode.COMPLETE = {models.CallMode.COMPLETE.value}")
print(f"   CallMode.BATCH = {models.CallMode.BATCH.value}")
print("   ✅ 枚举类型正常")

# 测试LLMResponse
print("\n2. 测试LLMResponse:")
response = models.LLMResponse(
    content="Test response",
    model="gpt-3.5-turbo",
    usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
)
print(f"   content: {response.content}")
print(f"   model: {response.model}")
print(f"   total_tokens: {response.total_tokens}")
print(f"   prompt_tokens: {response.prompt_tokens}")
print(f"   completion_tokens: {response.completion_tokens}")
print("   ✅ LLMResponse正常")

# 测试CompressContext
print("\n3. 测试CompressContext:")
def token_estimator(text: str) -> int:
    return len(text) // 4

messages = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
context = models.CompressContext(
    messages=messages,
    max_tokens=1000,
    token_estimator=token_estimator,
    current_tokens=100
)
print(f"   messages: {len(context.messages)}")
print(f"   max_tokens: {context.max_tokens}")
print(f"   current_tokens: {context.current_tokens}")
msg_tokens = context.estimate_message_tokens(messages[0])
print(f"   estimate_message_tokens: {msg_tokens}")
print("   ✅ CompressContext正常")

# 测试CompressResult
print("\n4. 测试CompressResult:")
result = models.CompressResult(
    kept_messages=messages[:1],
    removed_messages=messages[1:],
    tokens_before=100,
    tokens_after=50,
    compression_ratio=0.5
)
print(f"   kept: {len(result.kept_messages)}")
print(f"   removed: {len(result.removed_messages)}")
print(f"   saved_tokens: {result.saved_tokens}")
print(f"   compression_ratio: {result.compression_ratio}")
print(f"   str: {result}")
print("   ✅ CompressResult正常")

# 测试PipelineContext
print("\n5. 测试PipelineContext:")
pipe_context = models.PipelineContext(
    messages=messages,
    max_tokens=4000,
    temperature=0.7,
    stream=False
)
print(f"   messages: {len(pipe_context.messages)}")
print(f"   max_tokens: {pipe_context.max_tokens}")
print(f"   temperature: {pipe_context.temperature}")
print(f"   stream: {pipe_context.stream}")
print("   ✅ PipelineContext正常")

# 测试PipelineResult
print("\n6. 测试PipelineResult:")
pipe_result = models.PipelineResult(
    response=response,
    cached=True,
    compressed=False
)
print(f"   is_stream: {pipe_result.is_stream}")
print(f"   cached: {pipe_result.cached}")
print(f"   compressed: {pipe_result.compressed}")
print(f"   str: {pipe_result}")
print("   ✅ PipelineResult正常")

# 测试辅助函数
print("\n7. 测试辅助函数:")
user_msg = models.create_user_message("Hello", important=True)
assistant_msg = models.create_assistant_message("Hi!")
system_msg = models.create_system_message("You are helpful.")

print(f"   user_message: {user_msg}")
print(f"   assistant_message: {assistant_msg}")
print(f"   system_message: {system_msg}")
print("   ✅ 辅助函数正常")

print("\n" + "=" * 60)
print("✅ 所有数据模型验证通过！")
print("=" * 60)
