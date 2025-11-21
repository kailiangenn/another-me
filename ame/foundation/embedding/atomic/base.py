"""
Embedding抽象基类

定义所有Embedding实现必须遵循的接口。
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import logging

from ..core.models import EmbeddingResult, EmbeddingConfig
from ..core.exceptions import EmbeddingError

logger = logging.getLogger(__name__)


class EmbeddingBase(ABC):
    """
    Embedding抽象基类
    
    所有Embedding实现(OpenAI, HuggingFace等)都应继承此类。
    """
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """
        初始化
        
        Args:
            config: Embedding配置
        """
        self.config = config or EmbeddingConfig()
        logger.debug(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod
    def embed_text(self, text: str) -> EmbeddingResult:
        """
        文本向量化(单条)
        
        Args:
            text: 待向量化的文本
        
        Returns:
            EmbeddingResult: 向量化结果
        
        Raises:
            EmbeddingError: 向量化失败
        """
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        批量文本向量化
        
        Args:
            texts: 文本列表
        
        Returns:
            List[EmbeddingResult]: 向量化结果列表
        
        Raises:
            EmbeddingError: 向量化失败
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """
        获取向量维度
        
        Returns:
            int: 向量维度
        """
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """
        检查是否已正确配置
        
        Returns:
            bool: 是否已配置
        """
        pass
    
    def validate_dimension(self, vector: List[float]) -> bool:
        """
        验证向量维度
        
        Args:
            vector: 向量
        
        Returns:
            bool: 是否有效
        """
        expected_dim = self.get_dimension()
        actual_dim = len(vector)
        
        if actual_dim != expected_dim:
            logger.error(
                f"维度不匹配: 期望{expected_dim}, 实际{actual_dim}"
            )
            return False
        
        return True
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的token数(简单估算)
        
        Args:
            text: 文本
        
        Returns:
            int: 估算的token数
        """
        # 简单估算: 中文2字符/token, 英文4字符/token
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        other_chars = len(text) - chinese_chars
        
        chinese_tokens = chinese_chars // 2
        other_tokens = other_chars // 4
        
        return max(1, chinese_tokens + other_tokens)
