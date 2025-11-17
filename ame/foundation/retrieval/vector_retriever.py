"""
Foundation Layer - Vector Retriever

基于向量相似度的检索器（原子能力）
"""

import logging
from typing import List, Dict, Any, Optional

from .base import RetrieverBase, RetrievalResult
from ame.foundation.storage import VectorStore
from ame.foundation.embedding import EmbeddingBase

logger = logging.getLogger(__name__)


class VectorRetriever(RetrieverBase):
    """
    向量检索器（Foundation 层原子能力）
    
    特性：
    - 原子化：仅负责向量相似度检索
    - 无状态：不包含业务逻辑
    - 高性能：直接调用 VectorStore
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding: EmbeddingBase
    ):
        """
        初始化向量检索器
        
        Args:
            vector_store: 向量存储实例
            embedding: 嵌入向量生成器
        """
        self.vector_store = vector_store
        self.embedding = embedding
        
        logger.debug("VectorRetriever 初始化完成")
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        向量检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            filters: 过滤条件（如时间范围、来源等）
            **kwargs: 其他参数
                - min_score: 最小相似度阈值
        
        Returns:
            检索结果列表
        """
        if not query or not query.strip():
            logger.warning("VectorRetriever: 查询为空")
            return []
        
        try:
            # 1. 生成查询向量
            embedding_result = await self.embedding.embed_text(query)
            
            # 2. Faiss 检索
            vector_results = await self.vector_store.search(
                query=embedding_result.vector,
                top_k=top_k,
                filters=filters
            )
            
            # 3. 转换为统一格式
            results = []
            for r in vector_results:
                # 获取文档内容
                content = r.get("content", "")
                
                # 构建元数据
                metadata = {
                    "doc_id": r.get("doc_id", ""),
                    **r.get("metadata", {})
                }
                
                results.append(RetrievalResult(
                    content=content,
                    metadata=metadata,
                    score=r.get("score", 0.0),
                    source="vector"
                ))
            
            # 4. 应用最小分数过滤
            min_score = kwargs.get("min_score", 0.0)
            if min_score > 0:
                results = [r for r in results if r.score >= min_score]
            
            logger.debug(f"VectorRetriever: 检索到 {len(results)} 个结果")
            
            return results
            
        except Exception as e:
            logger.error(f"VectorRetriever 检索失败: {e}", exc_info=True)
            return []
    
    def get_name(self) -> str:
        """获取检索器名称"""
        return "VectorRetriever"
