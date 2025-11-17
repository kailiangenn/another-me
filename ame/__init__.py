"""
AME - Another Me Engine (Foundation Package)
基础能力引擎包，提供 LLM 和文件解析等核心能力

架构：Foundation (基础能力层)

注意：完整的业务能力（Capabilities、Services）请使用 ame-back 包
"""

__version__ = "0.1.0"
__author__ = "Another Me Team"

# ========== Foundation Layer (基础能力层) ==========
# LLM - LLM 调用能力
from .foundation.llm import (
    # Core - 核心层
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
    # Atomic - 原子层
    LLMCallerBase,
    StreamCaller,
    OpenAICaller,
    CacheStrategy,
    CompressStrategy,
    SessionCompressStrategy,
    DocumentCompressStrategy,
    ChunkingCompressStrategy,
    RetryStrategy,
    # Pipeline - 管道层
    PipelineBase,
    SessionPipe,
    DocumentPipe,
)

# File - 文件解析能力
from .foundation.file import (
    # Core - 核心层
    DocumentFormat,
    SectionType,
    DocumentSection,
    ParsedDocument,
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
    # Atomic - 原子层
    FileParserBase,
    TextParser,
    MarkdownParser,
    PDFParser,
    DocxParser,
    # Pipeline - 管道层
    DocumentParsePipeline,
    parse_document,
)


__all__ = [
    # ========== Foundation Layer ==========
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
