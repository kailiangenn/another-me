"""
能力工厂 - 统一的能力创建和管理中心

遵循设计规范:
- Service层只能依赖CapabilityFactory，不能直接使用Foundation层组件
- 支持能力实例缓存，提升性能
- 提供预设配置和自定义组合能力
"""

from typing import Dict, Any, Optional
from loguru import logger

# Foundation imports
from ame.foundation.llm import LLMCallerBase, OpenAICaller
from ame.foundation.storage import GraphStoreBase, FalkorDBStore
from ame.foundation.nlp import (
    IntentRecognizer,
    EntityExtractor,
    EmotionAnalyzer,
    Summarizer,
)
from ame.foundation.algorithm import TodoSorter

# Capability imports
from .life import (
    ContextRetriever,
    DialogueGenerator,
    MemoryExtractor,
)
from .work import (
    DocumentParser,
    ProjectAnalyzer,
    TodoParser,
    TodoManager,
    PatternAnalyzer,
    AdviceGenerator,
)


class CapabilityFactory:
    """能力工厂
    
    提供统一的能力创建接口，支持：
    1. 单一能力构建
    2. 预设能力包
    3. 自定义组合
    4. 实例缓存复用
    """
    
    def __init__(self):
        """初始化能力工厂"""
        self._cache: Dict[str, Any] = {}
        logger.debug("能力工厂初始化完成")
    
    # ========== Foundation Layer - LLM ==========
    
    def create_llm_caller(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> LLMCallerBase:
        """创建LLM调用器
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            base_url: API基础URL
            cache_key: 缓存键（如果提供，会尝试复用已有实例）
            **kwargs: 其他OpenAI参数
            
        Returns:
            LLM调用器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的LLM调用器: {cache_key}")
            return self._cache[cache_key]
        
        caller = OpenAICaller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs
        )
        
        if cache_key:
            self._cache[cache_key] = caller
            logger.debug(f"缓存LLM调用器: {cache_key}")
        
        return caller
    
    # ========== Foundation Layer - Storage ==========
    
    def create_graph_store(
        self,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "ame_graph",
        password: Optional[str] = None,
        cache_key: Optional[str] = None,
        **kwargs
    ) -> GraphStoreBase:
        """创建图存储
        
        Args:
            host: FalkorDB主机
            port: FalkorDB端口
            graph_name: 图名称
            password: 密码
            cache_key: 缓存键
            **kwargs: 其他参数
            
        Returns:
            图存储实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的图存储: {cache_key}")
            return self._cache[cache_key]
        
        store = FalkorDBStore(
            host=host,
            port=port,
            graph_name=graph_name,
            password=password,
            **kwargs
        )
        
        if cache_key:
            self._cache[cache_key] = store
            logger.debug(f"缓存图存储: {cache_key}")
        
        return store
    
    # ========== Foundation Layer - NLP ==========
    
    def create_intent_recognizer(
        self,
        llm_caller: Optional[LLMCallerBase] = None,
        cache_key: Optional[str] = None
    ) -> IntentRecognizer:
        """创建意图识别器
        
        Args:
            llm_caller: LLM调用器（可选，用于增强识别）
            cache_key: 缓存键
            
        Returns:
            意图识别器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的意图识别器: {cache_key}")
            return self._cache[cache_key]
        
        recognizer = IntentRecognizer(llm_caller=llm_caller)
        
        if cache_key:
            self._cache[cache_key] = recognizer
        
        return recognizer
    
    def create_entity_extractor(
        self,
        llm_caller: Optional[LLMCallerBase] = None,
        enable_jieba: bool = True,
        cache_key: Optional[str] = None
    ) -> EntityExtractor:
        """创建实体提取器
        
        Args:
            llm_caller: LLM调用器
            enable_jieba: 是否启用jieba分词
            cache_key: 缓存键
            
        Returns:
            实体提取器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的实体提取器: {cache_key}")
            return self._cache[cache_key]
        
        extractor = EntityExtractor(
            llm_caller=llm_caller,
            enable_jieba=enable_jieba
        )
        
        if cache_key:
            self._cache[cache_key] = extractor
        
        return extractor
    
    def create_emotion_analyzer(
        self,
        llm_caller: Optional[LLMCallerBase] = None,
        cache_key: Optional[str] = None
    ) -> EmotionAnalyzer:
        """创建情感分析器
        
        Args:
            llm_caller: LLM调用器
            cache_key: 缓存键
            
        Returns:
            情感分析器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的情感分析器: {cache_key}")
            return self._cache[cache_key]
        
        analyzer = EmotionAnalyzer(llm_caller=llm_caller)
        
        if cache_key:
            self._cache[cache_key] = analyzer
        
        return analyzer
    
    def create_summarizer(
        self,
        llm_caller: LLMCallerBase,
        entity_extractor: Optional[EntityExtractor] = None,
        emotion_analyzer: Optional[EmotionAnalyzer] = None,
        cache_key: Optional[str] = None
    ) -> Summarizer:
        """创建摘要生成器
        
        Args:
            llm_caller: LLM调用器（必需）
            entity_extractor: 实体提取器（可选）
            emotion_analyzer: 情感分析器（可选）
            cache_key: 缓存键
            
        Returns:
            摘要生成器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的摘要生成器: {cache_key}")
            return self._cache[cache_key]
        
        summarizer = Summarizer(
            llm_caller=llm_caller,
            entity_extractor=entity_extractor,
            emotion_analyzer=emotion_analyzer
        )
        
        if cache_key:
            self._cache[cache_key] = summarizer
        
        return summarizer
    
    # ========== Foundation Layer - Algorithm ==========
    
    def create_todo_sorter(
        self,
        cache_key: Optional[str] = None
    ) -> TodoSorter:
        """创建待办排序器
        
        Args:
            cache_key: 缓存键
            
        Returns:
            待办排序器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的待办排序器: {cache_key}")
            return self._cache[cache_key]
        
        sorter = TodoSorter()
        
        if cache_key:
            self._cache[cache_key] = sorter
        
        return sorter
    
    # ========== Capability Layer - Test Capabilities ==========
    
    def create_llm_test_capability(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        **kwargs
    ):
        """创建LLM测试能力
        
        Args:
            api_key: OpenAI API密钥
            model: 模型名称
            base_url: API基础URL
            **kwargs: 其他参数
            
        Returns:
            LLM测试器
        """
        from ame.service.connect.test_llm import LLMTester
        
        llm_caller = self.create_llm_caller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            **kwargs
        )
        
        return LLMTester(llm_caller)
    
    def create_storage_test_capability(
        self,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "test_graph",
        password: Optional[str] = None,
        **kwargs
    ):
        """创建Storage测试能力
        
        Args:
            host: FalkorDB主机
            port: FalkorDB端口
            graph_name: 图名称
            password: 密码
            **kwargs: 其他参数
            
        Returns:
            Storage测试器
        """
        from ame.service.connect.test_storage import StorageTester
        
        graph_store = self.create_graph_store(
            host=host,
            port=port,
            graph_name=graph_name,
            password=password,
            **kwargs
        )
        
        return StorageTester(graph_store)
    
    # ========== Capability Layer - NLP Capability Package ==========
    
    def create_nlp_capability_package(
        self,
        llm_caller: LLMCallerBase,
        enable_entity_extraction: bool = True,
        enable_emotion_analysis: bool = True,
        cache_prefix: str = "nlp"
    ) -> Dict[str, Any]:
        """创建NLP能力包（预设组合）
        
        包含：意图识别、实体提取、情感分析、摘要生成
        
        Args:
            llm_caller: LLM调用器
            enable_entity_extraction: 是否启用实体提取
            enable_emotion_analysis: 是否启用情感分析
            cache_prefix: 缓存键前缀
            
        Returns:
            NLP能力字典
        """
        package = {
            "intent_recognizer": self.create_intent_recognizer(
                llm_caller=llm_caller,
                cache_key=f"{cache_prefix}_intent"
            )
        }
        
        if enable_entity_extraction:
            package["entity_extractor"] = self.create_entity_extractor(
                llm_caller=llm_caller,
                enable_jieba=True,
                cache_key=f"{cache_prefix}_entity"
            )
        
        if enable_emotion_analysis:
            package["emotion_analyzer"] = self.create_emotion_analyzer(
                llm_caller=llm_caller,
                cache_key=f"{cache_prefix}_emotion"
            )
        
        # 摘要生成器（依赖上述组件）
        package["summarizer"] = self.create_summarizer(
            llm_caller=llm_caller,
            entity_extractor=package.get("entity_extractor"),
            emotion_analyzer=package.get("emotion_analyzer"),
            cache_key=f"{cache_prefix}_summarizer"
        )
        
        logger.info(f"创建NLP能力包完成，包含 {len(package)} 个能力")
        return package
    
    # ========== Capability Layer - Life Capabilities ==========
    
    def create_context_retriever(
        self,
        graph_store: GraphStoreBase,
        cache_key: Optional[str] = None
    ) -> ContextRetriever:
        """创建上下文检索器
        
        Args:
            graph_store: 图存储实例
            cache_key: 缓存键
            
        Returns:
            上下文检索器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的上下文检索器: {cache_key}")
            return self._cache[cache_key]
        
        retriever = ContextRetriever(graph_store=graph_store)
        
        if cache_key:
            self._cache[cache_key] = retriever
        
        return retriever
    
    def create_dialogue_generator(
        self,
        llm_caller: LLMCallerBase,
        cache_key: Optional[str] = None
    ) -> DialogueGenerator:
        """创建对话生成器
        
        Args:
            llm_caller: LLM调用器
            cache_key: 缓存键
            
        Returns:
            对话生成器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的对话生成器: {cache_key}")
            return self._cache[cache_key]
        
        generator = DialogueGenerator(llm_caller=llm_caller)
        
        if cache_key:
            self._cache[cache_key] = generator
        
        return generator
    
    def create_memory_extractor(
        self,
        graph_store: GraphStoreBase,
        summarizer: Summarizer,
        cache_key: Optional[str] = None
    ) -> MemoryExtractor:
        """创建记忆提取器
        
        Args:
            graph_store: 图存储实例
            summarizer: 摘要生成器
            cache_key: 缓存键
            
        Returns:
            记忆提取器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的记忆提取器: {cache_key}")
            return self._cache[cache_key]
        
        extractor = MemoryExtractor(
            graph_store=graph_store,
            summarizer=summarizer
        )
        
        if cache_key:
            self._cache[cache_key] = extractor
        
        return extractor
    
    def create_life_capability_package(
        self,
        llm_caller: LLMCallerBase,
        graph_store: GraphStoreBase,
        cache_prefix: str = "life"
    ) -> Dict[str, Any]:
        """创建Life能力包（预设组合）
        
        包含：意图识别、上下文检索、对话生成、记忆提取
        
        Args:
            llm_caller: LLM调用器
            graph_store: 图存储实例
            cache_prefix: 缓存键前缀
            
        Returns:
            Life能力字典
        """
        # 1. NLP能力
        nlp_package = self.create_nlp_capability_package(
            llm_caller=llm_caller,
            cache_prefix=f"{cache_prefix}_nlp"
        )
        
        # 2. Life特定能力
        package = {
            "intent_recognizer": nlp_package["intent_recognizer"],
            "entity_extractor": nlp_package.get("entity_extractor"),
            "emotion_analyzer": nlp_package.get("emotion_analyzer"),
            "summarizer": nlp_package["summarizer"],
            "context_retriever": self.create_context_retriever(
                graph_store=graph_store,
                cache_key=f"{cache_prefix}_context"
            ),
            "dialogue_generator": self.create_dialogue_generator(
                llm_caller=llm_caller,
                cache_key=f"{cache_prefix}_dialogue"
            ),
            "memory_extractor": self.create_memory_extractor(
                graph_store=graph_store,
                summarizer=nlp_package["summarizer"],
                cache_key=f"{cache_prefix}_memory"
            )
        }
        
        logger.info(f"创建Life能力包完成，包含 {len(package)} 个能力")
        return package
    
    # ========== Capability Layer - Work Capabilities ==========
    
    def create_document_parser(
        self,
        use_pdfplumber: bool = False,
        llm_caller: Optional[LLMCallerBase] = None,
        cache_key: Optional[str] = None
    ) -> DocumentParser:
        """创建文档解析器
        
        Args:
            use_pdfplumber: PDF解析是否使用pdfplumber
            llm_caller: LLM调用器(用于实体提取)
            cache_key: 缓存键
            
        Returns:
            文档解析器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的文档解析器: {cache_key}")
            return self._cache[cache_key]
        
        entity_extractor = None
        if llm_caller:
            entity_extractor = self.create_entity_extractor(
                llm_caller=llm_caller,
                enable_jieba=True
            )
        
        parser = DocumentParser(
            use_pdfplumber=use_pdfplumber,
            entity_extractor=entity_extractor
        )
        
        if cache_key:
            self._cache[cache_key] = parser
        
        return parser
    
    def create_todo_parser(
        self,
        llm_caller: Optional[LLMCallerBase] = None,
        cache_key: Optional[str] = None
    ) -> TodoParser:
        """创建待办解析器
        
        Args:
            llm_caller: LLM调用器(可选)
            cache_key: 缓存键
            
        Returns:
            待办解析器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的待办解析器: {cache_key}")
            return self._cache[cache_key]
        
        parser = TodoParser(llm_caller=llm_caller)
        
        if cache_key:
            self._cache[cache_key] = parser
        
        return parser
    
    def create_pattern_analyzer(
        self,
        graph_store: GraphStoreBase,
        cache_key: Optional[str] = None
    ) -> PatternAnalyzer:
        """创建模式分析器
        
        Args:
            graph_store: 图存储实例
            cache_key: 缓存键
            
        Returns:
            模式分析器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的模式分析器: {cache_key}")
            return self._cache[cache_key]
        
        analyzer = PatternAnalyzer(graph_store=graph_store)
        
        if cache_key:
            self._cache[cache_key] = analyzer
        
        return analyzer
    
    def create_project_analyzer(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> ProjectAnalyzer:
        """创建项目分析器
        
        Args:
            api_key: LLM API密钥
            model: 模型名称
            base_url: API基础URL
            cache_key: 缓存键
            
        Returns:
            项目分析器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的项目分析器: {cache_key}")
            return self._cache[cache_key]
        
        # 创建依赖组件
        llm_caller = self.create_llm_caller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            cache_key=f"{cache_key}_llm" if cache_key else None
        )
        
        entity_extractor = self.create_entity_extractor(
            llm_caller=llm_caller,
            enable_jieba=True,
            cache_key=f"{cache_key}_entity" if cache_key else None
        )
        
        # 创建DocumentParsePipeline
        from ame.foundation.file import DocumentParsePipeline
        doc_parser = DocumentParsePipeline()
        
        analyzer = ProjectAnalyzer(
            llm_caller=llm_caller,
            doc_parser=doc_parser,
            entity_extractor=entity_extractor
        )
        
        if cache_key:
            self._cache[cache_key] = analyzer
            logger.debug(f"缓存项目分析器: {cache_key}")
        
        return analyzer
    
    def create_todo_manager(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        graph_host: str = "localhost",
        graph_port: int = 6379,
        graph_name: str = "work_graph",
        graph_password: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> TodoManager:
        """创建待办管理器
        
        Args:
            api_key: LLM API密钥
            model: 模型名称
            base_url: API基础URL
            graph_host: 图数据库主机
            graph_port: 图数据库端口
            graph_name: 图名称
            graph_password: 图数据库密码
            cache_key: 缓存键
            
        Returns:
            待办管理器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的待办管理器: {cache_key}")
            return self._cache[cache_key]
        
        # 创建依赖组件
        llm_caller = self.create_llm_caller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            cache_key=f"{cache_key}_llm" if cache_key else None
        )
        
        graph_store = self.create_graph_store(
            host=graph_host,
            port=graph_port,
            graph_name=graph_name,
            password=graph_password,
            cache_key=f"{cache_key}_graph" if cache_key else None
        )
        
        todo_sorter = self.create_todo_sorter(
            cache_key=f"{cache_key}_sorter" if cache_key else None
        )
        
        manager = TodoManager(
            llm_caller=llm_caller,
            graph_store=graph_store,
            todo_sorter=todo_sorter
        )
        
        if cache_key:
            self._cache[cache_key] = manager
            logger.debug(f"缓存待办管理器: {cache_key}")
        
        return manager
    
    def create_advice_generator(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        graph_host: str = "localhost",
        graph_port: int = 6379,
        graph_name: str = "work_graph",
        graph_password: Optional[str] = None,
        cache_key: Optional[str] = None
    ) -> AdviceGenerator:
        """创建建议生成器
        
        Args:
            api_key: LLM API密钥
            model: 模型名称
            base_url: API基础URL
            graph_host: 图数据库主机
            graph_port: 图数据库端口
            graph_name: 图名称
            graph_password: 图数据库密码
            cache_key: 缓存键
            
        Returns:
            建议生成器实例
        """
        if cache_key and cache_key in self._cache:
            logger.debug(f"复用缓存的建议生成器: {cache_key}")
            return self._cache[cache_key]
        
        # 创建依赖组件
        llm_caller = self.create_llm_caller(
            api_key=api_key,
            model=model,
            base_url=base_url,
            cache_key=f"{cache_key}_llm" if cache_key else None
        )
        
        graph_store = self.create_graph_store(
            host=graph_host,
            port=graph_port,
            graph_name=graph_name,
            password=graph_password,
            cache_key=f"{cache_key}_graph" if cache_key else None
        )
        
        generator = AdviceGenerator(
            llm_caller=llm_caller,
            graph_store=graph_store
        )
        
        if cache_key:
            self._cache[cache_key] = generator
            logger.debug(f"缓存建议生成器: {cache_key}")
        
        return generator
    
    def create_work_capability_package(
        self,
        llm_api_key: str,
        llm_model: str = "gpt-3.5-turbo",
        llm_base_url: Optional[str] = None,
        graph_host: str = "localhost",
        graph_port: int = 6379,
        graph_name: str = "work_graph",
        graph_password: Optional[str] = None,
        cache_prefix: str = "work"
    ) -> Dict[str, Any]:
        """创建Work能力包（预设组合）
        
        包含：文档解析器、待办解析器、项目分析器、待办管理器、模式分析器、建议生成器
        
        Args:
            llm_api_key: LLM API密钥
            llm_model: 模型名称
            llm_base_url: API基础URL
            graph_host: 图数据库主机
            graph_port: 图数据库端口
            graph_name: 图名称
            graph_password: 图数据库密码
            cache_prefix: 缓存键前缀
            
        Returns:
            Work能力字典
        """
        # 创建共享的LLM调用器和图存储
        llm_caller = self.create_llm_caller(
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
            cache_key=f"{cache_prefix}_llm"
        )
        
        graph_store = self.create_graph_store(
            host=graph_host,
            port=graph_port,
            graph_name=graph_name,
            password=graph_password,
            cache_key=f"{cache_prefix}_graph"
        )
        
        package = {
            "document_parser": self.create_document_parser(
                use_pdfplumber=False,
                llm_caller=llm_caller,
                cache_key=f"{cache_prefix}_document_parser"
            ),
            "todo_parser": self.create_todo_parser(
                llm_caller=llm_caller,
                cache_key=f"{cache_prefix}_todo_parser"
            ),
            "project_analyzer": self.create_project_analyzer(
                api_key=llm_api_key,
                model=llm_model,
                base_url=llm_base_url,
                cache_key=f"{cache_prefix}_project_analyzer"
            ),
            "todo_manager": self.create_todo_manager(
                api_key=llm_api_key,
                model=llm_model,
                base_url=llm_base_url,
                graph_host=graph_host,
                graph_port=graph_port,
                graph_name=graph_name,
                graph_password=graph_password,
                cache_key=f"{cache_prefix}_todo_manager"
            ),
            "pattern_analyzer": self.create_pattern_analyzer(
                graph_store=graph_store,
                cache_key=f"{cache_prefix}_pattern_analyzer"
            ),
            "advice_generator": self.create_advice_generator(
                api_key=llm_api_key,
                model=llm_model,
                base_url=llm_base_url,
                graph_host=graph_host,
                graph_port=graph_port,
                graph_name=graph_name,
                graph_password=graph_password,
                cache_key=f"{cache_prefix}_advice_generator"
            )
        }
        
        logger.info(f"创建Work能力包完成，包含 {len(package)} 个能力")
        return package
    
    # ========== Cache Management ==========
    
    def clear_cache(self, pattern: Optional[str] = None):
        """清理缓存
        
        Args:
            pattern: 缓存键模式（如果提供，只清理匹配的键）
        """
        if pattern:
            keys_to_remove = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self._cache[key]
            logger.info(f"清理缓存: {len(keys_to_remove)} 个匹配 '{pattern}' 的键")
        else:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"清理所有缓存: {count} 个键")
    
    def get_cache_info(self) -> Dict[str, int]:
        """获取缓存信息
        
        Returns:
            缓存统计信息
        """
        return {
            "total_cached": len(self._cache),
            "cached_keys": list(self._cache.keys())
        }
