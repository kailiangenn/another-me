"""
PromptBuilder 单元测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接导入避免依赖问题
sys.path.insert(0, str(project_root / "ame" / "foundation" / "llm" / "core"))
from prompt_builder import PromptBuilder, PromptTemplates


def test_basic_build():
    """测试基础提示词构建"""
    print("\n" + "="*60)
    print("测试: 基础提示词构建")
    print("="*60)
    
    builder = PromptBuilder()
    
    # 测试简单变量替换
    template = "请分析: ${content}"
    variables = {"content": "今天天气很好"}
    result = builder.build(template, variables)
    
    print(f"模板: {template}")
    print(f"变量: {variables}")
    print(f"结果: {result}")
    
    assert "今天天气很好" in result, "变量替换失败"
    assert "${content}" not in result, "模板未被替换"
    
    print("✓ 基础构建测试通过")


def test_build_with_context():
    """测试带上下文的构建"""
    print("\n" + "="*60)
    print("测试: 带上下文的构建")
    print("="*60)
    
    builder = PromptBuilder()
    
    template = "用户${user_name}说: ${message}"
    variables = {"message": "你好"}
    context = {"user_name": "张三"}
    
    result = builder.build(template, variables, context)
    
    print(f"模板: {template}")
    print(f"变量: {variables}")
    print(f"上下文: {context}")
    print(f"结果: {result}")
    
    assert "张三" in result, "上下文未嵌入"
    assert "你好" in result, "变量未替换"
    
    print("✓ 上下文构建测试通过")


def test_build_with_history():
    """测试带历史的构建"""
    print("\n" + "="*60)
    print("测试: 带历史的提示词构建")
    print("="*60)
    
    builder = PromptBuilder()
    
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好!有什么可以帮您?"},
        {"role": "user", "content": "今天天气怎么样?"}
    ]
    
    template = """对话历史:
${history}

请继续对话。"""
    
    result = builder.build_with_history(template, history)
    
    print(f"历史消息数: {len(history)}")
    print(f"结果:\n{result}")
    
    assert "User: 你好" in result, "历史未正确格式化"
    assert "Assistant:" in result, "角色名称转换失败"
    
    print("✓ 历史构建测试通过")


def test_build_few_shot():
    """测试Few-shot构建"""
    print("\n" + "="*60)
    print("测试: Few-shot提示词构建")
    print("="*60)
    
    builder = PromptBuilder()
    
    examples = [
        {"input": "今天天气很好", "output": "正面"},
        {"input": "我很难过", "output": "负面"},
        {"input": "这是一本书", "output": "中性"}
    ]
    
    result = builder.build_few_shot(
        task_description="情感分类任务",
        examples=examples,
        query="我很开心",
        instruction="请判断情感倾向"
    )
    
    print(f"示例数: {len(examples)}")
    print(f"结果:\n{result}")
    
    assert "示例1:" in result, "示例未添加"
    assert "示例2:" in result, "示例未添加"
    assert "示例3:" in result, "示例未添加"
    assert "我很开心" in result, "查询未添加"
    assert "情感分类任务" in result, "任务描述未添加"
    
    print("✓ Few-shot构建测试通过")


def test_build_with_system():
    """测试系统提示词构建"""
    print("\n" + "="*60)
    print("测试: 系统提示词构建")
    print("="*60)
    
    builder = PromptBuilder(default_system_prompt="你是一个智能助手")
    
    messages = builder.build_with_system("请帮我分析一下")
    
    print(f"消息数: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"消息{i+1}: role={msg['role']}, content={msg['content'][:30]}...")
    
    assert len(messages) == 2, "消息数量错误"
    assert messages[0]["role"] == "system", "系统消息角色错误"
    assert messages[1]["role"] == "user", "用户消息角色错误"
    assert "智能助手" in messages[0]["content"], "系统提示词未设置"
    
    print("✓ 系统提示词构建测试通过")


def test_build_messages_with_history():
    """测试完整消息列表构建"""
    print("\n" + "="*60)
    print("测试: 完整消息列表构建")
    print("="*60)
    
    builder = PromptBuilder()
    
    history = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好!"}
    ]
    
    messages = builder.build_messages_with_history(
        user_message="今天天气怎么样?",
        history=history,
        system_prompt="你是天气助手"
    )
    
    print(f"消息数: {len(messages)}")
    for i, msg in enumerate(messages):
        print(f"{i+1}. {msg['role']}: {msg['content'][:50]}")
    
    assert messages[0]["role"] == "system", "系统消息缺失"
    assert messages[1]["role"] == "user", "历史消息缺失"
    assert messages[2]["role"] == "assistant", "历史消息缺失"
    assert messages[3]["role"] == "user", "新消息缺失"
    assert "今天天气怎么样?" in messages[3]["content"], "新消息内容错误"
    
    print("✓ 完整消息列表构建测试通过")


def test_history_truncation():
    """测试历史截断"""
    print("\n" + "="*60)
    print("测试: 历史消息截断")
    print("="*60)
    
    builder = PromptBuilder()
    
    # 创建20条历史消息
    history = []
    for i in range(20):
        history.append({"role": "user", "content": f"消息{i}"})
        history.append({"role": "assistant", "content": f"回复{i}"})
    
    messages = builder.build_messages_with_history(
        user_message="新消息",
        history=history,
        max_history_messages=5  # 只保留5条
    )
    
    # 期望: 1条新消息 + 5条历史 = 6条(不含system)
    history_count = len([m for m in messages if m["role"] in ["user", "assistant"]]) - 1
    
    print(f"原始历史数: {len(history)}")
    print(f"截断后历史数: {history_count}")
    print(f"总消息数: {len(messages)}")
    
    assert history_count == 5, f"历史截断失败,期望5条,实际{history_count}条"
    
    print("✓ 历史截断测试通过")


def test_prompt_templates():
    """测试预定义模板"""
    print("\n" + "="*60)
    print("测试: 预定义模板")
    print("="*60)
    
    builder = PromptBuilder()
    
    # 测试情感分析模板
    result = builder.build(
        PromptTemplates.EMOTION_ANALYSIS,
        {"text": "今天心情很好"}
    )
    
    print(f"情感分析模板结果:\n{result[:200]}...")
    
    assert "今天心情很好" in result, "模板变量替换失败"
    assert "情绪类型" in result, "模板内容缺失"
    
    print("✓ 预定义模板测试通过")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*60)
    print("测试: 边界情况")
    print("="*60)
    
    builder = PromptBuilder()
    
    # 1. 空历史
    result1 = builder.build_with_history("${history}", [])
    print(f"空历史结果: {result1}")
    assert "(无历史对话)" in result1, "空历史处理失败"
    
    # 2. 缺失变量
    result2 = builder.build("${missing_var}", {})
    print(f"缺失变量结果: {result2}")
    assert "${missing_var}" in result2, "缺失变量应保持原样"
    
    # 3. 空示例
    result3 = builder.build_few_shot("任务", [], "查询")
    print(f"空示例结果:\n{result3}")
    assert "查询" in result3, "查询未添加"
    
    print("✓ 边界情况测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始 PromptBuilder 完整测试")
    print("="*60)
    
    tests = [
        test_basic_build,
        test_build_with_context,
        test_build_with_history,
        test_build_few_shot,
        test_build_with_system,
        test_build_messages_with_history,
        test_history_truncation,
        test_prompt_templates,
        test_edge_cases
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} 错误: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
