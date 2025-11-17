"""
HybridRetriever - 混合检索器（Pipeline 封装版）
"""
from typing import List, Optional, Dict, Any
import logging

from ame.foundation.embedding import EmbeddingBase
from ame.foundation.storage import VectorStore, GraphStore
from ame.foundation.nlp.ner import NERBase
from ame.foundation.llm import LLMCallerBase
from ame.foundation.retrieval import VectorRetriever, GraphRetriever
from ame.foundation.utils import validate_text

from .base import RetrieverBase, RetrievalResult, RetrievalStrategy
from .pipeline import RetrievalPipeline
from .stages import (
    VectorRetrievalStage,
    GraphRetrievalStage,
    FusionStage,
    SemanticRerankStage,
    DiversityFilterStage,
    IntentAdaptiveStage,
)


logger = logging.getLogger(__name__)


class HybridRetriever(RetrieverBase):
    """
    混合检索器（Pipeline 封装版）
    
    设计：
    - 不再包含具体检索逻辑，完全委托给 Pipeline
    - 根据 strategy 参数动态构建不同的 Pipeline
    - 简化代码，提高可维护性
    """
    
    def __init__(
        self,
        embedding: EmbeddingBase,
        vector_store: VectorStore,
        graph_store: Optional[GraphStore] = None,
        ner: Optional[NERBase] = None,
        llm: Optional[LLMCallerBase] = None,
        pipeline_mode: str = "advanced",
    ):
        """
        Args:
            embedding: 嵌入向量生成器
            vector_store: 向量存储
            graph_store: 图谱存储（可选）
            ner: 命名实体识别器（可选）
            llm: LLM 调用器（可选，用于语义重排序）
            pipeline_mode: Pipeline 模式 ('basic', 'advanced', 'semantic')
        """
        self.embedding = embedding
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.ner = ner
        self.llm = llm
        self.pipeline_mode = pipeline_mode
        
        # 创建 Foundation 层检索器
        self.vector_retriever = VectorRetriever(
            vector_store=vector_store,
            embedding=embedding
        )
        
        self.graph_retriever = None
        if graph_store and ner:
            self.graph_retriever = GraphRetriever(
                graph_store=graph_store,
                ner=ner,
                enable_multi_hop=True
            )
        
        # 预构建默认 Pipeline
        self.default_pipeline = self._build_pipeline(pipeline_mode)
        
        logger.info(f"HybridRetriever 初始化完成 (mode={pipeline_mode})")
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 10,
        strategy: RetrievalStrategy = RetrievalStrategy.HYBRID,
        rerank: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalResult]:
        """
        检索文档（通过 Pipeline）
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            strategy: 检索策略（用于动态构建 Pipeline）
            rerank: 是否重排序（已集成到 Pipeline 中）
            filters: 过滤条件
        
        Returns:
            检索结果列表
        """
        if not validate_text(query):
            return []
        
        # 根据 strategy 选择或构建 Pipeline
        if strategy == RetrievalStrategy.VECTOR_ONLY:
            pipeline = self._build_vector_only_pipeline()
        elif strategy == RetrievalStrategy.GRAPH_ONLY:
            pipeline = self._build_graph_only_pipeline()
        elif strategy == RetrievalStrategy.ADAPTIVE:
            pipeline = self._build_adaptive_pipeline(query)
        else:  # HYBRID
            pipeline = self.default_pipeline
        
        # 执行 Pipeline
        context = {"filters": filters} if filters else {}
        results = await pipeline.execute(query, top_k, context)
        
        return results
    
    def _build_pipeline(self, mode: str) -> RetrievalPipeline:
        """
        构建 Pipeline
        
        Args:
            mode: 'basic', 'advanced', 'semantic'
        """
        if mode == "basic":
            return self._build_basic_pipeline()
        elif mode == "semantic":
            return self._build_semantic_pipeline()
        else:  # advanced
            return self._build_advanced_pipeline()
    
    def _build_basic_pipeline(self) -> RetrievalPipeline:
        """Basic: Vector → Rerank"""
        pipeline = RetrievalPipeline(name="basic")
        pipeline.add_stage(VectorRetrievalStage(self.vector_retriever, weight=1.0))
        pipeline.add_stage(SemanticRerankStage(llm_caller=self.llm, use_llm=False))
        return pipeline
    
    def _build_advanced_pipeline(self) -> RetrievalPipeline:
        """Advanced: Vector + Graph → Fusion → Rerank"""
        pipeline = RetrievalPipeline(name="advanced")
        pipeline.add_stage(VectorRetrievalStage(self.vector_retriever, weight=0.6))
        
        if self.graph_retriever:
            pipeline.add_stage(GraphRetrievalStage(self.graph_retriever, weight=0.4))
            pipeline.add_stage(FusionStage(fusion_method="rrf"))
        
        pipeline.add_stage(SemanticRerankStage(llm_caller=self.llm, use_llm=False))
        return pipeline
    
    def _build_semantic_pipeline(self) -> RetrievalPipeline:
        """Semantic: Vector → Intent → Rerank → Diversity"""
        pipeline = RetrievalPipeline(name="semantic")
        pipeline.add_stage(VectorRetrievalStage(self.vector_retriever, weight=1.0))
        pipeline.add_stage(IntentAdaptiveStage(ner_extractor=self.ner))
        pipeline.add_stage(SemanticRerankStage(llm_caller=self.llm, use_llm=False))
        pipeline.add_stage(DiversityFilterStage(lambda_param=0.7))
        return pipeline
    
    def _build_vector_only_pipeline(self) -> RetrievalPipeline:
        """Vector Only: 仅向量检索"""
        pipeline = RetrievalPipeline(name="vector_only")
        pipeline.add_stage(VectorRetrievalStage(self.vector_retriever, weight=1.0))
        return pipeline
    
    def _build_graph_only_pipeline(self) -> RetrievalPipeline:
        """Graph Only: 仅图谱检索"""
        if not self.graph_retriever:
            logger.warning("Graph retriever not available, fallback to vector")
            return self._build_vector_only_pipeline()
        
        pipeline = RetrievalPipeline(name="graph_only")
        pipeline.add_stage(GraphRetrievalStage(self.graph_retriever, weight=1.0))
        return pipeline
    
    def _build_adaptive_pipeline(self, query: str) -> RetrievalPipeline:
        """
        Adaptive: 根据查询特征选择 Pipeline
        
        规则：
        - 实体丰富 → advanced（graph 权重高）
        - 语义查询 → semantic
        """
        # 简化版：检查是否包含实体
        has_entities = False
        if self.ner:
            # 这里简化处理，实际可以异步调用
            import asyncio
            try:
                entities = asyncio.run(self.ner.extract(query))
                has_entities = len(entities) > 0
            except:
                pass
        
        if has_entities and self.graph_retriever:
            return self._build_advanced_pipeline()
        else:
            return self._build_semantic_pipeline()
