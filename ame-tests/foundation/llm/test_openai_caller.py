"""
OpenAICaller 脚本化测试

需要真实的OpenAI API Key来运行测试
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ame import OpenAICaller, LLMResponse


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    else:
        print("-" * 80)


async def test_token_estimation(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试Token估算"""
    print_separator("测试Token估算")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    
    # 测试英文
    text_en = "Hello world, this is a test."
    tokens_en = caller.estimate_tokens(text_en)
    print(f"\n英文文本: {text_en}")
    print(f"估算Token数: {tokens_en}")
    
    # 测试中文
    text_cn = "你好世界，这是一个测试。"
    tokens_cn = caller.estimate_tokens(text_cn)
    print(f"\n中文文本: {text_cn}")
    print(f"估算Token数: {tokens_cn}")
    
    # 测试混合
    text_mix = "Hello 你好 world 世界"
    tokens_mix = caller.estimate_tokens(text_mix)
    print(f"\n混合文本: {text_mix}")
    print(f"估算Token数: {tokens_mix}")
    
    # 测试消息列表
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    total_tokens = caller.estimate_messages_tokens(messages)
    print(f"\n消息列表:")
    for msg in messages:
        print(f"  [{msg['role']}] {msg['content']}")
    print(f"总Token估算: {total_tokens}")
    
    print("\n✅ Token估算测试完成")


async def test_basic_generate(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试基本生成"""
    print_separator("测试基本生成（Complete模式）")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    
    print(f"\n配置状态: {'已配置' if caller.is_configured() else '未配置'}")
    print(f"使用模型: {caller.model}")
    
    messages = [
        {"role": "user", "content": "用一句话介绍Python编程语言"}
    ]
    
    print(f"\n发送消息: {messages[0]['content']}")
    print("\n等待响应...")
    
    response = await caller.generate(
        messages=messages,
        temperature=0.7,
        max_tokens=100
    )
    
    print(f"\n📝 响应内容:")
    print(f"   {response.content}")
    print(f"\n📊 使用统计:")
    print(f"   模型: {response.model}")
    print(f"   提示Token: {response.prompt_tokens}")
    print(f"   生成Token: {response.completion_tokens}")
    print(f"   总Token: {response.total_tokens}")
    print(f"   完成原因: {response.finish_reason}")
    
    print("\n✅ 基本生成测试完成")


async def test_stream_generate(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试流式生成"""
    print_separator("测试流式生成（Stream模式）")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    
    messages = [
        {"role": "user", "content": "用三句话介绍人工智能的发展历程"}
    ]
    
    print(f"\n发送消息: {messages[0]['content']}")
    print("\n📝 流式响应:")
    print("   ", end="", flush=True)
    
    full_response = ""
    async for chunk in caller.generate_stream(
        messages=messages,
        temperature=0.7,
        max_tokens=200
    ):
        print(chunk, end="", flush=True)
        full_response += chunk
    
    print("\n")
    print(f"\n完整响应长度: {len(full_response)} 字符")
    print(f"估算Token数: {caller.estimate_tokens(full_response)}")
    
    print("\n✅ 流式生成测试完成")


async def test_multi_turn_conversation(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试多轮对话"""
    print_separator("测试多轮对话")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    
    messages = [
        {"role": "system", "content": "你是一个友好的助手。"},
        {"role": "user", "content": "你好，我想学习编程"},
    ]
    
    print("\n💬 对话开始")
    
    # 第一轮
    print(f"\n👤 用户: {messages[-1]['content']}")
    response1 = await caller.generate(messages, temperature=0.7, max_tokens=100)
    print(f"🤖 助手: {response1.content}")
    
    messages.append({"role": "assistant", "content": response1.content})
    messages.append({"role": "user", "content": "推荐一个适合初学者的语言"})
    
    # 第二轮
    print(f"\n👤 用户: {messages[-1]['content']}")
    response2 = await caller.generate(messages, temperature=0.7, max_tokens=100)
    print(f"🤖 助手: {response2.content}")
    
    print(f"\n📊 对话统计:")
    print(f"   总轮次: 2")
    print(f"   总消息数: {len(messages) + 1}")
    total_tokens = caller.estimate_messages_tokens(messages) + response2.completion_tokens
    print(f"   估算总Token: {total_tokens}")
    
    print("\n✅ 多轮对话测试完成")


async def main():
    """主测试流程"""
    print_separator("OpenAICaller 脚本化测试")
    
    # 获取API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n请输入OpenAI API Key:")
        api_key = input("> ").strip()
    
    if not api_key:
        print("\n❌ 错误: 未提供API Key")
        return
    
    # 获取Base URL（可选）
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        print("\n请输入Base URL (直接回车使用默认):")
        base_url_input = input("> ").strip()
        base_url = base_url_input if base_url_input else None
    
    # 获取模型名称
    model_name = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    print(f"\n请输入模型名称 (直接回车使用默认: {model_name}):")
    model_input = input("> ").strip()
    if model_input:
        model_name = model_input
    
    print(f"\n✅ 配置信息:")
    print(f"   API Key: {api_key[:8]}...")
    print(f"   Base URL: {base_url or '默认'}")
    print(f"   Model: {model_name}")
    
    try:
        # 执行测试
        await test_token_estimation(api_key, base_url, model_name)
        await test_basic_generate(api_key, base_url, model_name)
        await test_stream_generate(api_key, base_url, model_name)
        await test_multi_turn_conversation(api_key, base_url, model_name)
        
        print_separator("所有测试完成")
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
