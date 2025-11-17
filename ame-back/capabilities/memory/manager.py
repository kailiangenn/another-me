"""
MemoryManager - 记忆管理器实现
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import math

from ame.foundation.embedding import EmbeddingBase
from ame.foundation.storage import VectorStore, MetadataStore
from ame.foundation.utils import now, validate_text

from .base import MemoryBase, MemoryItem


logger = logging.getLogger(__name__)


class MemoryManager(MemoryBase):
    """
    记忆管理器
    
    特性：
    - 向量化存储与检索
    - 时间衰减算法
    - 重要性评分
    - 访问频率追踪
    """
    
    def __init__(
        self,
        embedding: EmbeddingBase,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
        decay_factor: float = 0.99,  # 每天衰减1%
    ):
        """
        Args:
            embedding: 嵌入向量生成器
            vector_store: 向量存储
            metadata_store: 元数据存储
            decay_factor: 时间衰减因子（每天）
        """
        self.embedding = embedding
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.decay_factor = decay_factor
    
    async def store(
        self,
        content: str,
        importance: float = 0.5,
        emotion: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """存储记忆"""
        if not validate_text(content):
            raise ValueError("Invalid content")
        
        if not 0 <= importance <= 1:
            raise ValueError("Importance must be between 0 and 1")
        
        # 生成 ID
        timestamp = now()
        memory_id = f"mem_{timestamp.timestamp()}"
        
        # 生成嵌入向量
        embedding_result = await self.embedding.embed_text(content)
        
        # 存储到向量库
        await self.vector_store.insert(memory_id, embedding_result.vector)
        
        # 存储元数据
        await self.metadata_store.insert(memory_id, {
            "content": content,
            "doc_type": "memory",
            "timestamp": timestamp.isoformat(),
            "importance": importance,
            "emotion": emotion,
            "stored_in_vector": True,
            "metadata": {
                "category": category,
                "tags": tags or [],
                "access_count": 0,
                **(metadata or {})
            }
        })
        
        logger.info(f"Stored memory: {memory_id}")
        return memory_id
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        time_decay: bool = True,
        importance_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[MemoryItem]:
        """检索记忆"""
        if not validate_text(query):
            return []
        
        # 生成查询向量
        embedding_result = await self.embedding.embed_text(query)
        
        # 向量检索
        vector_results = await self.vector_store.search(
            query=embedding_result.vector,
            top_k=top_k * 2,  # 检索更多候选
        )
        
        # 获取元数据
        doc_ids = [r["doc_id"] for r in vector_results]
        metadata_list = await self.metadata_store.get_by_ids(doc_ids)
        metadata_map = {m["id"]: m for m in metadata_list}
        
        # 合并结果并计算最终分数
        memories = []
        for result in vector_results:
            doc_id = result["doc_id"]
            metadata = metadata_map.get(doc_id)
            
            if not metadata:
                continue
            
            # 应用过滤条件
            if filters:
                if "category" in filters and metadata.get("metadata", {}).get("category") != filters["category"]:
                    continue
                if "tags" in filters:
                    mem_tags = set(metadata.get("metadata", {}).get("tags", []))
                    filter_tags = set(filters["tags"])
                    if not mem_tags.intersection(filter_tags):
                        continue
            
            # 重要性过滤
            importance = metadata.get("importance", 0.5)
            if importance < importance_threshold:
                continue
            
            # 计算最终分数
            score = result["score"]
            
            # 应用时间衰减
            if time_decay:
                timestamp_str = metadata.get("timestamp")
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    days_ago = (now() - timestamp).days
                    decay = self.decay_factor ** days_ago
                    score *= decay
            
            # 结合重要性
            score *= (0.5 + 0.5 * importance)
            
            # 创建 MemoryItem
            memory = MemoryItem(
                id=doc_id,
                content=metadata["content"],
                timestamp=datetime.fromisoformat(metadata["timestamp"]),
                importance=importance,
                emotion=metadata.get("emotion"),
                category=metadata.get("metadata", {}).get("category"),
                tags=metadata.get("metadata", {}).get("tags", []),
                metadata=metadata.get("metadata", {}),
                access_count=metadata.get("metadata", {}).get("access_count", 0),
            )
            
            memories.append((score, memory))
        
        # 排序并返回
        memories.sort(key=lambda x: x[0], reverse=True)
        result_memories = [m for _, m in memories[:top_k]]
        
        # 更新访问统计
        for memory in result_memories:
            await self._update_access(memory.id)
        
        return result_memories
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """获取单条记忆"""
        metadata = await self.metadata_store.get(memory_id)
        
        if not metadata:
            return None
        
        memory = MemoryItem(
            id=memory_id,
            content=metadata["content"],
            timestamp=datetime.fromisoformat(metadata["timestamp"]),
            importance=metadata.get("importance", 0.5),
            emotion=metadata.get("emotion"),
            category=metadata.get("metadata", {}).get("category"),
            tags=metadata.get("metadata", {}).get("tags", []),
            metadata=metadata.get("metadata", {}),
            access_count=metadata.get("metadata", {}).get("access_count", 0),
        )
        
        await self._update_access(memory_id)
        return memory
    
    async def update_importance(self, memory_id: str, importance: float) -> bool:
        """更新记忆重要性"""
        if not 0 <= importance <= 1:
            raise ValueError("Importance must be between 0 and 1")
        
        return await self.metadata_store.update(memory_id, {"importance": importance})
    
    async def delete(self, memory_id: str) -> bool:
        """删除记忆"""
        # 从向量库删除
        await self.vector_store.delete(memory_id)
        
        # 从元数据库删除
        return await self.metadata_store.delete(memory_id)
    
    async def _update_access(self, memory_id: str):
        """更新访问统计"""
        metadata = await self.metadata_store.get(memory_id)
        if metadata:
            access_count = metadata.get("metadata", {}).get("access_count", 0) + 1
            metadata["metadata"]["access_count"] = access_count
            metadata["metadata"]["last_access"] = now().isoformat()
            
            await self.metadata_store.update(memory_id, {
                "metadata": metadata["metadata"]
            })
