"""
AME系统集成测试

测试整个架构的集成情况，包括Foundation、Capability、Service层。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from loguru import logger


async def test_nlp_foundation():
    """测试NLP Foundation层"""
    logger.info("=" * 60)
    logger.info("测试 Foundation - NLP层")
    logger.info("=" * 60)
    
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
    assert intent_result.intent == IntentType.QUERY_SELF
    logger.success(f"✓ 意图识别: {intent_result.intent.value} (置信度: {intent_result.confidence})")
    
    # 2. 测试实体提取
    extractor = EntityExtractor(enable_jieba=True)
    entities = extractor.extract_sync("我今天去北京玩")
    logger.success(f"✓ 实体提取: 找到 {len(entities)} 个实体")
    for entity in entities:
        logger.info(f"  - {entity.text} ({entity.type.value})")
    
    # 3. 测试情感分析
    analyzer = EmotionAnalyzer()
    emotion = analyzer.analyze_sync("今天真是太开心了！")
    assert emotion.emotion in [EmotionType.JOY, EmotionType.NEUTRAL]
    logger.success(f"✓ 情感分析: {emotion.emotion.value} (强度: {emotion.intensity}, 效价: {emotion.valence})")


async def test_algorithm_foundation():
    """测试Algorithm Foundation层"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 Foundation - Algorithm层")
    logger.info("=" * 60)
    
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
    
    assert len(result.sorted_todos) == 3
    logger.success(f"✓ 待办排序: {len(result.sorted_todos)} 个任务已排序")
    for i, todo in enumerate(result.sorted_todos, 1):
        logger.info(f"  {i}. {todo.title} (优先级: {todo.priority.value})")


async def test_capability_factory():
    """测试Capability Factory"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 Capability - Factory")
    logger.info("=" * 60)
    
    from ame.capability import CapabilityFactory
    
    factory = CapabilityFactory()
    
    # 测试创建NLP能力（不需要真实LLM）
    recognizer = factory.create_intent_recognizer(cache_key="test_intent")
    assert recognizer is not None
    logger.success("✓ 创建意图识别器")
    
    # 测试缓存
    recognizer2 = factory.create_intent_recognizer(cache_key="test_intent")
    assert recognizer is recognizer2
    logger.success("✓ 缓存机制正常")
    
    # 测试缓存信息
    cache_info = factory.get_cache_info()
    logger.success(f"✓ 缓存统计: {cache_info['total_cached']} 个实例")


async def test_services():
    """测试Service层（不需要真实API）"""
    logger.info("\n" + "=" * 60)
    logger.info("测试 Service层")
    logger.info("=" * 60)
    
    from ame.capability import CapabilityFactory
    from ame.service import ConnectService
    
    factory = CapabilityFactory()
    
    # 测试ConnectService初始化
    connect_service = ConnectService(factory)
    assert connect_service is not None
    logger.success("✓ ConnectService 初始化成功")
    
    # 注意：不执行实际的LLM/Storage测试，因为需要真实配置
    logger.info("  （跳过LLM/Storage实际连接测试）")


async def test_architecture_compliance():
    """测试架构规范遵循"""
    logger.info("\n" + "=" * 60)
    logger.info("测试架构规范遵循")
    logger.info("=" * 60)
    
    from ame.capability import CapabilityFactory
    from ame.service import ConnectService
    import inspect
    
    # 检查ConnectService构造函数
    sig = inspect.signature(ConnectService.__init__)
    params = list(sig.parameters.keys())
    
    # 验证第一个参数是capability_factory
    assert "capability_factory" in params
    logger.success("✓ ConnectService遵循依赖注入规范（使用CapabilityFactory）")
    
    # 验证不直接依赖Foundation层
    assert "llm_caller" not in params
    assert "graph_store" not in params
    logger.success("✓ ConnectService不直接依赖Foundation层组件")


async def run_all_tests():
    """运行所有测试"""
    logger.info("\n" + "🚀 " * 20)
    logger.info("AME系统集成测试开始")
    logger.info("🚀 " * 20 + "\n")
    
    try:
        await test_nlp_foundation()
        await test_algorithm_foundation()
        await test_capability_factory()
        await test_services()
        await test_architecture_compliance()
        
        logger.info("\n" + "=" * 60)
        logger.success("✅ 所有测试通过！")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
