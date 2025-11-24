"""
文件处理模块 - 文档解析与Markdown转换

架构设计:
- utils/: 工具层（数据模型、异常定义）
- components/: 组件层（Markdown转换器、分块处理器）
- core/: 核心层（解析器基类、统一解析器）

特性:
- 统一转换为Markdown格式
- 支持多种文档格式（PDF/DOCX/PPT/MD/TXT）
- 简单的继承接口
- 自动格式识别

使用示例:
    from ame.foundation.file import AMEParser
    
    parser = AMEParser()
    result = await parser.parse("/path/to/document.pdf")
    print(result.markdown_content)
    
自定义解析器:
    from ame.foundation.file import AMEParser
    
    class MyParser(AMEParser):
        async def _parse_pdf(self, path):
            # 自定义PDF解析逻辑
            content = "..."
            metadata = {...}
            return content, metadata
"""

# 核心类
from .core import FileParserBase, AMEParser

# 数据模型
from .utils import (
    DocumentFormat,
    SectionType,
    DocumentSection,
    DocumentStructure,
    ParsedMarkdown,
)

# 异常
from .utils import (
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
)

# 组件
from .components import Trans2Markdown, StructureExtractor

__all__ = [
    # 核心解析器
    "FileParserBase",
    "AMEParser",
    
    # 数据模型
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
    
    # 组件
    "Trans2Markdown",
    "StructureExtractor",
]