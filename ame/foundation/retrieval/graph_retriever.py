"""
Foundation Layer - Graph Retriever

基于图谱的检索器（原子能力）
"""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from .base import RetrieverBase, RetrievalResult
from ame.foundation.storage import GraphStore
from ame.foundation.nlp.ner import NERBase

logger = logging.getLogger(__name__)


class GraphRetriever(RetrieverBase):
    """
    图谱检索器（Foundation 层原子能力）
    
    特性：
    - 实体关系检索
    - 多跳推理扩展
    - 关系权重计算
    """
    
    def __init__(
        self,
        graph_store: GraphStore,
        ner: NERBase,
        enable_multi_hop: bool = True,
        max_hops: int = 2
    ):
        """
        初始化图谱检索器
        
        Args:
            graph_store: 图谱存储实例
            ner: NER 服务（用于提取查询实体）
            enable_multi_hop: 是否启用多跳推理
            max_hops: 最大跳数（默认 2）
        """
        self.graph_store = graph_store
        self.ner = ner
        self.enable_multi_hop = enable_multi_hop
        self.max_hops = max_hops
        
        logger.debug(
            f"GraphRetriever 初始化完成 (多跳: {enable_multi_hop}, 最大跳数: {max_hops})"
        )
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[RetrievalResult]:
        """
        图谱检索
        
        流程:
        1. NER 提取查询实体
        2. Falkor 查询相关文档
        3. 多跳推理（可选）
        4. 返回结果
        
        Args:
            query: 查询文本
            top_k: 返回前 K 个结果
            filters: 过滤条件（可选）
            **kwargs: 扩展参数
                - enable_multi_hop: 是否启用多跳推理（覆盖默认值）
                - max_hops: 最大跳数（覆盖默认值）
        
        Returns:
            检索结果列表
        """
        if not query or not query.strip():
            logger.warning("GraphRetriever: 查询为空")
            return []
        
        try:
            # 1. 提取实体
            entities = await self._extract_entities(query)
            
            if not entities:
                logger.debug(f"GraphRetriever: 未从查询中提取到实体: {query}")
                return []
            
            logger.debug(f"GraphRetriever: 提取到 {len(entities)} 个实体: {entities}")
            
            # 2. 图谱检索
            graph_results = await self.graph_store.search_by_entities(
                entities=entities,
                top_k=top_k * 2  # 召回更多，后续过滤
            )
            
            if not graph_results:
                logger.debug("GraphRetriever: 图谱检索未找到结果")
                return []
            
            # 3. 多跳推理（扩展相关文档）
            enable_multi_hop = kwargs.get("enable_multi_hop", self.enable_multi_hop)
            if enable_multi_hop:
                max_hops = kwargs.get("max_hops", self.max_hops)
                graph_results = await self._expand_multi_hop(
                    graph_results,
                    max_hops=max_hops
                )
            
            # 4. 转换为 RetrievalResult
            results = self._convert_to_results(graph_results)
            
            # 5. 排序并返回 top_k
            results.sort(key=lambda r: r.score, reverse=True)
            
            logger.debug(f"GraphRetriever: 检索到 {len(results[:top_k])} 个结果")
            
            return results[:top_k]
            
        except Exception as e:
            logger.error(f"GraphRetriever 检索失败: {e}", exc_info=True)
            return []
    
    async def _extract_entities(self, text: str) -> List[str]:
        """
        实体提取
        
        Args:
            text: 输入文本
        
        Returns:
            实体名列表
        """
        try:
            entity_objects = await self.ner.extract(text)
            # 转换为字符串列表
            return [entity.text for entity in entity_objects]
        except Exception as e:
            logger.error(f"GraphRetriever 实体提取失败: {e}")
            return []
    
    async def _expand_multi_hop(
        self,
        initial_results: List[Dict],
        max_hops: int = 2
    ) -> List[Dict]:
        """
        多跳推理扩展
        
        Args:
            initial_results: 初始检索结果
            max_hops: 最大跳数
        
        Returns:
            扩展后的结果
        """
        expanded = list(initial_results)
        existing_doc_ids = {r["doc_id"] for r in initial_results if "doc_id" in r}
        
        # 取前 5 个结果进行扩展（避免性能问题）
        top_results = initial_results[:5]
        
        for result in top_results:
            doc_id = result.get("doc_id")
            if not doc_id:
                continue
            
            try:
                # 查找相关文档
                related_docs = await self.graph_store.find_related_docs(
                    doc_id=doc_id,
                    max_hops=max_hops,
                    limit=10
                )
                
                # 添加新文档
                for related in related_docs:
                    related_doc_id = related.get("doc_id")
                    
                    if related_doc_id and related_doc_id not in existing_doc_ids:
                        # 计算衰减分数
                        distance = related.get("distance", 1)
                        decay_factor = 0.7 ** distance  # 距离越远衰减越多
                        
                        expanded.append({
                            "doc_id": related_doc_id,
                            "score": result.get("score", 0.5) * decay_factor,
                            "source": "graph_expanded",
                            "hop_distance": distance,
                            "base_doc_id": doc_id
                        })
                        
                        existing_doc_ids.add(related_doc_id)
            
            except Exception as e:
                logger.error(f"GraphRetriever 多跳推理失败 (doc_id={doc_id}): {e}")
                continue
        
        logger.debug(
            f"GraphRetriever: 多跳推理扩展 {len(initial_results)} -> {len(expanded)} 个结果"
        )
        
        return expanded
    
    def _convert_to_results(
        self,
        graph_results: List[Dict]
    ) -> List[RetrievalResult]:
        """
        转换为 RetrievalResult 对象
        
        Args:
            graph_results: 图谱检索原始结果
        
        Returns:
            RetrievalResult 列表
        """
        results = []
        
        for r in graph_results:
            doc_id = r.get("doc_id")
            if not doc_id:
                continue
            
            # 构建元数据
            metadata = {
                "doc_id": doc_id,
                "source": r.get("source", "graph"),
            }
            
            # 添加可选字段
            if "matched_entities" in r:
                metadata["matched_entities"] = r["matched_entities"]
            
            if "hop_distance" in r:
                metadata["hop_distance"] = r["hop_distance"]
            
            if "base_doc_id" in r:
                metadata["base_doc_id"] = r["base_doc_id"]
            
            if "shared_entities" in r:
                metadata["shared_entities"] = r["shared_entities"]
            
            # 内容在后续从 Repository 获取
            content = r.get("content", "")
            
            results.append(RetrievalResult(
                content=content,
                metadata=metadata,
                score=r.get("score", 0.5),
                source=metadata["source"]
            ))
        
        return results
    
    def get_name(self) -> str:
        """获取检索器名称"""
        return "GraphRetriever"
