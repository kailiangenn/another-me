"""
Capability Factory - 能力工厂

设计理念:
- 使用工厂模式构建能力实例
- 支持能力的灵活组合
- 便于扩展新能力
- 提供预设的能力组合方案
"""

from typing import Optional, Dict, Any, List
from enum import Enum

# Foundation Layer
from ame.foundation.storage import VectorStoreBase, GraphStoreBase, DocumentStoreBase
from ame.foundation.llm import OpenAICaller
from ame.foundation.nlp import NERBase
from ame.foundation.embedding import EmbeddingBase

# Capabilities Layer
from .retrieval import HybridRetriever
from .analysis import DataAnalyzer, InsightGenerator
from .generation import RAGGenerator, StyleGenerator
from .memory import MemoryManager
from .intent import IntentRecognizer


class CapabilityType(Enum):
    """能力类型枚举"""
    RETRIEVAL = "retrieval"
    ANALYSIS = "analysis"
    GENERATION = "generation"
    MEMORY = "memory"
    INTENT = "intent"


class CapabilityFactory:
    """
    能力工厂 - 构建和组合各种能力
    
    设计优势:
    1. 集中管理依赖注入
    2. 提供预设组合方案
    3. 便于单元测试（可注入 mock）
    4. 支持灵活扩展
    """
    
    def __init__(
        self,
        # Foundation 层依赖
        vector_store: Optional[VectorStoreBase] = None,
        graph_store: Optional[GraphStoreBase] = None,
        document_store: Optional[DocumentStoreBase] = None,
        llm_caller: Optional[OpenAICaller] = None,
        ner_service: Optional[NERBase] = None,
        embedding_function: Optional[EmbeddingBase] = None,
    ):
        """
        初始化能力工厂
        
        Args:
            vector_store: 向量存储（用于检索、记忆）
            graph_store: 图存储（用于关系检索）
            document_store: 文档存储（用于记忆管理）
            llm_caller: LLM 调用器（用于生成、分析、意图识别）
            ner_service: NER 服务（用于实体提取）
            embedding_function: Embedding 函数（用于向量化）
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.document_store = document_store
        self.llm = llm_caller
        self.ner = ner_service
        self.embedding = embedding_function
        
        # 缓存已创建的能力实例
        self._capabilities_cache: Dict[str, Any] = {}
    
    # ==================== 单一能力构建方法 ====================
    
    def create_retriever(
        self,
        pipeline_mode: str = "advanced",
        cache_key: Optional[str] = None
    ) -> HybridRetriever:
        """
        创建混合检索器（基于 Pipeline）
        
        Args:
            pipeline_mode: Pipeline 模式 ('basic', 'advanced', 'semantic')
            cache_key: 缓存键（提供后会复用实例）
        
        Returns:
            HybridRetriever 实例
        """
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        retriever = HybridRetriever(
            embedding=self.embedding,
            vector_store=self.vector_store,
            graph_store=self.graph_store,
            ner=self.ner,
            llm=self.llm,
            pipeline_mode=pipeline_mode
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = retriever
        
        return retriever
    
    def create_memory_manager(
        self,
        cache_key: Optional[str] = None
    ) -> MemoryManager:
        """创建记忆管理器"""
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        memory_manager = MemoryManager(
            document_store=self.document_store,
            vector_store=self.vector_store,
            embedding_function=self.embedding
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = memory_manager
        
        return memory_manager
    
    def create_intent_recognizer(
        self,
        cache_key: Optional[str] = None
    ) -> IntentRecognizer:
        """创建意图识别器"""
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        intent_recognizer = IntentRecognizer(
            llm_caller=self.llm,
            embedding_function=self.embedding
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = intent_recognizer
        
        return intent_recognizer
    
    def create_data_analyzer(
        self,
        with_retriever: bool = False,
        cache_key: Optional[str] = None
    ) -> DataAnalyzer:
        """
        创建数据分析器
        
        Args:
            with_retriever: 是否注入检索器（用于增强分析）
            cache_key: 缓存键
        """
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        retriever = None
        if with_retriever:
            retriever = self.create_retriever(cache_key="default_retriever")
        
        analyzer = DataAnalyzer(
            llm_caller=self.llm,
            retriever=retriever
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = analyzer
        
        return analyzer
    
    def create_insight_generator(
        self,
        cache_key: Optional[str] = None
    ) -> InsightGenerator:
        """创建洞察生成器"""
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        generator = InsightGenerator(
            llm_caller=self.llm
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = generator
        
        return generator
    
    def create_rag_generator(
        self,
        cache_key: Optional[str] = None
    ) -> RAGGenerator:
        """创建 RAG 生成器"""
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        retriever = self.create_retriever(cache_key="default_retriever")
        
        generator = RAGGenerator(
            llm_caller=self.llm,
            retriever=retriever
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = generator
        
        return generator
    
    def create_style_generator(
        self,
        with_retriever: bool = True,
        cache_key: Optional[str] = None
    ) -> StyleGenerator:
        """
        创建风格化生成器
        
        Args:
            with_retriever: 是否注入检索器（用于历史风格参考）
            cache_key: 缓存键
        """
        if cache_key and cache_key in self._capabilities_cache:
            return self._capabilities_cache[cache_key]
        
        retriever = None
        if with_retriever:
            retriever = self.create_retriever(cache_key="default_retriever")
        
        generator = StyleGenerator(
            llm_caller=self.llm,
            retriever=retriever
        )
        
        if cache_key:
            self._capabilities_cache[cache_key] = generator
        
        return generator
    
    # ==================== 预设能力组合方案 ====================
    
    def create_work_capability_bundle(self) -> Dict[str, Any]:
        """
        创建工作场景能力包
        
        包含:
        - 数据分析器（带检索增强）
        - RAG 生成器
        - 记忆管理器
        - 风格化生成器
        """
        return {
            "analyzer": self.create_data_analyzer(with_retriever=True, cache_key="work_analyzer"),
            "rag_generator": self.create_rag_generator(cache_key="work_rag"),
            "memory_manager": self.create_memory_manager(cache_key="work_memory"),
            "style_generator": self.create_style_generator(with_retriever=True, cache_key="work_style")
        }
    
    def create_life_capability_bundle(self) -> Dict[str, Any]:
        """
        创建生活场景能力包
        
        包含:
        - 数据分析器
        - 记忆管理器
        - 风格化生成器（温暖风格）
        - RAG 生成器
        """
        return {
            "analyzer": self.create_data_analyzer(with_retriever=False, cache_key="life_analyzer"),
            "memory_manager": self.create_memory_manager(cache_key="life_memory"),
            "style_generator": self.create_style_generator(with_retriever=True, cache_key="life_style"),
            "rag_generator": self.create_rag_generator(cache_key="life_rag")
        }
    
    def create_conversation_capability_bundle(self) -> Dict[str, Any]:
        """
        创建对话场景能力包
        
        包含:
        - 意图识别器
        - 记忆管理器
        - 检索器
        - RAG 生成器
        """
        return {
            "intent_recognizer": self.create_intent_recognizer(cache_key="conversation_intent"),
            "memory_manager": self.create_memory_manager(cache_key="conversation_memory"),
            "retriever": self.create_retriever(use_vector=True, use_graph=True, cache_key="conversation_retriever"),
            "rag_generator": self.create_rag_generator(cache_key="conversation_rag")
        }
    
    def create_knowledge_capability_bundle(self) -> Dict[str, Any]:
        """
        创建知识场景能力包
        
        包含:
        - 混合检索器（向量+图谱）
        - 数据分析器
        - 洞察生成器
        - 记忆管理器
        """
        return {
            "retriever": self.create_retriever(use_vector=True, use_graph=True, cache_key="knowledge_retriever"),
            "analyzer": self.create_data_analyzer(with_retriever=True, cache_key="knowledge_analyzer"),
            "insight_generator": self.create_insight_generator(cache_key="knowledge_insight"),
            "memory_manager": self.create_memory_manager(cache_key="knowledge_memory")
        }
    
    # ==================== 自定义能力组合 ====================
    
    def create_custom_bundle(
        self,
        capability_types: List[CapabilityType],
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        创建自定义能力组合
        
        Args:
            capability_types: 需要的能力类型列表
            config: 每个能力的配置（可选）
                例如: {"retrieval": {"use_graph": True}, "analyzer": {"with_retriever": True}}
        
        Returns:
            能力实例字典
        
        Example:
            >>> factory.create_custom_bundle(
            ...     capability_types=[CapabilityType.RETRIEVAL, CapabilityType.GENERATION],
            ...     config={"retrieval": {"use_graph": True}}
            ... )
        """
        config = config or {}
        bundle = {}
        
        for cap_type in capability_types:
            if cap_type == CapabilityType.RETRIEVAL:
                cfg = config.get("retrieval", {})
                bundle["retriever"] = self.create_retriever(**cfg)
            
            elif cap_type == CapabilityType.ANALYSIS:
                cfg = config.get("analysis", {})
                bundle["analyzer"] = self.create_data_analyzer(**cfg)
                bundle["insight_generator"] = self.create_insight_generator()
            
            elif cap_type == CapabilityType.GENERATION:
                cfg = config.get("generation", {})
                bundle["rag_generator"] = self.create_rag_generator()
                bundle["style_generator"] = self.create_style_generator(**cfg)
            
            elif cap_type == CapabilityType.MEMORY:
                bundle["memory_manager"] = self.create_memory_manager()
            
            elif cap_type == CapabilityType.INTENT:
                bundle["intent_recognizer"] = self.create_intent_recognizer()
        
        return bundle
    
    def clear_cache(self):
        """清空能力缓存"""
        self._capabilities_cache.clear()
