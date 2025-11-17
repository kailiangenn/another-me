"""
记忆回顾服务
职责: 记忆检索、时间线生成

设计: 通过 CapabilityFactory 注入能力
"""
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from ame.capabilities.factory import CapabilityFactory
from ame.capabilities.retrieval import HybridRetriever
from ame.models.domain import Document

logger = logging.getLogger(__name__)


class MemoryService:
    """记忆回顾服务"""
    
    def __init__(self, capability_factory: CapabilityFactory):
        self.retriever = capability_factory.create_retriever(
            pipeline_mode="semantic",
            cache_key="memory_retriever"
        )
        logger.info("MemoryService 初始化完成")
    
    async def recall(
        self,
        query: str,
        user_id: str,
        time_range: Optional[timedelta] = None,
        top_k: int = 10
    ) -> List[Document]:
        """
        回忆检索
        
        Args:
            query: 查询文本
            user_id: 用户ID
            time_range: 时间范围（可选）
            top_k: 返回数量
        
        Returns:
            memories: 相关记忆列表
        """
        filters = {"user_id": user_id, "doc_type": "life"}
        
        results = await self.retriever.retrieve(
            query=query,
            top_k=top_k,
            filters=filters
        )
        
        if time_range:
            cutoff_date = datetime.now() - time_range
            results = [
                r for r in results
                if hasattr(r, 'timestamp') and r.timestamp >= cutoff_date
            ]
        
        return results
    
    async def get_timeline(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Document]:
        """
        获取时间线记忆
        
        Args:
            user_id: 用户ID
            start_date: 开始时间
            end_date: 结束时间
        
        Returns:
            memories: 时间线记忆列表
        """
        filters = {
            "user_id": user_id,
            "start_time": start_date,
            "end_time": end_date
        }
        
        results = await self.retriever.retrieve(
            query="",
            top_k=100,
            filters=filters
        )
        
        return sorted(results, key=lambda x: x.timestamp if hasattr(x, 'timestamp') else datetime.now())
