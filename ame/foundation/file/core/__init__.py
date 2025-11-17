"""
文档解析核心模块

包含:
- 数据模型
- 异常定义
- 常量配置
"""

from .models import (
    DocumentFormat,
    SectionType,
    DocumentSection,
    ParsedDocument,
)

from .exceptions import (
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
)

__all__ = [
    # 数据模型
    "DocumentFormat",
    "SectionType",
    "DocumentSection",
    "ParsedDocument",
    
    # 异常
    "FileParserError",
    "UnsupportedFormatError",
    "ParseError",
    "DependencyMissingError",
]
