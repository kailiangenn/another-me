"""
Memory 抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    content: str
    timestamp: datetime
    importance: float  # 0-1
    embedding: Optional[List[float]] = None
    
    # 元数据
    emotion: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # 统计
    access_count: int = 0
    last_access: Optional[datetime] = None


class MemoryBase(ABC):
    """记忆管理抽象基类"""
    
    @abstractmethod
    async def store(
        self,
        content: str,
        importance: float = 0.5,
        emotion: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        存储记忆
        
        Args:
            content: 记忆内容
            importance: 重要性（0-1）
            emotion: 情绪标签
            category: 分类
            tags: 标签列表
            metadata: 额外元数据
        
        Returns:
            memory_id: 记忆ID
        """
        pass
    
    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        time_decay: bool = True,
        importance_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """
        检索记忆
        
        Args:
            query: 查询内容
            top_k: 返回数量
            time_decay: 是否应用时间衰减
            importance_threshold: 重要性阈值
            filters: 过滤条件（category, tags等）
        
        Returns:
            List[MemoryItem]: 记忆列表
        """
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取单条记忆"""
        pass
    
    @abstractmethod
    async def update_importance(self, memory_id: str, importance: float) -> bool:
        """更新记忆重要性"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        pass
