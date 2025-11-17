"""
Foundation Layer - 基础能力层

提供原子化的技术能力，无业务逻辑，可独立使用和测试。

模块：
- llm: LLM 调用能力
- file: 文件解析能力
"""

__version__ = "0.3.0"

# LLM
from .llm import (
    # Core
    CallMode,
    LLMResponse,
    CompressContext,
    CompressResult,
    PipelineContext,
    PipelineResult,
    create_user_message,
    create_assistant_message,
    create_system_message,
    ConversationHistory,
    LLMError,
    CallerNotConfiguredError,
    TokenLimitExceededError,
    CompressionError,
    CacheError,
    # Atomic
    LLMCallerBase,
    StreamCaller,
    OpenAICaller,
    CacheStrategy,
    CompressStrategy,
    SessionCompressStrategy,
    DocumentCompressStrategy,
    ChunkingCompressStrategy,
    RetryStrategy,
    # Pipeline
    PipelineBase,
    SessionPipe,
    DocumentPipe,
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
    # LLM - Core
    "CallMode",
    "LLMResponse",
    "CompressContext",
    "CompressResult",
    "PipelineContext",
    "PipelineResult",
    "create_user_message",
    "create_assistant_message",
    "create_system_message",
    "ConversationHistory",
    "LLMError",
    "CallerNotConfiguredError",
    "TokenLimitExceededError",
    "CompressionError",
    "CacheError",
    # LLM - Atomic
    "LLMCallerBase",
    "StreamCaller",
    "OpenAICaller",
    "CacheStrategy",
    "CompressStrategy",
    "SessionCompressStrategy",
    "DocumentCompressStrategy",
    "ChunkingCompressStrategy",
    "RetryStrategy",
    # LLM - Pipeline
    "PipelineBase",
    "SessionPipe",
    "DocumentPipe",
    
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
]
