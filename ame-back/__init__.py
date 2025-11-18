"""
AME - Another Me Engine
独立的算法能力引擎，提供检索、分析、生成等核心能力

架构：Foundation (基础能力层) → Capabilities (能力模块层) → Services (业务服务层)
"""

__version__ = "0.1.0"
__author__ = "Another Me Team"

# ========== Foundation Layer (基础能力层) ==========
# Inference - 推理框架
from .foundation.inference import (
    CascadeInferenceEngine,
    InferenceLevelBase,
    InferenceResult,
    InferenceLevel,
    create_rule_level,
    create_llm_level,
)

# LLM - LLM 调用
from .foundation.llm import (
    LLMCallerBase,
    LLMResponse,
    OpenAICaller,
)

# Storage - 存储能力
from .foundation.storage import (
    StorageBase,
    VectorStore,
    GraphStore,
    MetadataStore,
    DocumentStore,
)

# NLP - NLP 基础能力
from .foundation.nlp.emotion import (
    EmotionDetectorBase,
    EmotionResult,
    EmotionType,
    RuleEmotionDetector,
    LLMEmotionDetector,
    HybridEmotionDetector,
)

from .foundation.nlp.ner import (
    NERBase,
    HybridNER,
    Entity,
)

# ========== Capabilities Layer (能力模块层) ==========
# Factory (推荐使用)
from .capabilities import (
    CapabilityFactory,
    CapabilityType,
)

# Memory - 记忆管理
from .capabilities.memory import (
    MemoryBase,
    MemoryItem,
    MemoryManager,
    ConversationFilter,
)

# Retrieval - 混合检索
from .capabilities.retrieval import (
    RetrieverBase as CapRetrieverBase,
    RetrievalResult as CapRetrievalResult,
    HybridRetriever,
)

# Intent - 意图识别
from .capabilities.intent import (
    IntentRecognizerBase,
    IntentResult,
    UserIntent,
    IntentRecognizer,
)

# Analysis - 数据分析
from .capabilities.analysis import (
    DataAnalyzer,
    InsightGenerator,
)

# Generation - RAG 生成
from .capabilities.generation import (
    RAGGenerator,
    StyleGenerator,
)

# ========== Services Layer (业务服务层) ==========
# Conversation Services
from .services.conversation import (
    MimicService,
)

# Knowledge Services
from .services.knowledge import (
    SearchService,
    DocumentService,
)

# Work Services
from .services.work import (
    ReportService,
    TodoService,
    MeetingService,
    ProjectService,
)

# Life Services
from .services.life import (
    MoodService,
    InterestService,
    MemoryService,
)



# 导出模型
from .models.domain import (
    Document,
    DocumentType,
    DataLayer,
    MemoryRetentionType,
    DocumentStatus,
    SearchResult,
)

from .models.report_models import (
    WeeklyReport,
    DailyReport,
    TaskSummary,
    Achievement,
    OrganizedTodos,
    TaskInfo,
    ProjectProgress,
    MoodAnalysis,
    EmotionResult,
    MoodTrend,
    InterestReport,
    InterestTopic,
)

__all__ = [
    # ========== Foundation Layer ==========
    # Inference
    "CascadeInferenceEngine",
    "InferenceLevelBase",
    "InferenceResult",
    "InferenceLevel",
    "create_rule_level",
    "create_llm_level",
    
    # LLM
    "OpenAICaller",
    "LLMCallerBase",
    "LLMResponse",
    
    # Storage
    "StorageBase",
    "VectorStore",
    "GraphStore",
    "MetadataStore",
    "DocumentStore",
    
    # NLP - Emotion
    "EmotionDetectorBase",
    "EmotionResult",
    "EmotionType",
    "RuleEmotionDetector",
    "LLMEmotionDetector",
    "HybridEmotionDetector",
    
    # NLP - NER
    "NERBase",
    "HybridNER",
    "Entity",
    
    # ========== Capabilities Layer ==========
    # Factory (推荐使用)
    "CapabilityFactory",
    "CapabilityType",
    
    # Memory
    "MemoryBase",
    "MemoryItem",
    "MemoryManager",
    "ConversationFilter",
    
    # Retrieval (Capabilities)
    "CapRetrieverBase",
    "CapRetrievalResult",
    "HybridRetriever",
    
    # Intent
    "IntentRecognizerBase",
    "IntentResult",
    "UserIntent",
    "IntentRecognizer",
    
    # Analysis
    "DataAnalyzer",
    "InsightGenerator",
    
    # Generation
    "RAGGenerator",
    "StyleGenerator",
    
    # ========== Services Layer ==========
    # Conversation
    "MimicService",
    
    # Knowledge
    "SearchService",
    "DocumentService",
    
    # Work
    "ReportService",
    "TodoService",
    "MeetingService",
    "ProjectService",
    
    # Life
    "MoodService",
    "InterestService",
    "MemoryService",    
    
    # 域模型
    "Document",
    "DocumentType",
    "DataLayer",
    "MemoryRetentionType",
    "DocumentStatus",
    "SearchResult",
    # 报告模型
    "WeeklyReport",
    "DailyReport",
    "TaskSummary",
    "Achievement",
    "OrganizedTodos",
    "TaskInfo",
    "ProjectProgress",
    "MoodAnalysis",
    "EmotionResult",
    "MoodTrend",
    "InterestReport",
    "InterestTopic",
]
