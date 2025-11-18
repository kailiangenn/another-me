"""
管道脚本化测试

测试SessionPipe和DocumentPipe的真实功能
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from ame import OpenAICaller, SessionPipe, DocumentPipe, PipelineContext


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    else:
        print("-" * 80)


async def test_session_basic(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试SessionPipe基本功能"""
    print_separator("测试SessionPipe基本功能")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    pipe = SessionPipe(caller, cache_enabled=True)
    
    messages = [
        {"role": "user", "content": "用一句话介绍机器学习"}
    ]
    
    print(f"\n发送消息: {messages[0]['content']}")
    
    context = PipelineContext(messages=messages, max_tokens=4000, temperature=0.7)
    result = await pipe.process(context)
    
    print(f"\n📝 响应内容:")
    print(f"   {result.response.content}")
    print(f"\n📊 管道信息:")
    print(f"   模式: {result.metadata.get('mode', 'unknown')}")
    print(f"   缓存: {'命中' if result.cached else '未命中'}")
    print(f"   压缩: {'是' if result.compressed else '否'}")
    print(f"   总Token: {result.response.total_tokens}")
    
    print("\n✅ SessionPipe基本功能测试完成")


async def test_session_cache(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试SessionPipe缓存功能"""
    print_separator("测试SessionPipe缓存功能")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    pipe = SessionPipe(caller, cache_enabled=True)
    
    messages = [
        {"role": "user", "content": "什么是深度学习？"}
    ]
    
    context = PipelineContext(messages=messages, max_tokens=4000, temperature=0.7)
    
    # 第一次调用
    print("\n第一次调用...")
    result1 = await pipe.process(context)
    print(f"响应: {result1.response.content[:50]}...")
    print(f"缓存状态: {'命中' if result1.cached else '未命中'}")
    
    # 第二次调用（应该命中缓存）
    print("\n第二次调用（相同输入）...")
    result2 = await pipe.process(context)
    print(f"响应: {result2.response.content[:50]}...")
    print(f"缓存状态: {'命中' if result2.cached else '未命中'}")
    
    # 缓存统计
    stats = pipe.get_cache_stats()
    print(f"\n📊 缓存统计:")
    print(f"   启用: {stats['enabled']}")
    print(f"   当前大小: {stats['size']}")
    print(f"   最大容量: {stats['max_size']}")
    
    print("\n✅ SessionPipe缓存功能测试完成")


async def test_session_compression(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试SessionPipe压缩功能"""
    print_separator("测试SessionPipe压缩功能")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    pipe = SessionPipe(
        caller,
        compress_threshold=0.5,  # 降低阈值以便触发
        keep_recent=1
    )
    
    # 创建长对话历史
    messages = [
        {"role": "system", "content": "你是一个助手"}
    ]
    
    for i in range(5):
        messages.append({
            "role": "user",
            "content": f"这是第{i+1}个问题：请详细介绍人工智能的第{i+1}个应用场景。" * 10
        })
        messages.append({
            "role": "assistant",
            "content": f"关于第{i+1}个应用场景的详细说明..." * 20
        })
    
    messages.append({"role": "user", "content": "总结一下前面的内容"})
    
    print(f"\n总消息数: {len(messages)}")
    print(f"估算Token数: {caller.estimate_messages_tokens(messages)}")
    
    context = PipelineContext(messages=messages, max_tokens=1000, temperature=0.7)
    result = await pipe.process(context)
    
    print(f"\n📝 响应: {result.response.content[:100]}...")
    print(f"\n📊 压缩信息:")
    print(f"   是否压缩: {result.compressed}")
    if result.compressed and result.compression_info:
        print(f"   压缩前Token: {result.compression_info.get('tokens_before', 0)}")
        print(f"   压缩后Token: {result.compression_info.get('tokens_after', 0)}")
        print(f"   压缩比: {result.compression_info.get('compression_ratio', 0):.2%}")
        print(f"   移除消息数: {result.compression_info.get('removed_count', 0)}")
    
    print("\n✅ SessionPipe压缩功能测试完成")


async def test_document_basic(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试DocumentPipe基本功能"""
    print_separator("测试DocumentPipe基本功能")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    pipe = DocumentPipe(caller)
    
    messages = [
        {"role": "system", "content": "你是一个文档分析助手"},
        {"role": "user", "content": "分析这篇文档的主题：人工智能正在改变世界，深度学习是其核心技术之一。"}
    ]
    
    print(f"\n发送消息: {messages[1]['content']}")
    
    context = PipelineContext(messages=messages, max_tokens=4000, temperature=0.7)
    result = await pipe.process(context)
    
    print(f"\n📝 分析结果:")
    print(f"   {result.response.content}")
    print(f"\n📊 管道信息:")
    print(f"   模式: {result.metadata.get('mode', 'unknown')}")
    print(f"   管道类型: {result.metadata.get('pipeline', 'unknown')}")
    print(f"   缓存: {'命中' if result.cached else '未命中'}")
    print(f"   压缩: {'是' if result.compressed else '否'}")
    
    print("\n✅ DocumentPipe基本功能测试完成")


async def test_document_compression(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试DocumentPipe激进压缩"""
    print_separator("测试DocumentPipe激进压缩")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    pipe = DocumentPipe(caller, compress_threshold=0.5)
    
    # 创建多轮分析历史
    messages = [
        {"role": "system", "content": "你是一个文档分析助手"}
    ]
    
    for i in range(5):
        messages.append({
            "role": "user",
            "content": f"分析文档片段{i+1}：" + "这是一段很长的文档内容，包含了大量的技术细节和说明。" * 30
        })
        messages.append({
            "role": "assistant",
            "content": f"对片段{i+1}的分析结果..." * 40
        })
    
    messages.append({"role": "user", "content": "请总结所有片段"})
    
    print(f"\n总消息数: {len(messages)}")
    print(f"估算Token数: {caller.estimate_messages_tokens(messages)}")
    
    context = PipelineContext(messages=messages, max_tokens=1000, temperature=0.7)
    result = await pipe.process(context)
    
    print(f"\n📝 响应: {result.response.content[:100]}...")
    print(f"\n📊 压缩信息:")
    print(f"   是否压缩: {result.compressed}")
    if result.compressed and result.compression_info:
        print(f"   压缩前Token: {result.compression_info.get('tokens_before', 0)}")
        print(f"   压缩后Token: {result.compression_info.get('tokens_after', 0)}")
        print(f"   压缩比: {result.compression_info.get('compression_ratio', 0):.2%}")
        print(f"   移除消息数: {result.compression_info.get('removed_count', 0)}")
    
    print("\n✅ DocumentPipe激进压缩测试完成")


async def test_session_export(api_key: str, base_url: str = None, model_name: str = "gpt-3.5-turbo"):
    """测试会话导出功能"""
    print_separator("测试会话导出功能")
    
    caller = OpenAICaller(api_key=api_key, model=model_name, base_url=base_url)
    pipe = SessionPipe(caller)
    
    # 进行几轮对话
    messages = [
        {"role": "user", "content": "你好"}
    ]
    
    context = PipelineContext(messages=messages)
    result1 = await pipe.process(context)
    
    messages.append({"role": "assistant", "content": result1.response.content})
    messages.append({"role": "user", "content": "介绍一下AI"})
    
    context = PipelineContext(messages=messages)
    result2 = await pipe.process(context)
    
    # 导出会话
    session_data = pipe.export_session()
    
    print(f"\n📦 导出数据:")
    print(f"   类型: {session_data.get('type')}")
    print(f"   消息数: {session_data['history']['total_messages']}")
    print(f"   压缩事件: {len(session_data['history']['compression_events'])}")
    print(f"   导出时间: {session_data.get('exported_at')}")
    
    print("\n✅ 会话导出功能测试完成")


async def main():
    """主测试流程"""
    print_separator("管道脚本化测试")
    
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
        await test_session_basic(api_key, base_url, model_name)
        await test_session_cache(api_key, base_url, model_name)
        await test_session_compression(api_key, base_url, model_name)
        await test_document_basic(api_key, base_url, model_name)
        await test_document_compression(api_key, base_url, model_name)
        await test_session_export(api_key, base_url, model_name)
        
        print_separator("所有测试完成")
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
