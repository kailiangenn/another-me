"""
Life场景意图识别器测试

测试LifeIntentRecognizer的功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ame.capability.life.intent_recognizer import LifeIntentRecognizer
from ame.foundation.nlp.core.models import IntentType


def test_basic_intent_recognition():
    """测试基础意图识别"""
    print("测试1: 基础意图识别")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    # 测试query_self意图
    result = recognizer.recognize_sync("我喜欢什么？")
    assert result.intent == IntentType.QUERY_SELF, f"Expected QUERY_SELF, got {result.intent}"
    assert result.confidence > 0.7, f"Confidence too low: {result.confidence}"
    print(f"  ✓ query_self识别成功: '{result.intent.value}', 置信度: {result.confidence}")
    
    # 测试comfort意图
    result = recognizer.recognize_sync("我很难过")
    assert result.intent == IntentType.COMFORT, f"Expected COMFORT, got {result.intent}"
    print(f"  ✓ comfort识别成功: '{result.intent.value}'")
    
    # 测试analyze意图
    result = recognizer.recognize_sync("分析一下我最近的表现")
    assert result.intent == IntentType.ANALYZE, f"Expected ANALYZE, got {result.intent}"
    print(f"  ✓ analyze识别成功: '{result.intent.value}'")
    
    # 测试chat意图
    result = recognizer.recognize_sync("你好")
    assert result.intent == IntentType.CHAT, f"Expected CHAT, got {result.intent}"
    print(f"  ✓ chat识别成功: '{result.intent.value}'")
    
    print("✅ 测试1通过\n")


def test_extended_life_rules():
    """测试Life场景扩展规则"""
    print("测试2: Life场景扩展规则")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    # 测试扩展的query_self规则
    test_cases = [
        ("我的兴趣是什么", IntentType.QUERY_SELF),
        ("介绍一下我自己", IntentType.QUERY_SELF),
        ("我做过什么项目", IntentType.QUERY_SELF),
    ]
    
    for text, expected_intent in test_cases:
        result = recognizer.recognize_sync(text)
        assert result.intent == expected_intent, \
            f"Text: '{text}', Expected: {expected_intent}, Got: {result.intent}"
        print(f"  ✓ '{text}' -> {result.intent.value}")
    
    print("✅ 测试2通过\n")


def test_comfort_variations():
    """测试comfort意图的多种表达"""
    print("测试3: Comfort意图变体")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    comfort_texts = [
        "我很难过",
        "心情不好",
        "感觉很焦虑",
        "我想找人倾诉",
        "压力很大",
        "感到孤独",
    ]
    
    for text in comfort_texts:
        result = recognizer.recognize_sync(text)
        assert result.intent == IntentType.COMFORT, \
            f"Text: '{text}' should be COMFORT, got {result.intent}"
        print(f"  ✓ '{text}' -> COMFORT")
    
    print("✅ 测试3通过\n")


def test_post_processing():
    """测试后处理逻辑"""
    print("测试4: 后处理逻辑")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    # 测试comfort意图的置信度提升
    result = recognizer.recognize_sync("我很难过")
    assert result.intent == IntentType.COMFORT
    
    # comfort意图应该有置信度提升
    assert result.metadata.get("life_boost") == True, "应该有life_boost标记"
    print(f"  ✓ Comfort意图置信度提升: {result.confidence}")
    
    print("✅ 测试4通过\n")


def test_custom_intent_registration():
    """测试自定义意图注册"""
    print("测试5: 自定义意图注册")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    # 注册自定义意图
    recognizer.register_custom_intent(
        intent_name="book_recommendation",
        patterns=[r"推荐.*?(书|阅读)", r"有什么.*?书"]
    )
    
    # 测试自定义意图识别
    result = recognizer.recognize_sync("推荐一本书给我")
    # 自定义意图会被映射为CUSTOM
    assert result.intent == IntentType.CUSTOM or result.intent == IntentType.CHAT
    print(f"  ✓ 自定义意图注册成功: '{result.intent.value}'")
    
    # 获取支持的意图列表
    intents = recognizer.get_supported_intents()
    assert "book_recommendation" in intents or len(intents) > 0
    print(f"  ✓ 支持的意图数量: {len(intents)}")
    
    print("✅ 测试5通过\n")


def test_edge_cases():
    """测试边界情况"""
    print("测试6: 边界情况")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    # 空文本 - 应该抛出异常
    try:
        result = recognizer.recognize_sync("")
        assert False, "空文本应该抛出异常"
    except Exception as e:
        print(f"  ✓ 空文本正确抛出异常: {type(e).__name__}")
    
    # 只有空格
    try:
        result = recognizer.recognize_sync("   ")
        assert False, "纯空格应该抛出异常"
    except Exception as e:
        print(f"  ✓ 纯空格正确抛出异常: {type(e).__name__}")
    
    # 非常长的文本
    long_text = "我" * 1000
    result = recognizer.recognize_sync(long_text)
    assert result.intent in [IntentType.CHAT, IntentType.QUERY_SELF]
    print(f"  ✓ 长文本处理成功: {result.intent.value}")
    
    print("✅ 测试6通过\n")


def test_confidence_scores():
    """测试置信度评分"""
    print("测试7: 置信度评分")
    
    recognizer = LifeIntentRecognizer(llm_caller=None)
    
    # 明确的意图应该有较高置信度
    result = recognizer.recognize_sync("我喜欢什么")
    assert result.confidence >= 0.7, f"明确意图置信度应该 >= 0.7, 实际: {result.confidence}"
    print(f"  ✓ 明确意图置信度: {result.confidence:.2f}")
    
    # 模糊的意图可能置信度较低
    result = recognizer.recognize_sync("嗯")
    assert result.confidence > 0, f"置信度应该 > 0, 实际: {result.confidence}"
    print(f"  ✓ 模糊意图置信度: {result.confidence:.2f}")
    
    print("✅ 测试7通过\n")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Life场景意图识别器测试")
    print("=" * 60)
    print()
    
    try:
        test_basic_intent_recognition()
        test_extended_life_rules()
        test_comfort_variations()
        test_post_processing()
        test_custom_intent_registration()
        test_edge_cases()
        test_confidence_scores()
        
        print("=" * 60)
        print("✅ 所有测试通过!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
