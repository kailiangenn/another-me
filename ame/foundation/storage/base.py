"""
存储抽象基类

定义所有存储后端的统一接口
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class StorageConfig:
    """存储配置"""
    storage_type: str           # 存储类型（vector/graph/metadata/document）
    storage_path: str           # 存储路径
    dimension: Optional[int] = None  # 向量维度（仅向量存储需要）
    metadata: Dict[str, Any] = None  # 额外配置
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StorageBase(ABC):
    """存储抽象基类"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化存储
        
        Returns:
            success: 是否成功
        """
        pass
    
    @abstractmethod
    async def add(self, item: Any) -> str:
        """
        添加项
        
        Args:
            item: 要添加的项
            
        Returns:
            item_id: 项的唯一标识
        """
        pass
    
    @abstractmethod
    async def get(self, item_id: str) -> Optional[Any]:
        """
        获取项
        
        Args:
            item_id: 项的唯一标识
            
        Returns:
            item: 项对象，不存在则返回 None
        """
        pass
    
    @abstractmethod
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新项
        
        Args:
            item_id: 项的唯一标识
            updates: 更新内容
            
        Returns:
            success: 是否成功
        """
        pass
    
    @abstractmethod
    async def delete(self, item_id: str) -> bool:
        """
        删除项
        
        Args:
            item_id: 项的唯一标识
            
        Returns:
            success: 是否成功
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        query: Any,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        搜索
        
        Args:
            query: 查询条件
            top_k: 返回数量
            filters: 过滤条件
            
        Returns:
            results: 搜索结果列表
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计数量
        
        Args:
            filters: 过滤条件
            
        Returns:
            count: 数量
        """
        pass
    
    @abstractmethod
    async def clear(self) -> bool:
        """
        清空存储
        
        Returns:
            success: 是否成功
        """
        pass
    
    @abstractmethod
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        pass
