"""
Document Service - 文档管理服务

提供文档 CRUD 的业务级服务,基于 CapabilityFactory 注入能力

设计理念:
- 不直接依赖 DocumentProcessor
- 使用 Embedding + NER 能力进行文档预处理
- 遵循依赖注入和单一职责原则
"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from ame.models.domain import Document, DocumentType
from ame.foundation.storage import DocumentStore
from ame.foundation.embedding import EmbeddingBase
from ame.foundation.nlp import NERBase
from ame.capabilities.factory import CapabilityFactory

logger = logging.getLogger(__name__)


class DocumentService:
    """
    文档管理服务
    
    职责:
    - 文档的创建、读取、更新、删除
    - 文档预处理(Embedding + NER)
    - 批量操作支持
    
    设计:
    - 通过 CapabilityFactory 获取 Embedding 和 NER 能力
    - 不直接依赖 DocumentProcessor
    - 支持自动预处理和手动处理
    """
    
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        document_store: DocumentStore,
        enable_auto_process: bool = True
    ):
        """
        初始化文档服务
        
        Args:
            capability_factory: 能力工厂实例(注入)
            document_store: 文档存储实例
            enable_auto_process: 是否启用自动预处理
        
        Example:
            >>> factory = CapabilityFactory(...)
            >>> doc_service = DocumentService(
            ...     capability_factory=factory,
            ...     document_store=doc_store
            ... )
        """
        self.factory = capability_factory
        self.store = document_store
        self.enable_auto_process = enable_auto_process
        
        # 从 factory 获取能力
        self.embedding = capability_factory.embedding
        self.ner = capability_factory.ner
        
        logger.info(
            f"DocumentService 初始化完成 "
            f"(自动预处理={enable_auto_process})"
        )
    
    async def create_document(
        self,
        content: str,
        doc_type: DocumentType = DocumentType.RAG_KNOWLEDGE,
        metadata: Optional[Dict[str, Any]] = None,
        auto_process: bool = True
    ) -> str:
        """
        创建文档
        
        流程:
        1. 创建文档对象
        2. 自动预处理(Embedding + NER)
        3. 存储到 DocumentStore
        
        Args:
            content: 文档内容
            doc_type: 文档类型
            metadata: 元数据
            auto_process: 是否自动预处理
        
        Returns:
            doc_id: 创建的文档ID
        """
        # 创建文档对象
        doc_data = {
            "content": content,
            "doc_type": doc_type,
            "source": metadata.get("source", "user_upload") if metadata else "user_upload",
            "timestamp": datetime.now(),
            "metadata": metadata or {}
        }
        
        # 自动预处理
        if auto_process and self.enable_auto_process:
            doc_data = await self._process_document(doc_data)
        
        # 存储
        doc_id = await self.store.add(doc_data)
        
        logger.info(f"创建文档: {doc_id}, 类型={doc_type}")
        
        return doc_id
    
    async def batch_create(
        self,
        documents: List[Dict[str, Any]],
        auto_process: bool = True
    ) -> List[str]:
        """
        批量创建文档
        
        Args:
            documents: 文档数据列表
            auto_process: 是否自动预处理
        
        Returns:
            doc_ids: 创建的文档ID列表
        """
        doc_ids = []
        
        for doc_data in documents:
            doc_id = await self.create_document(
                content=doc_data["content"],
                doc_type=doc_data.get("doc_type", DocumentType.RAG_KNOWLEDGE),
                metadata=doc_data.get("metadata", {}),
                auto_process=auto_process
            )
            doc_ids.append(doc_id)
        
        logger.info(f"批量创建文档: {len(doc_ids)} 个")
        
        return doc_ids
    
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        获取文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            document: 文档对象(字典格式)
        """
        return await self.store.get(doc_id)
    
    async def get_documents(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取文档
        
        Args:
            doc_ids: 文档ID列表
        
        Returns:
            documents: 文档列表
        """
        docs = []
        for doc_id in doc_ids:
            doc = await self.store.get(doc_id)
            if doc:
                docs.append(doc)
        return docs
    
    async def update_document(
        self,
        doc_id: str,
        updates: Dict[str, Any],
        reprocess: bool = False
    ) -> bool:
        """
        更新文档
        
        Args:
            doc_id: 文档 ID
            updates: 更新内容
            reprocess: 是否重新处理(当内容变化时)
        
        Returns:
            success: 是否成功
        """
        # 如果内容变化且需要重新处理
        if reprocess and "content" in updates:
            # 重新生成 embedding 和实体
            processed_updates = await self._process_document({
                "content": updates["content"]
            })
            
            updates["embedding"] = processed_updates.get("embedding")
            updates["entities"] = processed_updates.get("entities", [])
        
        updates["updated_at"] = datetime.now()
        
        return await self.store.update(doc_id, updates)
    
    async def delete_document(self, doc_id: str) -> bool:
        """
        删除文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            success: 是否成功
        """
        success = await self.store.delete(doc_id)
        
        if success:
            logger.info(f"删除文档: {doc_id}")
        
        return success
    
    async def list_documents(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出文档
        
        Args:
            filters: 过滤条件
            limit: 返回数量
            offset: 偏移量
        
        Returns:
            documents: 文档列表
        """
        query_filters = filters or {}
        
        # TODO: 实现 DocumentStore.search 方法
        return await self.store.search(
            query=None,
            top_k=limit,
            filters=query_filters
        )
    
    async def count_documents(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计文档数量
        
        Args:
            filters: 过滤条件
        
        Returns:
            count: 文档数量
        """
        return await self.store.count(filters)
    
    # ==================== 私有方法 ====================
    
    async def _process_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理文档(生成 Embedding + 提取实体)
        
        Args:
            doc_data: 文档数据
        
        Returns:
            processed_data: 处理后的数据(包含 embedding 和 entities)
        """
        content = doc_data.get("content", "")
        
        # 生成 Embedding
        if self.embedding:
            try:
                embed_result = await self.embedding.embed_text(content)
                doc_data["embedding"] = embed_result.vector
                logger.debug(f"生成 Embedding: 维度={len(embed_result.vector)}")
            except Exception as e:
                logger.error(f"生成 Embedding 失败: {e}")
                doc_data["embedding"] = None
        
        # 提取实体
        if self.ner:
            try:
                entities = await self.ner.extract(content)
                doc_data["entities"] = [e.text for e in entities]
                logger.debug(f"提取实体: {len(entities)} 个")
            except Exception as e:
                logger.error(f"提取实体失败: {e}")
                doc_data["entities"] = []
        
        return doc_data
