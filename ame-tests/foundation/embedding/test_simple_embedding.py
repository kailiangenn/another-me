"""
SimpleEmbedding 单元测试
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 直接导入模块
from ame.foundation.embedding.atomic.simple_embedding import SimpleEmbedding
from ame.foundation.embedding.core.models import EmbeddingConfig


def test_basic_embedding():
    """测试基础向量化"""
    print("\n" + "="*60)
    print("测试: 基础向量化")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    text = "今天天气很好"
    result = embedding.embed_text(text)
    
    print(f"文本: {text}")
    print(f"向量维度: {result.dimension}")
    print(f"向量长度: {len(result.vector)}")
    print(f"前10个值: {result.vector[:10]}")
    print(f"模型: {result.model}")
    
    assert result.dimension == 384, "维度错误"
    assert len(result.vector) == 384, "向量长度错误"
    assert result.model == "simple-embedding", "模型名称错误"
    assert all(-1.0 <= v <= 1.0 for v in result.vector), "向量值应在[-1, 1]范围内"
    
    print("✓ 基础向量化测试通过")


def test_custom_dimension():
    """测试自定义维度"""
    print("\n" + "="*60)
    print("测试: 自定义维度")
    print("="*60)
    
    config = EmbeddingConfig(dimension=128)
    embedding = SimpleEmbedding(config)
    
    result = embedding.embed_text("测试文本")
    
    print(f"自定义维度: {config.dimension}")
    print(f"结果维度: {result.dimension}")
    print(f"向量长度: {len(result.vector)}")
    
    assert result.dimension == 128, "自定义维度未生效"
    assert len(result.vector) == 128, "向量长度错误"
    
    print("✓ 自定义维度测试通过")


def test_batch_embedding():
    """测试批量向量化"""
    print("\n" + "="*60)
    print("测试: 批量向量化")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    texts = [
        "今天天气很好",
        "我喜欢编程",
        "人工智能很有趣"
    ]
    
    results = embedding.embed_batch(texts)
    
    print(f"文本数量: {len(texts)}")
    print(f"结果数量: {len(results)}")
    
    assert len(results) == len(texts), "结果数量错误"
    
    for i, (text, result) in enumerate(zip(texts, results)):
        print(f"  {i+1}. {text} -> dim={result.dimension}")
        assert result.dimension == 384, f"第{i+1}个结果维度错误"
    
    print("✓ 批量向量化测试通过")


def test_same_text_same_vector():
    """测试相同文本生成相同向量"""
    print("\n" + "="*60)
    print("测试: 相同文本生成相同向量")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    text = "这是测试文本"
    result1 = embedding.embed_text(text)
    result2 = embedding.embed_text(text)
    
    # 计算相似度
    similarity = embedding.cosine_similarity(result1.vector, result2.vector)
    
    print(f"文本: {text}")
    print(f"第一次向量前5个值: {result1.vector[:5]}")
    print(f"第二次向量前5个值: {result2.vector[:5]}")
    print(f"余弦相似度: {similarity}")
    
    assert abs(similarity - 1.0) < 1e-6, "相同文本应生成相同向量"
    
    print("✓ 相同文本测试通过")


def test_different_text_different_vector():
    """测试不同文本生成不同向量"""
    print("\n" + "="*60)
    print("测试: 不同文本生成不同向量")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    text1 = "今天天气很好"
    text2 = "我喜欢编程"
    
    result1 = embedding.embed_text(text1)
    result2 = embedding.embed_text(text2)
    
    similarity = embedding.cosine_similarity(result1.vector, result2.vector)
    
    print(f"文本1: {text1}")
    print(f"文本2: {text2}")
    print(f"余弦相似度: {similarity}")
    
    assert abs(similarity) < 0.9, "不同文本应生成不同向量"
    
    print("✓ 不同文本测试通过")


def test_empty_text():
    """测试空文本"""
    print("\n" + "="*60)
    print("测试: 空文本处理")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    result = embedding.embed_text("")
    
    print(f"空文本向量维度: {result.dimension}")
    print(f"空文本向量(前10个): {result.vector[:10]}")
    
    assert result.dimension == 384, "空文本维度错误"
    assert all(v == 0.0 for v in result.vector), "空文本应返回零向量"
    
    print("✓ 空文本测试通过")


def test_get_dimension():
    """测试获取维度"""
    print("\n" + "="*60)
    print("测试: 获取维度")
    print("="*60)
    
    config = EmbeddingConfig(dimension=256)
    embedding = SimpleEmbedding(config)
    
    dim = embedding.get_dimension()
    
    print(f"配置维度: {config.dimension}")
    print(f"获取维度: {dim}")
    
    assert dim == 256, "获取维度错误"
    
    print("✓ 获取维度测试通过")


def test_is_configured():
    """测试配置检查"""
    print("\n" + "="*60)
    print("测试: 配置检查")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    is_conf = embedding.is_configured()
    
    print(f"是否已配置: {is_conf}")
    
    assert is_conf is True, "应该已配置"
    
    print("✓ 配置检查测试通过")


def test_validate_dimension():
    """测试维度验证"""
    print("\n" + "="*60)
    print("测试: 维度验证")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    # 正确维度
    vector_correct = [0.0] * 384
    is_valid1 = embedding.validate_dimension(vector_correct)
    print(f"正确维度(384): {is_valid1}")
    assert is_valid1 is True, "应该有效"
    
    # 错误维度
    vector_wrong = [0.0] * 100
    is_valid2 = embedding.validate_dimension(vector_wrong)
    print(f"错误维度(100): {is_valid2}")
    assert is_valid2 is False, "应该无效"
    
    print("✓ 维度验证测试通过")


def test_cosine_similarity():
    """测试余弦相似度计算"""
    print("\n" + "="*60)
    print("测试: 余弦相似度计算")
    print("="*60)
    
    embedding = SimpleEmbedding()
    
    # 测试完全相同
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    sim1 = embedding.cosine_similarity(vec1, vec2)
    print(f"相同向量相似度: {sim1}")
    # 注意:需要归一化
    
    # 测试正交
    vec3 = [1.0, 0.0, 0.0]
    vec4 = [0.0, 1.0, 0.0]
    sim2 = embedding.cosine_similarity(vec3, vec4)
    print(f"正交向量相似度: {sim2}")
    assert abs(sim2) < 0.1, "正交向量相似度应接近0"
    
    print("✓ 余弦相似度测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始 SimpleEmbedding 完整测试")
    print("="*60)
    
    tests = [
        test_basic_embedding,
        test_custom_dimension,
        test_batch_embedding,
        test_same_text_same_vector,
        test_different_text_different_vector,
        test_empty_text,
        test_get_dimension,
        test_is_configured,
        test_validate_dimension,
        test_cosine_similarity
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
