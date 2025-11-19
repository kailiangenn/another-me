"""
混合检索器 - 结合向量检索和图谱检索

实现RRF(Reciprocal Rank Fusion)融合策略
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass
from loguru import logger
import numpy as np

from .vector_store import VectorStoreBase, SearchResult
from .base import GraphStoreBase
from ..core.models import GraphNode


@dataclass
class HybridSearchResult:
    """混合检索结果"""
    id: str                          # 结果ID
    score: float                     # 融合后的分数
    vector_score: float              # 向量检索分数
    graph_score: float               # 图谱检索分数
    source: str                      # 来源 ("vector", "graph", "both")
    metadata: Dict[str, Any]         # 元数据
    node: Optional[GraphNode] = None # 图节点(如果来自图谱)


class HybridRetriever:
    """
    混合检索器
    
    Features:
    - 向量检索 + 图谱检索
    - RRF融合算法
    - 可配置权重
    - 多样性过滤(MMR)
    """
    
    def __init__(
        self,
        vector_store: VectorStoreBase,
        graph_store: GraphStoreBase,
        vector_weight: float = 0.6,
        graph_weight: float = 0.4,
        rrf_k: int = 60
    ):
        """
        初始化混合检索器
        
        Args:
            vector_store: 向量存储
            graph_store: 图存储
            vector_weight: 向量检索权重
            graph_weight: 图谱检索权重
            rrf_k: RRF融合参数(默认60)
        """
        if abs(vector_weight + graph_weight - 1.0) > 1e-6:
            logger.warning(f"权重之和不为1.0: {vector_weight + graph_weight}, 将自动归一化")
            total = vector_weight + graph_weight
            vector_weight /= total
            graph_weight /= total
        
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight
        self.rrf_k = rrf_k
    
    def set_weights(self, vector_weight: float, graph_weight: float) -> None:
        """
        设置检索权重
        
        Args:
            vector_weight: 向量检索权重
            graph_weight: 图谱检索权重
        """
        total = vector_weight + graph_weight
        self.vector_weight = vector_weight / total
        self.graph_weight = graph_weight / total
        logger.info(f"更新检索权重: 向量={self.vector_weight:.2f}, 图谱={self.graph_weight:.2f}")
    
    async def retrieve(
        self,
        query_vector: np.ndarray,
        query_context: Optional[str] = None,
        k: int = 10,
        vector_k: Optional[int] = None,
        graph_k: Optional[int] = None,
        use_mmr: bool = False,
        lambda_param: float = 0.5
    ) -> List[HybridSearchResult]:
        """
        混合检索
        
        Args:
            query_vector: 查询向量
            query_context: 查询上下文(用于图谱检索)
            k: 最终返回的结果数
            vector_k: 向量检索返回数(默认2*k)
            graph_k: 图谱检索返回数(默认2*k)
            use_mmr: 是否使用MMR多样性过滤
            lambda_param: MMR参数(0-1, 相关性vs多样性)
        
        Returns:
            results: 混合检索结果列表
        """
        vector_k = vector_k or (2 * k)
        graph_k = graph_k or (2 * k)
        
        # 1. 向量检索
        vector_results = await self._vector_retrieve(query_vector, vector_k)
        logger.debug(f"向量检索返回 {len(vector_results)} 个结果")
        
        # 2. 图谱检索
        graph_results = await self._graph_retrieve(query_context, graph_k)
        logger.debug(f"图谱检索返回 {len(graph_results)} 个结果")
        
        # 3. RRF融合
        merged_results = self._rrf_fusion(vector_results, graph_results)
        logger.debug(f"RRF融合后 {len(merged_results)} 个结果")
        
        # 4. 重排序
        merged_results.sort(key=lambda x: x.score, reverse=True)
        
        # 5. MMR多样性过滤(可选)
        if use_mmr and len(merged_results) > k:
            merged_results = self._mmr_rerank(
                merged_results,
                k,
                lambda_param,
                query_vector
            )
        
        return merged_results[:k]
    
    async def _vector_retrieve(
        self,
        query_vector: np.ndarray,
        k: int
    ) -> List[Tuple[str, float, Dict]]:
        """
        向量检索
        
        Returns:
            List of (id, score, metadata)
        """
        try:
            search_results = await self.vector_store.search(
                query_vector=query_vector,
                k=k,
                include_embedding=False
            )
            
            return [(r.id, r.score, r.metadata) for r in search_results]
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []
    
    async def _graph_retrieve(
        self,
        query_context: Optional[str],
        k: int
    ) -> List[Tuple[str, float, Dict, GraphNode]]:
        """
        图谱检索
        
        Args:
            query_context: 查询上下文
            k: 返回数量
        
        Returns:
            List of (id, score, metadata, node)
        """
        if not query_context:
            return []
        
        try:
            # 简单实现: 基于关键词匹配节点
            # 实际应该使用更复杂的图谱查询策略
            nodes = await self.graph_store.find_nodes(limit=k * 2)
            
            # 计算相关性分数(简单文本匹配)
            results = []
            for node in nodes:
                score = self._calculate_graph_relevance(node, query_context)
                if score > 0:
                    results.append((
                        node.node_id,
                        score,
                        node.properties,
                        node
                    ))
            
            # 按分数排序
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:k]
            
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []
    
    def _calculate_graph_relevance(
        self,
        node: GraphNode,
        query: str
    ) -> float:
        """
        计算图节点与查询的相关性
        
        Args:
            node: 图节点
            query: 查询文本
        
        Returns:
            score: 相关性分数(0-1)
        """
        # 简单实现: 关键词匹配
        node_text = str(node.properties.get('content', ''))
        query_lower = query.lower()
        node_lower = node_text.lower()
        
        # 计算Jaccard相似度
        query_words = set(query_lower.split())
        node_words = set(node_lower.split())
        
        if not query_words or not node_words:
            return 0.0
        
        intersection = query_words & node_words
        union = query_words | node_words
        
        return len(intersection) / len(union) if union else 0.0
    
    def _rrf_fusion(
        self,
        vector_results: List[Tuple[str, float, Dict]],
        graph_results: List[Tuple[str, float, Dict, Any]]
    ) -> List[HybridSearchResult]:
        """
        RRF(Reciprocal Rank Fusion)融合
        
        公式: score = sum(1 / (k + rank))
        
        Args:
            vector_results: 向量检索结果
            graph_results: 图谱检索结果
        
        Returns:
            融合后的结果
        """
        # 计算每个结果的RRF分数
        rrf_scores = {}
        
        # 向量检索贡献
        for rank, (result_id, score, metadata) in enumerate(vector_results, start=1):
            if result_id not in rrf_scores:
                rrf_scores[result_id] = {
                    'vector_score': score,
                    'graph_score': 0.0,
                    'vector_rrf': 0.0,
                    'graph_rrf': 0.0,
                    'metadata': metadata,
                    'node': None
                }
            
            rrf_scores[result_id]['vector_rrf'] = 1.0 / (self.rrf_k + rank)
            rrf_scores[result_id]['vector_score'] = score
        
        # 图谱检索贡献
        for rank, (result_id, score, metadata, node) in enumerate(graph_results, start=1):
            if result_id not in rrf_scores:
                rrf_scores[result_id] = {
                    'vector_score': 0.0,
                    'graph_score': score,
                    'vector_rrf': 0.0,
                    'graph_rrf': 0.0,
                    'metadata': metadata,
                    'node': node
                }
            
            rrf_scores[result_id]['graph_rrf'] = 1.0 / (self.rrf_k + rank)
            rrf_scores[result_id]['graph_score'] = score
            rrf_scores[result_id]['node'] = node
        
        # 计算加权融合分数
        hybrid_results = []
        for result_id, scores in rrf_scores.items():
            final_score = (
                self.vector_weight * scores['vector_rrf'] +
                self.graph_weight * scores['graph_rrf']
            )
            
            # 确定来源
            if scores['vector_score'] > 0 and scores['graph_score'] > 0:
                source = "both"
            elif scores['vector_score'] > 0:
                source = "vector"
            else:
                source = "graph"
            
            hybrid_results.append(HybridSearchResult(
                id=result_id,
                score=final_score,
                vector_score=scores['vector_score'],
                graph_score=scores['graph_score'],
                source=source,
                metadata=scores['metadata'],
                node=scores['node']
            ))
        
        return hybrid_results
    
    def _mmr_rerank(
        self,
        results: List[HybridSearchResult],
        k: int,
        lambda_param: float,
        query_vector: np.ndarray
    ) -> List[HybridSearchResult]:
        """
        MMR(Maximal Marginal Relevance)重排序
        
        平衡相关性和多样性
        
        Args:
            results: 检索结果
            k: 返回数量
            lambda_param: 相关性vs多样性权重(0-1)
            query_vector: 查询向量
        
        Returns:
            重排序后的结果
        """
        if len(results) <= k:
            return results
        
        selected = []
        remaining = results.copy()
        
        # 第一个选择最相关的
        if remaining:
            best = max(remaining, key=lambda x: x.score)
            selected.append(best)
            remaining.remove(best)
        
        # 迭代选择剩余的
        while len(selected) < k and remaining:
            best_score = -float('inf')
            best_result = None
            
            for candidate in remaining:
                # 相关性分数
                relevance = candidate.score
                
                # 多样性分数(与已选择结果的最大相似度)
                max_similarity = 0.0
                for selected_result in selected:
                    # 简化: 使用ID相似度作为替代
                    similarity = self._calculate_similarity(
                        candidate.id,
                        selected_result.id
                    )
                    max_similarity = max(max_similarity, similarity)
                
                # MMR分数
                mmr_score = (
                    lambda_param * relevance -
                    (1 - lambda_param) * max_similarity
                )
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_result = candidate
            
            if best_result:
                selected.append(best_result)
                remaining.remove(best_result)
        
        return selected
    
    def _calculate_similarity(self, id1: str, id2: str) -> float:
        """
        计算两个结果的相似度
        
        简化实现: 基于ID字符串相似度
        实际应该使用向量相似度
        """
        # 简单的Jaccard相似度
        set1 = set(id1)
        set2 = set(id2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = set1 & set2
        union = set1 | set2
        
        return len(intersection) / len(union) if union else 0.0
