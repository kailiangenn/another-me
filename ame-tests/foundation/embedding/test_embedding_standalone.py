"""
Embedding模块独立测试

将所有依赖代码嵌入,避免导入问题。
"""

import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from abc import ABC, abstractmethod
import hashlib
import logging

# ============================================================================
# 嵌入的数据模型
# ============================================================================

@dataclass
class EmbeddingResult:
    """Embedding结果"""
    vector: List[float]
    dimension: int
    model: str
    usage: Optional[Dict[str, int]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证数据"""
        if len(self.vector) != self.dimension:
            raise ValueError(
                f"向量长度({len(self.vector)})与维度({self.dimension})不匹配"
            )


@dataclass
class EmbeddingConfig:
    """Embedding配置"""
    model: str = "text-embedding-ada-002"
    dimension: int = 1536
    batch_size: int = 100
    max_retries: int = 3
    timeout: int = 30
    api_base: Optional[str] = None
    api_key: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# 嵌入的抽象基类
# ============================================================================

class EmbeddingBase(ABC):
    """Embedding抽象基类"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        self.config = config or EmbeddingConfig()
    
    @abstractmethod
    def embed_text(self, text: str) -> EmbeddingResult:
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        pass
    
    def validate_dimension(self, vector: List[float]) -> bool:
        expected_dim = self.get_dimension()
        return len(vector) == expected_dim
    
    def estimate_tokens(self, text: str) -> int:
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        return max(1, chinese_chars // 2 + other_chars // 4)


# ============================================================================
# 嵌入的SimpleEmbedding实现
# ============================================================================

class SimpleEmbedding(EmbeddingBase):
    """简单Embedding实现"""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        if config is None:
            config = EmbeddingConfig(
                model="simple-embedding",
                dimension=384
            )
        super().__init__(config)
    
    def embed_text(self, text: str) -> EmbeddingResult:
        if not text:
            vector = [0.0] * self.config.dimension
        else:
            vector = self._hash_to_vector(text)
        
        return EmbeddingResult(
            vector=vector,
            dimension=self.config.dimension,
            model=self.config.model,
            usage={"tokens": self.estimate_tokens(text)},
            metadata={"method": "hash"}
        )
    
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        return [self.embed_text(text) for text in texts]
    
    def get_dimension(self) -> int:
        return self.config.dimension
    
    def is_configured(self) -> bool:
        return self.config is not None and self.config.dimension > 0
    
    def _hash_to_vector(self, text: str) -> List[float]:
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        vector = []
        dimension = self.config.dimension
        
        for i in range(dimension):
            byte_index = i % len(hash_bytes)
            seed = hash_bytes[byte_index] + i
            value = (seed % 256) / 128.0 - 1.0
            vector.append(value)
        
        return self._normalize_l2(vector)
    
    def _normalize_l2(self, vector: List[float]) -> List[float]:
        l2_norm = sum(x * x for x in vector) ** 0.5
        if l2_norm == 0:
            return vector
        return [x / l2_norm for x in vector]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            raise ValueError("向量维度不匹配")
        return sum(a * b for a, b in zip(vec1, vec2))


# ============================================================================
# 测试用例
# ============================================================================

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
    print(f"向量前10个值: {result.vector[:10]}")
    
    assert result.dimension == 384
    assert len(result.vector) == 384
    assert all(-1.0 <= v <= 1.0 for v in result.vector)
    
    print("✓ 基础向量化测试通过")


def test_batch_embedding():
    """测试批量向量化"""
    print("\n" + "="*60)
    print("测试: 批量向量化")
    print("="*60)
    
    embedding = SimpleEmbedding()
    texts = ["今天天气很好", "我喜欢编程", "人工智能很有趣"]
    results = embedding.embed_batch(texts)
    
    print(f"文本数量: {len(texts)}")
    print(f"结果数量: {len(results)}")
    
    assert len(results) == len(texts)
    for result in results:
        assert result.dimension == 384
    
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
    
    similarity = embedding.cosine_similarity(result1.vector, result2.vector)
    print(f"文本: {text}")
    print(f"余弦相似度: {similarity}")
    
    assert abs(similarity - 1.0) < 1e-6
    
    print("✓ 相同文本测试通过")


def test_empty_text():
    """测试空文本"""
    print("\n" + "="*60)
    print("测试: 空文本处理")
    print("="*60)
    
    embedding = SimpleEmbedding()
    result = embedding.embed_text("")
    
    print(f"空文本向量维度: {result.dimension}")
    assert all(v == 0.0 for v in result.vector)
    
    print("✓ 空文本测试通过")


def test_custom_dimension():
    """测试自定义维度"""
    print("\n" + "="*60)
    print("测试: 自定义维度")
    print("="*60)
    
    config = EmbeddingConfig(dimension=128)
    embedding = SimpleEmbedding(config)
    result = embedding.embed_text("测试")
    
    print(f"自定义维度: {config.dimension}")
    print(f"结果维度: {result.dimension}")
    
    assert result.dimension == 128
    assert len(result.vector) == 128
    
    print("✓ 自定义维度测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始 Embedding 模块测试")
    print("="*60)
    
    tests = [
        test_basic_embedding,
        test_batch_embedding,
        test_same_text_same_vector,
        test_empty_text,
        test_custom_dimension
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
