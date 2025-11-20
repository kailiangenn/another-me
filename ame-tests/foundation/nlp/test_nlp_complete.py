"""
NLP模块完整测试 - 测试意图识别、实体提取、情感分析、摘要生成

测试覆盖:
1. IntentRecognizer - 规则匹配、LLM增强、自定义意图
2. EntityExtractor - jieba提取、LLM增强、自定义词典
3. EmotionAnalyzer - 词典分析、LLM增强
4. Summarizer - 多种摘要策略、对话摘要
"""

import os
import sys
import asyncio
from typing import List, Dict

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../ame"))

from foundation.nlp.atomic.intent_recognizer import IntentRecognizer
from foundation.nlp.atomic.entity_extractor import EntityExtractor
from foundation.nlp.atomic.emotion_analyzer import EmotionAnalyzer
from foundation.nlp.atomic.summarizer import Summarizer, SummaryStrategy
from foundation.nlp.core import (
    IntentType,
    EntityType,
    EmotionType,
    IntentResult,
    Entity,
    EmotionResult,
    Summary,
)


# ============== Mock LLM Caller for Tests ==============

class MockLLMCaller:
    """模拟LLM调用器，用于不依赖真实API的测试"""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate(self, messages: List[Dict], **kwargs):
        """模拟生成响应"""
        self.call_count += 1
        
        # 根据提示词返回不同的模拟响应
        user_content = messages[-1]["content"] if messages else ""
        
        # 意图识别响应
        if "意图类型" in user_content:
            if "难过" in user_content or "伤心" in user_content:
                return type('Response', (), {'content': 'comfort'})()
            elif "我喜欢" in user_content:
                return type('Response', (), {'content': 'query_self'})()
            elif "分析" in user_content:
                return type('Response', (), {'content': 'analyze'})()
            return type('Response', (), {'content': 'chat'})()
        
        # 实体提取响应
        if "提取命名实体" in user_content:
            return type('Response', (), {'content': '''```json
[
  {"text": "张三", "type": "person"},
  {"text": "北京", "type": "location"},
  {"text": "人工智能", "type": "concept"}
]
```'''})()
        
        # 情感分析响应
        if "情感倾向" in user_content:
            if "开心" in user_content:
                return type('Response', (), {'content': '''```json
{"emotion": "joy", "intensity": 0.85, "valence": 0.85}
```'''})()
            elif "难过" in user_content:
                return type('Response', (), {'content': '''```json
{"emotion": "sadness", "intensity": 0.75, "valence": -0.75}
```'''})()
            return type('Response', (), {'content': '''```json
{"emotion": "neutral", "intensity": 0.5, "valence": 0.0}
```'''})()
        
        # 摘要生成响应
        if "生成摘要" in user_content or "总结以下对话" in user_content or "基于以下关键信息" in user_content:
            return type('Response', (), {'content': '''```json
{
  "summary": "这是一段关于AI技术讨论的摘要",
  "key_points": ["讨论了人工智能", "提到了机器学习", "探讨了未来趋势"],
  "topics": ["人工智能", "机器学习"]
}
```'''})() 
        
        return type('Response', (), {'content': 'mock response'})()
        
        return type('Response', (), {'content': 'mock response'})()


# ============== 测试函数 ==============

def test_intent_recognizer_rule_matching():
    """测试意图识别器 - 规则匹配"""
    print("\n=== 测试 IntentRecognizer - 规则匹配 ===")
    
    recognizer = IntentRecognizer()
    
    # 测试用例
    test_cases = [
        ("我喜欢看电影", IntentType.QUERY_SELF),
        ("我是什么样的人", IntentType.QUERY_SELF),
        ("我好难过啊", IntentType.COMFORT),
        ("今天心情不好", IntentType.COMFORT),
        ("分析一下我的状态", IntentType.ANALYZE),
        ("你好", IntentType.CHAT),  # 默认为CHAT
    ]
    
    for text, expected_intent in test_cases:
        result = recognizer.recognize_sync(text)
        print(f"文本: '{text}'")
        print(f"  识别意图: {result.intent.value}")
        print(f"  置信度: {result.confidence}")
        print(f"  关键词: {result.keywords}")
        
        assert result.intent == expected_intent, f"期望 {expected_intent.value}，实际 {result.intent.value}"
    
    print("✅ 规则匹配测试通过")


async def test_intent_recognizer_llm_fallback():
    """测试意图识别器 - LLM回退"""
    print("\n=== 测试 IntentRecognizer - LLM回退 ===")
    
    mock_llm = MockLLMCaller()
    recognizer = IntentRecognizer(llm_caller=mock_llm)
    
    # 测试规则无法匹配时使用LLM
    text = "我感觉很失落"  # 包含"失落"，应该被规则匹配为COMFORT
    result = await recognizer.recognize(text, use_llm=True)
    
    print(f"文本: '{text}'")
    print(f"  识别意图: {result.intent.value}")
    print(f"  方法: {result.metadata.get('method')}")
    
    assert result.intent == IntentType.COMFORT
    
    # 测试完全无法匹配的文本
    text2 = "今天天气真好"
    result2 = await recognizer.recognize(text2, use_llm=True)
    
    print(f"文本: '{text2}'")
    print(f"  识别意图: {result2.intent.value}")
    print(f"  方法: {result2.metadata.get('method')}")
    print(f"  LLM调用次数: {mock_llm.call_count}")
    
    print("✅ LLM回退测试通过")


def test_intent_recognizer_custom_intents():
    """测试意图识别器 - 自定义意图"""
    print("\n=== 测试 IntentRecognizer - 自定义意图 ===")
    
    # 创建带自定义意图的识别器
    custom_rules = {
        "book_query": [r"推荐.*?书", r"什么书", r"书籍"],
        "music_recommendation": [r"推荐.*?音乐", r"什么歌", r"音乐"],
    }
    
    recognizer = IntentRecognizer(intent_rules=custom_rules, extend_default=True)
    
    # 测试自定义意图
    text1 = "推荐一本好书"
    result1 = recognizer.recognize_sync(text1)
    print(f"文本: '{text1}'")
    print(f"  识别意图: {result1.intent.value}")
    
    # 动态注册新意图
    recognizer.register_intent("movie_query", [r"推荐.*?电影", r"什么电影"])
    
    text2 = "推荐一部电影"
    result2 = recognizer.recognize_sync(text2)
    print(f"文本: '{text2}'")
    print(f"  识别意图: {result2.intent.value}")
    
    # 获取所有注册的意图
    intents = recognizer.get_registered_intents()
    print(f"已注册的意图: {intents}")
    
    assert "book_query" in intents or "CUSTOM" in [i.upper() for i in intents]
    
    print("✅ 自定义意图测试通过")


def test_entity_extractor_jieba():
    """测试实体提取器 - jieba提取"""
    print("\n=== 测试 EntityExtractor - jieba提取 ===")
    
    extractor = EntityExtractor(enable_jieba=True)
    
    # 跳过测试如果jieba未安装
    if not extractor.enable_jieba:
        print("⚠️  jieba未安装，跳过测试")
        return
    
    text = "张三在北京清华大学学习人工智能"
    entities = extractor.extract_sync(text)
    
    print(f"文本: '{text}'")
    print(f"提取到 {len(entities)} 个实体:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.type.value}) [{entity.start}:{entity.end}]")
    
    # 验证至少提取到一些实体
    assert len(entities) > 0, "应该提取到至少一个实体"
    
    print("✅ jieba提取测试通过")


async def test_entity_extractor_llm():
    """测试实体提取器 - LLM增强"""
    print("\n=== 测试 EntityExtractor - LLM增强 ===")
    
    mock_llm = MockLLMCaller()
    extractor = EntityExtractor(llm_caller=mock_llm, enable_jieba=True)
    
    text = "张三在北京学习人工智能"
    entities = await extractor.extract(text, use_llm=True, use_backend=False)
    
    print(f"文本: '{text}'")
    print(f"提取到 {len(entities)} 个实体:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.type.value})")
        print(f"    方法: {entity.metadata.get('method')}")
    
    assert len(entities) > 0, "LLM应该提取到实体"
    assert any(e.metadata.get('method') == 'llm' for e in entities), "应该包含LLM提取的实体"
    
    print("✅ LLM增强测试通过")


def test_entity_extractor_custom_dict():
    """测试实体提取器 - 自定义词典"""
    print("\n=== 测试 EntityExtractor - 自定义词典 ===")
    
    extractor = EntityExtractor(enable_jieba=True)
    
    if not extractor.enable_jieba:
        print("⚠️  jieba未安装，跳过测试")
        return
    
    # 测试自定义NER函数
    def custom_ner(text: str) -> List[Entity]:
        """自定义NER函数示例"""
        entities = []
        if "Python" in text:
            entities.append(Entity(
                text="Python",
                type=EntityType.CONCEPT,
                start=text.find("Python"),
                end=text.find("Python") + 6,
                confidence=1.0,
                metadata={"method": "custom"}
            ))
        return entities
    
    extractor.set_custom_ner_function(custom_ner)
    
    text = "我喜欢用Python编程"
    entities = extractor.extract_sync(text)
    
    print(f"文本: '{text}'")
    print(f"提取到 {len(entities)} 个实体:")
    for entity in entities:
        print(f"  - {entity.text} ({entity.type.value})")
    
    assert any(e.text == "Python" for e in entities), "应该提取到Python实体"
    
    print("✅ 自定义词典测试通过")


def test_emotion_analyzer_dict():
    """测试情感分析器 - 词典分析"""
    print("\n=== 测试 EmotionAnalyzer - 词典分析 ===")
    
    analyzer = EmotionAnalyzer()
    
    test_cases = [
        ("今天好开心啊！", EmotionType.JOY),
        ("我好难过", EmotionType.SADNESS),
        ("太生气了", EmotionType.ANGER),
        ("有点害怕", EmotionType.FEAR),
        ("今天去超市了", EmotionType.NEUTRAL),
    ]
    
    for text, expected_emotion in test_cases:
        result = analyzer.analyze_sync(text)
        print(f"文本: '{text}'")
        print(f"  情绪: {result.emotion.value}")
        print(f"  强度: {result.intensity:.2f}")
        print(f"  效价: {result.valence:.2f}")
        print(f"  关键词: {result.keywords}")
        
        assert result.emotion == expected_emotion, f"期望 {expected_emotion.value}，实际 {result.emotion.value}"
        
        # 验证强度和效价的范围
        assert 0 <= result.intensity <= 1
        assert -1 <= result.valence <= 1
    
    print("✅ 词典分析测试通过")


async def test_emotion_analyzer_llm():
    """测试情感分析器 - LLM分析"""
    print("\n=== 测试 EmotionAnalyzer - LLM分析 ===")
    
    mock_llm = MockLLMCaller()
    analyzer = EmotionAnalyzer(llm_caller=mock_llm)
    
    text = "今天过得真开心"
    result = await analyzer.analyze(text, use_llm=True)
    
    print(f"文本: '{text}'")
    print(f"  情绪: {result.emotion.value}")
    print(f"  强度: {result.intensity:.2f}")
    print(f"  效价: {result.valence:.2f}")
    print(f"  方法: {result.metadata.get('method')}")
    
    assert result.metadata.get('method') == 'llm'
    assert 0 <= result.intensity <= 1
    assert -1 <= result.valence <= 1
    
    print("✅ LLM分析测试通过")


async def test_summarizer_strategies():
    """测试摘要生成器 - 多种策略"""
    print("\n=== 测试 Summarizer - 多种摘要策略 ===")
    
    mock_llm = MockLLMCaller()
    summarizer = Summarizer(llm_caller=mock_llm)
    
    text = """人工智能是计算机科学的一个分支。
它试图理解智能的实质。
人工智能可以应用于很多领域。
机器学习是人工智能的核心技术之一。
深度学习是机器学习的一个重要分支。"""
    
    # 测试生成式摘要
    print("\n--- 生成式摘要 ---")
    summarizer.set_strategy(SummaryStrategy.GENERATIVE)
    summary1 = await summarizer.summarize(text, max_length=100)
    
    print(f"摘要: {summary1.content}")
    print(f"关键点: {summary1.key_points}")
    print(f"话题: {summary1.topics}")
    print(f"方法: {summary1.metadata.get('method')}")
    
    assert summary1.content, "摘要内容不应为空"
    assert summary1.metadata.get('strategy') == 'generative'
    
    # 测试抽取式摘要
    print("\n--- 抽取式摘要 ---")
    summarizer.set_strategy(SummaryStrategy.EXTRACTIVE)
    summary2 = await summarizer.summarize(text, max_length=100)
    
    print(f"摘要: {summary2.content}")
    print(f"关键点数量: {len(summary2.key_points)}")
    print(f"方法: {summary2.metadata.get('method')}")
    
    assert summary2.metadata.get('strategy') == 'extractive'
    
    # 测试混合式摘要
    print("\n--- 混合式摘要 ---")
    summarizer.set_strategy(SummaryStrategy.HYBRID)
    summary3 = await summarizer.summarize(text, max_length=100)
    
    print(f"摘要: {summary3.content}")
    print(f"方法: {summary3.metadata.get('method')}")
    
    assert summary3.metadata.get('strategy') == 'hybrid'
    
    print("✅ 多种策略测试通过")


async def test_summarizer_session():
    """测试摘要生成器 - 对话摘要"""
    print("\n=== 测试 Summarizer - 对话摘要 ===")
    
    mock_llm = MockLLMCaller()
    mock_entity_extractor = EntityExtractor(llm_caller=mock_llm, enable_jieba=False)
    mock_emotion_analyzer = EmotionAnalyzer(llm_caller=mock_llm)
    
    summarizer = Summarizer(
        llm_caller=mock_llm,
        entity_extractor=mock_entity_extractor,
        emotion_analyzer=mock_emotion_analyzer
    )
    
    # 模拟一段对话
    messages = [
        {"role": "user", "content": "我最近在学习人工智能"},
        {"role": "assistant", "content": "很好！人工智能是一个很有前景的领域"},
        {"role": "user", "content": "我对机器学习特别感兴趣"},
        {"role": "assistant", "content": "机器学习是人工智能的核心技术"},
        {"role": "user", "content": "有什么好的学习资源推荐吗"},
    ]
    
    summary = await summarizer.summarize_session(
        messages,
        extract_entities=True,
        analyze_emotions=True
    )
    
    print(f"对话摘要: {summary.content}")
    print(f"关键点: {summary.key_points}")
    print(f"话题: {summary.topics}")
    print(f"消息数: {summary.metadata.get('message_count')}")
    print(f"用户消息数: {summary.metadata.get('user_message_count')}")
    
    assert summary.content, "对话摘要不应为空"
    assert summary.metadata.get('source') == 'session'
    assert summary.metadata.get('message_count') == 5
    assert summary.metadata.get('user_message_count') == 3
    
    print("✅ 对话摘要测试通过")


def test_data_model_validation():
    """测试数据模型验证"""
    print("\n=== 测试数据模型验证 ===")
    
    # 测试IntentResult验证
    try:
        result = IntentResult(intent=IntentType.CHAT, confidence=1.5)
        assert False, "应该抛出异常"
    except ValueError as e:
        print(f"✓ IntentResult验证正确: {e}")
    
    # 测试Entity验证
    try:
        entity = Entity(text="测试", type=EntityType.PERSON, confidence=2.0)
        assert False, "应该抛出异常"
    except ValueError as e:
        print(f"✓ Entity验证正确: {e}")
    
    # 测试EmotionResult验证
    try:
        emotion = EmotionResult(
            emotion=EmotionType.JOY,
            intensity=0.8,
            valence=2.0  # 超出范围
        )
        assert False, "应该抛出异常"
    except ValueError as e:
        print(f"✓ EmotionResult验证正确: {e}")
    
    print("✅ 数据模型验证测试通过")


# ============== 集成测试 ==============

async def test_nlp_integration():
    """NLP模块集成测试"""
    print("\n=== NLP模块集成测试 ===")
    
    mock_llm = MockLLMCaller()
    
    # 创建所有组件
    intent_recognizer = IntentRecognizer(llm_caller=mock_llm)
    entity_extractor = EntityExtractor(llm_caller=mock_llm, enable_jieba=True)
    emotion_analyzer = EmotionAnalyzer(llm_caller=mock_llm)
    summarizer = Summarizer(
        llm_caller=mock_llm,
        entity_extractor=entity_extractor,
        emotion_analyzer=emotion_analyzer
    )
    
    # 测试完整流程
    text = "我最近很难过，因为工作压力太大了"
    
    print(f"分析文本: '{text}'")
    
    # 1. 意图识别
    intent = await intent_recognizer.recognize(text, use_llm=False)
    print(f"\n意图: {intent.intent.value} (置信度: {intent.confidence})")
    
    # 2. 实体提取
    entities = await entity_extractor.extract(text, use_llm=True, use_backend=True)
    print(f"\n实体: {[e.text for e in entities]}")
    
    # 3. 情感分析
    emotion = await emotion_analyzer.analyze(text, use_llm=False)
    print(f"\n情感: {emotion.emotion.value}")
    print(f"  强度: {emotion.intensity:.2f}")
    print(f"  效价: {emotion.valence:.2f}")
    
    # 4. 生成摘要
    summary = await summarizer.summarize(text, max_length=100)
    print(f"\n摘要: {summary.content}")
    
    assert intent.intent == IntentType.COMFORT, "应该识别为安慰意图"
    assert emotion.emotion in [EmotionType.SADNESS, EmotionType.FEAR], "应该识别为负面情绪"
    assert summary.content, "摘要不应为空"
    
    print("\n✅ 集成测试通过")


# ============== 主测试函数 ==============

def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("NLP模块完整测试套件")
    print("=" * 60)
    
    # 同步测试
    test_intent_recognizer_rule_matching()
    test_intent_recognizer_custom_intents()
    test_entity_extractor_jieba()
    test_entity_extractor_custom_dict()
    test_emotion_analyzer_dict()
    test_data_model_validation()
    
    # 异步测试
    async def run_async_tests():
        await test_intent_recognizer_llm_fallback()
        await test_entity_extractor_llm()
        await test_emotion_analyzer_llm()
        await test_summarizer_strategies()
        await test_summarizer_session()
        await test_nlp_integration()
    
    asyncio.run(run_async_tests())
    
    print("\n" + "=" * 60)
    print("✅ 所有NLP测试通过！")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
