"""
Embedding 抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """嵌入向量结果"""
    vector: List[float]
    model: str
    dimension: int
    usage: Optional[int] = None  # token 使用量
    

class EmbeddingBase(ABC):
    """嵌入向量生成器抽象基类"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> EmbeddingResult:
        """
        生成单个文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            EmbeddingResult: 嵌入向量结果
        """
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """
        批量生成嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            List[EmbeddingResult]: 嵌入向量结果列表
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称"""
        pass
