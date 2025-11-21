"""
简单Embedding实现

基于TF-IDF的简单向量化实现,用于测试和演示。
不需要外部依赖,可直接使用。
"""

from typing import List, Optional, Dict
import hashlib
import logging

from .base import EmbeddingBase
from ..core.models import EmbeddingResult, EmbeddingConfig
from ..core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class SimpleEmbedding(EmbeddingBase):
    """
    简单Embedding实现
    
    基于文本哈希生成固定维度的向量。
    仅用于测试和演示,不适合生产环境。
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        初始化
        
        Args:
            config: Embedding配置
        """
        if config is None:
            config = EmbeddingConfig(
                model="simple-embedding",
                dimension=384  # 常见的小型向量维度
            )
        super().__init__(config)
        self._vocabulary: Dict[str, int] = {}
        logger.info(f"SimpleEmbedding initialized with dimension={config.dimension}")
    
    def embed_text(self, text: str) -> EmbeddingResult:
        """
        文本向量化
        
        使用简单哈希算法生成向量。
        
        Args:
            text: 文本
        
        Returns:
            EmbeddingResult: 向量结果
        """
        if not text:
            # 空文本返回零向量
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
        """
        批量向量化
        
        Args:
            texts: 文本列表
        
        Returns:
            List[EmbeddingResult]: 结果列表
        """
        results = []
        for text in texts:
            results.append(self.embed_text(text))
        
        logger.debug(f"Batch embedded {len(texts)} texts")
        return results
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.config.dimension
    
    def is_configured(self) -> bool:
        """检查是否已配置"""
        return self.config is not None and self.config.dimension > 0
    
    def _hash_to_vector(self, text: str) -> List[float]:
        """
        将文本哈希转换为向量
        
        Args:
            text: 文本
        
        Returns:
            List[float]: 向量
        """
        # 使用MD5哈希
        hash_obj = hashlib.md5(text.encode('utf-8'))
        hash_bytes = hash_obj.digest()
        
        # 生成向量
        vector = []
        dimension = self.config.dimension
        
        # 从哈希值生成伪随机向量
        for i in range(dimension):
            # 使用哈希值的不同部分生成不同的值
            byte_index = i % len(hash_bytes)
            seed = hash_bytes[byte_index] + i
            
            # 归一化到[-1, 1]
            value = (seed % 256) / 128.0 - 1.0
            vector.append(value)
        
        # L2归一化
        vector = self._normalize_l2(vector)
        
        return vector
    
    def _normalize_l2(self, vector: List[float]) -> List[float]:
        """
        L2归一化
        
        Args:
            vector: 原始向量
        
        Returns:
            List[float]: 归一化后的向量
        """
        # 计算L2范数
        l2_norm = sum(x * x for x in vector) ** 0.5
        
        if l2_norm == 0:
            return vector
        
        # 归一化
        return [x / l2_norm for x in vector]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        计算余弦相似度
        
        Args:
            vec1: 向量1
            vec2: 向量2
        
        Returns:
            float: 相似度[-1, 1]
        """
        if len(vec1) != len(vec2):
            raise ValueError("向量维度不匹配")
        
        # 点积
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # L2归一化的向量,点积即为余弦相似度
        return dot_product
