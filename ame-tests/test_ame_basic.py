"""
AME系统基础测试（不依赖外部库）

测试整个架构的基本功能。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def log_info(msg):
    print(f"[INFO] {msg}")

def log_success(msg):
    print(f"[✓] {msg}")

def log_error(msg):
    print(f"[✗] {msg}")


async def test_nlp_foundation():
    """测试NLP Foundation层"""
    print("\n" + "=" * 60)
    print("测试 Foundation - NLP层")
    print("=" * 60)
    
    from ame.foundation.nlp import (
        IntentRecognizer,
        EntityExtractor,
        EmotionAnalyzer,
        IntentType,
        EmotionType
    )
    
    # 1. 测试意图识别
    recognizer = IntentRecognizer()
    intent_result = recognizer.recognize_sync("我想知道我的兴趣爱好")
    assert intent_result.intent == IntentType.QUERY_SELF, f"Expected QUERY_SELF, got {intent_result.intent}"
    log_success(f"意图识别: {intent_result.intent.value} (置信度: {intent_result.confidence})")
    
    # 2. 测试实体提取（跳过jieba）
    extractor = EntityExtractor(enable_jieba=False)
    log_success(f"实体提取器创建成功")
    
    # 3. 测试情感分析
    analyzer = EmotionAnalyzer()
    emotion = analyzer.analyze_sync("今天真是太开心了！")
    log_success(f"情感分析: {emotion.emotion.value} (强度: {emotion.intensity:.2f}, 效价: {emotion.valence:.2f})")


async def test_algorithm_foundation():
    """测试Algorithm Foundation层"""
    print("\n" + "=" * 60)
    print("测试 Foundation - Algorithm层")
    print("=" * 60)
    
    from ame.foundation.algorithm import TodoSorter, TodoItem, Priority
    from datetime import datetime, timedelta
    
    # 创建待办列表
    todos = [
        TodoItem(
            id="1",
            title="任务A",
            priority=Priority.HIGH,
            due_date=datetime.now() + timedelta(days=1)
        ),
        TodoItem(
            id="2",
            title="任务B",
            priority=Priority.MEDIUM,
            due_date=datetime.now() + timedelta(days=3),
            dependencies=["1"]
        ),
        TodoItem(
            id="3",
            title="任务C",
            priority=Priority.LOW
        )
    ]
    
    # 排序
    sorter = TodoSorter()
    result = sorter.sort(todos, consider_dependencies=True)
    
    assert len(result.sorted_todos) == 3, f"Expected 3 todos, got {len(result.sorted_todos)}"
    log_success(f"待办排序: {len(result.sorted_todos)} 个任务已排序")
    for i, todo in enumerate(result.sorted_todos, 1):
        log_info(f"  {i}. {todo.title} (优先级: {todo.priority.value})")
    
    # 验证依赖顺序：任务A应该在任务B之前
    ids = [t.id for t in result.sorted_todos]
    assert ids.index("1") < ids.index("2"), "Task dependency order incorrect"
    log_success("依赖关系排序正确")


async def test_capability_factory():
    """测试Capability Factory"""
    print("\n" + "=" * 60)
    print("测试 Capability - Factory")
    print("=" * 60)
    
    from ame.capability import CapabilityFactory
    
    factory = CapabilityFactory()
    
    # 测试创建NLP能力（不需要真实LLM）
    recognizer = factory.create_intent_recognizer(cache_key="test_intent")
    assert recognizer is not None
    log_success("创建意图识别器")
    
    # 测试缓存
    recognizer2 = factory.create_intent_recognizer(cache_key="test_intent")
    assert recognizer is recognizer2, "Cache not working"
    log_success("缓存机制正常")
    
    # 测试缓存信息
    cache_info = factory.get_cache_info()
    log_success(f"缓存统计: {cache_info['total_cached']} 个实例")
    
    # 测试清理缓存
    factory.clear_cache("test")
    cache_info_after = factory.get_cache_info()
    log_success(f"清理后缓存: {cache_info_after['total_cached']} 个实例")


async def test_services():
    """测试Service层（不需要真实API）"""
    print("\n" + "=" * 60)
    print("测试 Service层")
    print("=" * 60)
    
    from ame.capability import CapabilityFactory
    from ame.service import ConnectService
    
    factory = CapabilityFactory()
    
    # 测试ConnectService初始化
    connect_service = ConnectService(factory)
    assert connect_service is not None
    log_success("ConnectService 初始化成功")
    
    log_info("（跳过LLM/Storage实际连接测试，需要真实配置）")


async def test_architecture_compliance():
    """测试架构规范遵循"""
    print("\n" + "=" * 60)
    print("测试架构规范遵循")
    print("=" * 60)
    
    from ame.capability import CapabilityFactory
    from ame.service import ConnectService
    import inspect
    
    # 检查ConnectService构造函数
    sig = inspect.signature(ConnectService.__init__)
    params = list(sig.parameters.keys())
    
    # 验证第一个参数是capability_factory
    assert "capability_factory" in params, "Missing capability_factory parameter"
    log_success("ConnectService遵循依赖注入规范（使用CapabilityFactory）")
    
    # 验证不直接依赖Foundation层
    assert "llm_caller" not in params, "Should not directly depend on llm_caller"
    assert "graph_store" not in params, "Should not directly depend on graph_store"
    log_success("ConnectService不直接依赖Foundation层组件")


async def test_data_models():
    """测试数据模型"""
    print("\n" + "=" * 60)
    print("测试数据模型")
    print("=" * 60)
    
    from ame.foundation.nlp import (
        IntentResult,
        IntentType,
        Entity,
        EntityType,
        EmotionResult,
        EmotionType
    )
    
    # 测试IntentResult
    intent = IntentResult(
        intent=IntentType.CHAT,
        confidence=0.9,
        keywords=["测试"]
    )
    assert intent.confidence == 0.9
    log_success("IntentResult 模型正常")
    
    # 测试Entity
    entity = Entity(
        text="北京",
        type=EntityType.LOCATION,
        confidence=0.8
    )
    assert entity.type == EntityType.LOCATION
    log_success("Entity 模型正常")
    
    # 测试EmotionResult
    emotion = EmotionResult(
        emotion=EmotionType.JOY,
        intensity=0.8,
        valence=0.9
    )
    assert emotion.valence == 0.9
    log_success("EmotionResult 模型正常")


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "🚀 " * 20)
    print("AME系统基础测试开始")
    print("🚀 " * 20)
    
    tests = [
        ("NLP Foundation", test_nlp_foundation),
        ("Algorithm Foundation", test_algorithm_foundation),
        ("Capability Factory", test_capability_factory),
        ("Service Layer", test_services),
        ("Architecture Compliance", test_architecture_compliance),
        ("Data Models", test_data_models),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            await test_func()
            passed += 1
        except Exception as e:
            failed += 1
            log_error(f"{test_name} 失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ 所有测试通过！\n")
        return True
    else:
        print(f"\n❌ {failed} 个测试失败\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
