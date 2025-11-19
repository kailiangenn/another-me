"""
向量数据库抽象基类

定义统一的向量数据库接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np


@dataclass
class Vector:
    """向量对象"""
    id: str                          # 向量ID
    embedding: np.ndarray            # 向量数据
    metadata: Dict[str, Any]         # 元数据


@dataclass
class SearchResult:
    """向量检索结果"""
    id: str                          # 向量ID
    score: float                     # 相似度分数
    metadata: Dict[str, Any]         # 元数据
    embedding: Optional[np.ndarray] = None  # 向量数据(可选)


class VectorStoreBase(ABC):
    """
    向量数据库抽象接口
    
    所有具体实现需要实现以下方法:
    - 连接管理
    - 向量CRUD
    - 向量检索
    - 批量操作
    """
    
    # ===== 连接管理 =====
    
    @abstractmethod
    async def connect(self) -> None:
        """建立连接"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """断开连接"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    # ===== 向量基础操作 =====
    
    @abstractmethod
    async def add_vector(
        self,
        vector_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        添加单个向量
        
        Args:
            vector_id: 向量ID
            embedding: 向量数据
            metadata: 元数据
        
        Returns:
            success: 是否添加成功
        """
        pass
    
    @abstractmethod
    async def add_vectors(
        self,
        vectors: List[Vector]
    ) -> List[str]:
        """
        批量添加向量
        
        Args:
            vectors: 向量列表
        
        Returns:
            ids: 成功添加的向量ID列表
        """
        pass
    
    @abstractmethod
    async def get_vector(
        self,
        vector_id: str,
        include_embedding: bool = False
    ) -> Optional[Vector]:
        """
        获取向量
        
        Args:
            vector_id: 向量ID
            include_embedding: 是否包含向量数据
        
        Returns:
            vector: 向量对象,不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_vector(
        self,
        vector_id: str,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        更新向量
        
        Args:
            vector_id: 向量ID
            embedding: 新的向量数据(可选)
            metadata: 新的元数据(可选)
        
        Returns:
            success: 是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete_vector(self, vector_id: str) -> bool:
        """
        删除向量
        
        Args:
            vector_id: 向量ID
        
        Returns:
            success: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def delete_vectors(self, vector_ids: List[str]) -> int:
        """
        批量删除向量
        
        Args:
            vector_ids: 向量ID列表
        
        Returns:
            count: 成功删除的数量
        """
        pass
    
    # ===== 向量检索 =====
    
    @abstractmethod
    async def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None,
        include_embedding: bool = False
    ) -> List[SearchResult]:
        """
        向量检索
        
        Args:
            query_vector: 查询向量
            k: 返回Top-K结果
            filter: 元数据过滤条件
            include_embedding: 是否包含向量数据
        
        Returns:
            results: 检索结果列表(按相似度降序)
        """
        pass
    
    @abstractmethod
    async def search_by_id(
        self,
        vector_id: str,
        k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        根据向量ID检索相似向量
        
        Args:
            vector_id: 向量ID
            k: 返回Top-K结果
            filter: 元数据过滤条件
        
        Returns:
            results: 检索结果列表
        """
        pass
    
    # ===== 统计与管理 =====
    
    @abstractmethod
    async def count(
        self,
        filter: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计向量数量
        
        Args:
            filter: 元数据过滤条件
        
        Returns:
            count: 向量数量
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        清空所有向量
        
        Returns:
            success: 是否清空成功
        """
        pass
    
    # ===== 索引管理 =====
    
    @abstractmethod
    async def build_index(self, **kwargs) -> bool:
        """
        构建或重建索引
        
        Args:
            **kwargs: 索引参数(依具体实现而定)
        
        Returns:
            success: 是否构建成功
        """
        pass
    
    @abstractmethod
    async def save_index(self, path: str) -> bool:
        """
        保存索引到文件
        
        Args:
            path: 保存路径
        
        Returns:
            success: 是否保存成功
        """
        pass
    
    @abstractmethod
    async def load_index(self, path: str) -> bool:
        """
        从文件加载索引
        
        Args:
            path: 索引文件路径
        
        Returns:
            success: 是否加载成功
        """
        pass
