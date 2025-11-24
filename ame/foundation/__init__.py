"""
Foundation Layer - 基础能力层

提供原子化的技术能力，无业务逻辑，可独立使用和测试。

模块：
- llm: LLM 调用能力
- file: 文件解析能力
- nlp: 自然语言处理能力
- algorithm: 算法能力
- storage: 存储能力
"""

__version__ = "0.1.0"

# LLM
from .llm import (
    # Utils
    LLMResponse,
    ConversationHistory,
    CompressContext,
    CompressResult,
    create_user_message,
    create_assistant_message,
    create_system_message,
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
    # Core
    BaseLLMCaller,
    OpenAICaller,
    # Components
    PromptBuilder,
    HistoryManager,
    CompressionStrategy,
    CacheStrategy,
    CompressStrategy,
    RetryStrategy,
)

# NLP
from .nlp import (
    # Core - Enums
    IntentType,
    EntityType,
    EmotionType,
    # Core - Models
    IntentResult,
    Entity,
    EmotionResult,
    Summary,
    NLPAnalysisResult,
    # Core - Exceptions
    NLPError,
    IntentRecognitionError,
    EntityExtractionError,
    EmotionAnalysisError,
    SummarizationError,
    ModelNotLoadedError,
    # Atomic
    IntentRecognizer,
    EntityExtractor,
    EmotionAnalyzer,
    Summarizer,
)

# Algorithm
from .algorithm import (
    TodoSorter,
    TodoItem,
    SortedTodoList,
    Priority,
    TaskStatus,
)

# Graph
from .graph import (
    # Enums
    NodeLabel,
    RelationType,
    GraphType,
    # Models
    GraphNode,
    GraphEdge,
    QueryResult,
    # Exceptions
    StorageError,
    ValidationError,
    GraphStoreError,
    # Core
    GraphStoreBase,
    FalkorDBStore,
)

# File
from .file import (
    # Core
    DocumentFormat,
    SectionType,
    DocumentSection,
    ParsedDocument,
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
    # Atomic
    FileParserBase,
    TextParser,
    MarkdownParser,
    PDFParser,
    DocxParser,
    # Pipeline
    DocumentParsePipeline,
    parse_document,
)

__all__ = [
    # LLM
    "LLMResponse",
    "ConversationHistory",
    "CompressContext",
    "CompressResult",
    "create_user_message",
    "create_assistant_message",
    "create_system_message",
    "LLMError",
    "CallerNotConfiguredError",
    "TokenLimitExceededError",
    "CompressionError",
    "CacheError",
    "BaseLLMCaller",
    "OpenAICaller",
    "PromptBuilder",
    "HistoryManager",
    "CompressionStrategy",
    "CacheStrategy",
    "CompressStrategy",
    "RetryStrategy",
    
    # File - Core
    "DocumentFormat",
    "SectionType",
    "DocumentSection",
    "ParsedDocument",
    "FileParserError",
    "UnsupportedFormatError",
    "ParseError",
    "DependencyMissingError",
    # File - Atomic
    "FileParserBase",
    "TextParser",
    "MarkdownParser",
    "PDFParser",
    "DocxParser",
    # File - Pipeline
    "DocumentParsePipeline",
    "parse_document",
    
    # NLP - Core - Enums
    "IntentType",
    "EntityType",
    "EmotionType",
    # NLP - Core - Models
    "IntentResult",
    "Entity",
    "EmotionResult",
    "Summary",
    "NLPAnalysisResult",
    # NLP - Core - Exceptions
    "NLPError",
    "IntentRecognitionError",
    "EntityExtractionError",
    "EmotionAnalysisError",
    "SummarizationError",
    "ModelNotLoadedError",
    # NLP - Atomic
    "IntentRecognizer",
    "EntityExtractor",
    "EmotionAnalyzer",
    "Summarizer",
    
    # Algorithm
    "TodoSorter",
    "TodoItem",
    "SortedTodoList",
    "Priority",
    "TaskStatus",
    
    # Graph - Enums
    "NodeLabel",
    "RelationType",
    "GraphType",
    # Graph - Models
    "GraphNode",
    "GraphEdge",
    "QueryResult",
    # Graph - Exceptions
    "StorageError",
    "ValidationError",
    "GraphStoreError",
    # Graph - Core
    "GraphStoreBase",
    "FalkorDBStore",
]
