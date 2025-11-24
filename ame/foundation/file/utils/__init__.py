"""
utils模块 - 数据模型和异常定义
"""

from .models import (
    DocumentFormat,
    SectionType,
    DocumentSection,
    DocumentStructure,
    ParsedMarkdown,
)
from .exceptions import (
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
)

__all__ = [
    # 模型
    "DocumentFormat",
    "SectionType",
    "DocumentSection",
    "DocumentStructure",
    "ParsedMarkdown",
    
    # 异常
    "FileParserError",
    "UnsupportedFormatError",
    "ParseError",
    "DependencyMissingError",
]