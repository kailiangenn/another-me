"""
Foundation Layer - 基础能力层

提供原子化的技术能力，无业务逻辑，可独立使用和测试。

模块：
- llm: LLM 调用能力
- file: 文件解析能力
- graph: 图谱存储能力
"""

__version__ = "0.1.0"

# LLM
from .llm import (
    # 数据模型
    LLMResponse,
    ConversationHistory,
    CompressContext,
    CompressResult,
    # 辅助函数
    create_user_message,
    create_assistant_message,
    create_system_message,
    # 异常
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
    # 核心实现
    BaseLLMCaller,
    OpenAICaller,
    # 组件层
    PromptBuilder,
    HistoryManager,
    CompressionStrategy,
    CacheStrategy,
    CompressStrategy,
    RetryStrategy,
)

# File
from .file import (
    # 核心类
    FileParserBase,
    AMEParser,
    # 数据模型
    DocumentFormat,
    SectionType,
    DocumentSection,
    DocumentStructure,
    ParsedMarkdown,
    # 异常
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
    # 组件
    Trans2Markdown,
    StructureExtractor,
)

# Graph
from .graph import (
    # 枚举
    NodeLabel,
    RelationType,
    GraphType,
    # 数据类
    GraphNode,
    GraphEdge,
    QueryResult,
    # 异常
    StorageError,
    ConnectionError,
    ValidationError,
    QueryError,
    GraphStoreError,
    # Core
    GraphStoreBase,
    FalkorDBStore,
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
    
    # File
    "FileParserBase",
    "AMEParser",
    "DocumentFormat",
    "SectionType",
    "DocumentSection",
    "DocumentStructure",
    "ParsedMarkdown",
    "FileParserError",
    "UnsupportedFormatError",
    "ParseError",
    "DependencyMissingError",
    "Trans2Markdown",
    "StructureExtractor",
    
    # Graph
    "NodeLabel",
    "RelationType",
    "GraphType",
    "GraphNode",
    "GraphEdge",
    "QueryResult",
    "StorageError",
    "ConnectionError",
    "ValidationError",
    "QueryError",
    "GraphStoreError",
    "GraphStoreBase",
    "FalkorDBStore",
]