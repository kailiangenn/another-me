"""
HistoryManager 单元测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接导入避免依赖问题
sys.path.insert(0, str(project_root / "ame" / "foundation" / "llm" / "core"))
from history_manager import HistoryManager, CompressionStrategy


def create_test_messages(n: int) -> list:
    """创建测试消息"""
    messages = []
    for i in range(n):
        if i % 2 == 0:
            messages.append({"role": "user", "content": f"用户消息{i}" * 10})  # 较长
        else:
            messages.append({"role": "assistant", "content": f"助手回复{i}" * 10})
    return messages


def test_token_estimation():
    """测试Token估算"""
    print("\n" + "="*60)
    print("测试: Token估算")
    print("="*60)
    
    manager = HistoryManager(max_tokens=1000)
    
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好!有什么可以帮您?"},
        {"role": "user", "content": "今天天气怎么样?"}
    ]
    
    tokens = manager.estimate_tokens(messages)
    
    print(f"消息数: {len(messages)}")
    print(f"估算token数: {tokens}")
    
    assert tokens > 0, "Token估算失败"
    assert tokens < 200, "Token估算值异常"  # 简单对话不应超过200
    
    print("✓ Token估算测试通过")


def test_truncate_strategy():
    """测试截断策略"""
    print("\n" + "="*60)
    print("测试: 截断策略")
    print("="*60)
    
    manager = HistoryManager(max_tokens=500)
    
    # 创建20条消息
    messages = create_test_messages(20)
    
    # 截断
    result = manager.manage(messages, strategy=CompressionStrategy.TRUNCATE)
    
    result_tokens = manager.estimate_tokens(result)
    
    print(f"原始消息数: {len(messages)}")
    print(f"截断后消息数: {len(result)}")
    print(f"原始tokens: {manager.estimate_tokens(messages)}")
    print(f"截断后tokens: {result_tokens}")
    
    assert len(result) < len(messages), "未进行截断"
    assert result_tokens <= manager.max_tokens, "截断后仍超过限制"
    
    # 验证保留的是最近的消息
    assert result[-1] == messages[-1], "未保留最新消息"
    
    print("✓ 截断策略测试通过")


def test_keep_system_messages():
    """测试保留系统消息"""
    print("\n" + "="*60)
    print("测试: 保留系统消息")
    print("="*60)
    
    manager = HistoryManager(max_tokens=300)
    
    messages = [
        {"role": "system", "content": "你是一个智能助手" * 10},
        *create_test_messages(15)
    ]
    
    # 保留系统消息
    result = manager.manage(messages, strategy=CompressionStrategy.TRUNCATE, keep_system=True)
    
    print(f"原始消息数: {len(messages)}")
    print(f"处理后消息数: {len(result)}")
    
    assert result[0]["role"] == "system", "系统消息未保留"
    assert len(result) < len(messages), "未进行压缩"
    
    print("✓ 保留系统消息测试通过")


def test_sliding_window():
    """测试滑动窗口策略"""
    print("\n" + "="*60)
    print("测试: 滑动窗口策略")
    print("="*60)
    
    manager = HistoryManager(max_tokens=500)
    
    messages = create_test_messages(20)
    
    result = manager.manage(messages, strategy=CompressionStrategy.SLIDING_WINDOW)
    
    print(f"原始消息数: {len(messages)}")
    print(f"滑动窗口后消息数: {len(result)}")
    print(f"第一条原始消息: {messages[0]}")
    print(f"第一条结果消息: {result[0] if result else None}")
    print(f"最后一条原始消息: {messages[-1]}")
    print(f"最后一条结果消息: {result[-1] if result else None}")
    
    assert len(result) < len(messages), "未进行压缩"
    # 滑动窗口后可能超过限制被二次截断,所以只检查最后一条
    assert result[-1] == messages[-1], "未保留结尾消息"
    
    print("✓ 滑动窗口测试通过")


def test_importance_based():
    """测试基于重要性的策略"""
    print("\n" + "="*60)
    print("测试: 基于重要性的策略")
    print("="*60)
    
    manager = HistoryManager(max_tokens=500)
    
    messages = [
        {"role": "system", "content": "系统提示"},
        {"role": "user", "content": "重要问题" * 20},  # 长消息,高重要性
        {"role": "assistant", "content": "回复"},
        {"role": "user", "content": "hi"},
        *create_test_messages(10)
    ]
    
    result = manager.manage(messages, strategy=CompressionStrategy.IMPORTANCE)
    
    print(f"原始消息数: {len(messages)}")
    print(f"重要性筛选后消息数: {len(result)}")
    
    # 验证系统消息被保留
    system_msgs = [m for m in result if m["role"] == "system"]
    assert len(system_msgs) > 0, "系统消息未保留"
    
    # 验证重要的长消息被保留
    important_msg = [m for m in result if "重要问题" in m.get("content", "")]
    assert len(important_msg) > 0, "重要消息未保留"
    
    print("✓ 基于重要性的策略测试通过")


def test_no_compression_needed():
    """测试无需压缩的情况"""
    print("\n" + "="*60)
    print("测试: 无需压缩的情况")
    print("="*60)
    
    manager = HistoryManager(max_tokens=10000)  # 很大的限制
    
    messages = create_test_messages(5)
    
    result = manager.manage(messages)
    
    print(f"消息数: {len(messages)}")
    print(f"处理后消息数: {len(result)}")
    
    assert len(result) == len(messages), "不应该压缩"
    assert result == messages, "消息内容应该完全相同"
    
    print("✓ 无需压缩测试通过")


def test_custom_token_estimator():
    """测试自定义Token估算器"""
    print("\n" + "="*60)
    print("测试: 自定义Token估算器")
    print("="*60)
    
    def custom_estimator(text: str) -> int:
        """每10个字符=1 token"""
        return max(1, len(text) // 10)
    
    manager = HistoryManager(max_tokens=100, token_estimator=custom_estimator)
    
    messages = create_test_messages(10)
    
    tokens = manager.estimate_tokens(messages)
    
    print(f"使用自定义估算器,token数: {tokens}")
    
    # 更新估算器
    manager.set_token_estimator(lambda text: len(text))  # 每字符=1 token
    
    new_tokens = manager.estimate_tokens(messages)
    
    print(f"更新估算器后,token数: {new_tokens}")
    
    assert tokens != new_tokens, "估算器未生效"
    
    print("✓ 自定义Token估算器测试通过")


def test_set_max_tokens():
    """测试动态修改最大token数"""
    print("\n" + "="*60)
    print("测试: 动态修改最大token数")
    print("="*60)
    
    manager = HistoryManager(max_tokens=300)
    
    messages = create_test_messages(20)
    
    result1 = manager.manage(messages)
    len1 = len(result1)
    
    # 增加限制
    manager.set_max_tokens(800)
    result2 = manager.manage(messages)
    len2 = len(result2)
    
    print(f"max_tokens=300时: {len1}条消息")
    print(f"max_tokens=800时: {len2}条消息")
    
    assert len2 > len1, "增加限制后应保留更多消息"
    
    print("✓ 动态修改max_tokens测试通过")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*60)
    print("测试: 边界情况")
    print("="*60)
    
    manager = HistoryManager(max_tokens=100)
    
    # 1. 空消息列表
    result1 = manager.manage([])
    print(f"空列表结果: {result1}")
    assert result1 == [], "空列表应返回空列表"
    
    # 2. 单条消息
    result2 = manager.manage([{"role": "user", "content": "hi"}])
    print(f"单条消息结果: {len(result2)}条")
    assert len(result2) == 1, "单条消息应保留"
    
    # 3. 极长单条消息
    long_msg = [{"role": "user", "content": "x" * 10000}]
    result3 = manager.manage(long_msg)
    print(f"极长消息结果: {len(result3)}条")
    # 即使超限也应保留至少最近1条
    assert len(result3) >= 1, "应至少保留最近1条消息"
    
    print("✓ 边界情况测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始 HistoryManager 完整测试")
    print("="*60)
    
    tests = [
        test_token_estimation,
        test_truncate_strategy,
        test_keep_system_messages,
        test_sliding_window,
        test_importance_based,
        test_no_compression_needed,
        test_custom_token_estimator,
        test_set_max_tokens,
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
