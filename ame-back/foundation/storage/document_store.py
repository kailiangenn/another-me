"""
文档存储 - 统一 CRUD 接口

提供文档的统一 CRUD 操作接口，整合向量、图谱、元数据存储

特性：
- 统一的文档 CRUD 接口
- 自动同步多个存储后端
- 事务性操作
- 批量操作支持

TODO: 从 repository/hybrid_repository.py 提取 CRUD 逻辑
"""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from .base import StorageBase
from .vector_store import VectorStore
from .graph_store import GraphStore
from .metadata_store import MetadataStore

logger = logging.getLogger(__name__)


class DocumentStore(StorageBase):
    """
    文档存储 - 整合多个存储后端
    
    职责：
    - 提供统一的文档 CRUD 接口
    - 协调向量、图谱、元数据存储
    - 确保数据一致性
    
    待实现：从 repository/hybrid_repository.py 提取并重构
    """
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        graph_store: Optional[GraphStore] = None,
        metadata_store: Optional[MetadataStore] = None
    ):
        """
        初始化文档存储
        
        Args:
            vector_store: 向量存储
            graph_store: 图谱存储
            metadata_store: 元数据存储
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.metadata_store = metadata_store
        self._initialized = False
    
    async def initialize(self) -> bool:
        """初始化所有存储后端"""
        try:
            if self.vector_store:
                await self.vector_store.initialize()
            
            if self.graph_store:
                await self.graph_store.initialize()
            
            if self.metadata_store:
                await self.metadata_store.initialize()
            
            self._initialized = True
            logger.info("文档存储初始化成功")
            return True
        
        except Exception as e:
            logger.error(f"文档存储初始化失败: {e}", exc_info=True)
            return False
    
    async def add(self, item: Dict[str, Any]) -> str:
        """
        添加文档
        
        Args:
            item: {
                "doc_id": str,
                "content": str,
                "embedding": List[float],
                "entities": List[str],
                "metadata": Dict
            }
        
        Returns:
            doc_id: 文档 ID
        """
        if not self._initialized:
            await self.initialize()
        
        doc_id = item["doc_id"]
        
        try:
            # 添加到向量存储
            if self.vector_store and "embedding" in item:
                await self.vector_store.add({
                    "doc_id": doc_id,
                    "embedding": item["embedding"]
                })
            
            # 添加到图谱存储
            if self.graph_store and "entities" in item:
                # TODO: 实现图谱添加逻辑
                pass
            
            # 添加到元数据存储
            if self.metadata_store:
                # TODO: 实现元数据添加逻辑
                pass
            
            logger.debug(f"添加文档: {doc_id}")
            return doc_id
        
        except Exception as e:
            logger.error(f"添加文档失败: {doc_id}, {e}", exc_info=True)
            # TODO: 回滚已添加的数据
            raise
    
    async def get(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            item_id: 文档 ID
        
        Returns:
            document: 文档对象
        """
        # TODO: 从元数据存储获取完整文档
        if self.metadata_store:
            return await self.metadata_store.get(item_id)
        return None
    
    async def update(self, item_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新文档
        
        Args:
            item_id: 文档 ID
            updates: 更新内容
        
        Returns:
            success: 是否成功
        """
        try:
            # 更新向量存储
            if self.vector_store and "embedding" in updates:
                await self.vector_store.update(item_id, {
                    "embedding": updates["embedding"]
                })
            
            # 更新图谱存储
            if self.graph_store:
                # TODO: 实现图谱更新逻辑
                pass
            
            # 更新元数据存储
            if self.metadata_store:
                await self.metadata_store.update(item_id, updates)
            
            logger.debug(f"更新文档: {item_id}")
            return True
        
        except Exception as e:
            logger.error(f"更新文档失败: {item_id}, {e}", exc_info=True)
            return False
    
    async def delete(self, item_id: str) -> bool:
        """
        删除文档
        
        Args:
            item_id: 文档 ID
        
        Returns:
            success: 是否成功
        """
        try:
            # 从向量存储删除
            if self.vector_store:
                await self.vector_store.delete(item_id)
            
            # 从图谱存储删除
            if self.graph_store:
                await self.graph_store.delete(item_id)
            
            # 从元数据存储删除
            if self.metadata_store:
                await self.metadata_store.delete(item_id)
            
            logger.debug(f"删除文档: {item_id}")
            return True
        
        except Exception as e:
            logger.error(f"删除文档失败: {item_id}, {e}", exc_info=True)
            return False
    
    async def search(
        self,
        query: Any,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索文档（仅元数据搜索，不包括语义检索）
        
        Args:
            query: 查询条件
            top_k: 返回数量
            filters: 过滤条件
        
        Returns:
            documents: 文档列表
        """
        if self.metadata_store:
            return await self.metadata_store.search(query, top_k, filters)
        return []
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """统计文档数量"""
        if self.metadata_store:
            return await self.metadata_store.count(filters)
        return 0
    
    async def clear(self) -> bool:
        """清空所有存储"""
        try:
            if self.vector_store:
                await self.vector_store.clear()
            
            if self.graph_store:
                await self.graph_store.clear()
            
            if self.metadata_store:
                await self.metadata_store.clear()
            
            logger.info("文档存储已清空")
            return True
        
        except Exception as e:
            logger.error(f"清空文档存储失败: {e}", exc_info=True)
            return False
    
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
