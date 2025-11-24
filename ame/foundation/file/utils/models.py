"""
文档解析数据模型

定义:
- 文档格式枚举
- 章节类型枚举
- 文档章节数据类
- 解析结果数据类
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional


class DocumentFormat(str, Enum):
    """文档格式枚举"""
    PDF = "pdf"
    MARKDOWN = "markdown"
    TEXT = "text"
    DOCX = "docx"
    DOC = "doc"
    PPT = "ppt"
    UNKNOWN = "unknown"
    
    
class SectionType(str, Enum):
    """文档章节类型"""
    HEADING_1 = "h1"
    HEADING_2 = "h2"
    HEADING_3 = "h3"
    HEADING_4 = "h4"
    HEADING_5 = "h5"
    HEADING_6 = "h6"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code"
    QUOTE = "quote"
    LIST_ITEM = "list"
    TABLE = "table"
    IMAGE = "image"
    UNKNOWN = "unknown"
