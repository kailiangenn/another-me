"""
文件处理模块 - 文档解析与结构化

架构设计:
- core/: 核心层（数据模型、异常定义）
- atomic/: 原子层（具体解析器实现）
- pipeline/: 管道层（解析管道和工厂）

提供统一的文档解析接口，支持多种格式：
- PDF
- Markdown
- TXT
- DOC/DOCX

特性:
- 结构化解析结果
- 自动格式识别
- 元数据提取
- 分块处理支持
"""

# 核心模型
from .core import (
    DocumentFormat,
    SectionType,
    DocumentSection,
    ParsedDocument,
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
)

# 原子解析器
from .atomic import (
    FileParserBase,
    TextParser,
    MarkdownParser,
    PDFParser,
    DocxParser,
)

# 管道
from .pipeline import (
    DocumentParsePipeline,
    parse_document,
)

__all__ = [
    # 核心数据模型
    "DocumentFormat",
    "SectionType",
    "DocumentSection",
    "ParsedDocument",
    
    # 异常
    "FileParserError",
    "UnsupportedFormatError",
    "ParseError",
    "DependencyMissingError",
    
    # 原子解析器
    "FileParserBase",
    "TextParser",
    "MarkdownParser",
    "PDFParser",
    "DocxParser",
    
    # 管道
    "DocumentParsePipeline",
    "parse_document",
]
