"""
Search Service - 文档检索服务

提供文档检索的业务级服务,基于 CapabilityFactory 注入检索能力

设计理念:
- 通过 CapabilityFactory 获取 HybridRetriever
- 不直接依赖 Foundation 层组件
- 遵循依赖注入和单一职责原则
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from ame.models.domain import Document, SearchResult
from ame.foundation.storage import DocumentStore
from ame.capabilities.retrieval import HybridRetriever, RetrievalResult
from ame.capabilities.factory import CapabilityFactory

logger = logging.getLogger(__name__)


class SearchService:
    """
    文档检索服务
    
    职责:
    - 使用 HybridRetriever 执行智能检索
    - 结果映射和过滤
    - 提供便捷的检索接口
    
    设计:
    - 通过 CapabilityFactory 注入检索能力
    - 利用 advanced pipeline (向量+图谱混合检索)
    - 支持多种检索策略和过滤条件
    """
    
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        document_store: DocumentStore
    ):
        """
        初始化检索服务
        
        Args:
            capability_factory: 能力工厂实例(注入)
            document_store: 文档存储实例
        
        Example:
            >>> factory = CapabilityFactory(...)
            >>> search_service = SearchService(
            ...     capability_factory=factory,
            ...     document_store=doc_store
            ... )
        """
        self.factory = capability_factory
        self.store = document_store
        
        # 使用 factory 创建高级混合检索器
        self.retriever = self.factory.create_retriever(
            pipeline_mode="advanced",  # 向量+图谱混合
            cache_key="knowledge_retriever"
        )
        
        logger.info("SearchService 初始化完成(使用 HybridRetriever)")
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        执行智能文档检索
        
        流程:
        1. 使用 HybridRetriever 执行混合检索(向量+图谱)
        2. 获取完整文档信息
        3. 应用业务过滤器
        4. 构建搜索结果
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件(doc_type, after, before, min_score等)
        
        Returns:
            results: 搜索结果列表
        """
        # 使用 HybridRetriever 执行检索
        retrieval_results = await self.retriever.retrieve(
            query=query,
            top_k=top_k * 2,  # 检索更多候选,后续过滤
            filters=filters
        )
        
        if not retrieval_results:
            return []
        
        # 提取文档 ID
        doc_ids = [r.doc_id for r in retrieval_results if r.doc_id]
        
        # 获取完整文档
        docs_dict = {}
        for doc_id in doc_ids:
            doc = await self.store.get(doc_id)
            if doc:
                docs_dict[doc_id] = doc
        
        # 应用业务过滤器并构建结果
        search_results = []
        
        for r in retrieval_results:
            doc = docs_dict.get(r.doc_id)
            
            if not doc:
                continue
            
            # 应用业务层过滤
            if filters and not self._match_filters(doc, r.score, filters):
                continue
            
            search_results.append(SearchResult(
                doc_id=doc["id"] if isinstance(doc, dict) else doc.id,
                content=r.content,  # 使用检索结果中的内容(可能被截断)
                score=r.score,
                source=r.source,
                metadata=r.metadata or {},
                entities=r.matched_entities or []
            ))
        
        logger.debug(f"检索完成: query='{query[:50]}', 结果数={len(search_results)}")
        
        return search_results[:top_k]
    
    async def search_by_time_range(
        self,
        start_date: datetime,
        end_date: datetime,
        doc_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Document]:
        """
        基于时间范围检索文档
        
        Args:
            start_date: 开始时间
            end_date: 结束时间
            doc_type: 文档类型过滤
            limit: 返回数量限制
        
        Returns:
            documents: 文档列表(按时间降序)
        """
        filters = {
            "after": start_date,
            "before": end_date,
            "limit": limit
        }
        
        if doc_type:
            filters["doc_type"] = doc_type
        
        # TODO: 实现 DocumentStore.search 方法
        return await self.store.search(query=None, top_k=limit, filters=filters)
    
    async def search_by_date(
        self,
        date: datetime,
        doc_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Document]:
        """
        检索指定日期的文档
        
        Args:
            date: 目标日期
            doc_type: 文档类型过滤
            limit: 返回数量限制
        
        Returns:
            documents: 文档列表
        """
        # 计算当日的开始和结束时间
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        return await self.search_by_time_range(
            start_date=start_date,
            end_date=end_date,
            doc_type=doc_type,
            limit=limit
        )
    
    async def search_similar(
        self,
        doc_id: str,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        查找相似文档
        
        Args:
            doc_id: 参考文档ID
            top_k: 返回数量
        
        Returns:
            similar_docs: 相似文档列表
        """
        doc = await self.store.get(doc_id)
        if not doc:
            logger.warning(f"文档不存在: {doc_id}")
            return []
        
        # 使用文档内容进行语义检索
        content = doc["content"] if isinstance(doc, dict) else doc.content
        
        results = await self.search(
            query=content,
            top_k=top_k + 1  # 多检索一个(排除自身)
        )
        
        # 排除自身
        return [r for r in results if r.doc_id != doc_id][:top_k]
    
    def _match_filters(
        self,
        doc: Any,  # 可能是 Document 对象或字典
        score: float,
        filters: Dict[str, Any]
    ) -> bool:
        """
        检查文档是否匹配业务过滤条件
        
        Args:
            doc: 文档对象或字典
            score: 检索分数
            filters: 过滤条件
        
        Returns:
            matched: 是否匹配
        """
        # 统一获取字段
        def get_field(key: str, default=None):
            if isinstance(doc, dict):
                return doc.get(key, default)
            return getattr(doc, key, default)
        
        # 文档类型过滤
        if "doc_type" in filters:
            if get_field("doc_type") != filters["doc_type"]:
                return False
        
        # 时间范围过滤
        timestamp = get_field("timestamp")
        if timestamp:
            if "after" in filters and timestamp < filters["after"]:
                return False
            if "before" in filters and timestamp > filters["before"]:
                return False
        
        # 分数阈值过滤
        if "min_score" in filters and score < filters["min_score"]:
            return False
        
        # 状态过滤
        if "status" in filters:
            if get_field("status") != filters["status"]:
                return False
        
        return True
