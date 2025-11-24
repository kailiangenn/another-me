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
    """章节类型枚举"""
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


@dataclass
class DocumentSection:
    """
    文档章节/段落结构
    
    用于表示文档的层级结构，包括标题、段落、列表等
    """
    type: SectionType                           # 章节类型
    content: str                                # 章节内容
    level: int = 0                             # 层级（用于标题，1-6）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    # 位置信息
    start_position: Optional[int] = None       # 起始位置
    end_position: Optional[int] = None         # 结束位置
    page_number: Optional[int] = None          # 页码（PDF专用）
    line_number: Optional[int] = None          # 行号
    
    def to_markdown(self) -> str:
        """
        将本章节转换为Markdown格式
        
        Returns:
            markdown: Markdown格式字符串
        """
        if self.type in [
            SectionType.HEADING_1, SectionType.HEADING_2,
            SectionType.HEADING_3, SectionType.HEADING_4,
            SectionType.HEADING_5, SectionType.HEADING_6
        ]:
            # 标题
            level = int(self.type.value[1])  # 从 'h1' 提取 1
            return f"{'#' * level} {self.content}"
        
        elif self.type == SectionType.CODE_BLOCK:
            # 代码块
            return f"```\n{self.content}\n```"
        
        elif self.type == SectionType.QUOTE:
            # 引用
            lines = self.content.split('\n')
            return '\n'.join(f"> {line}" for line in lines)
        
        elif self.type == SectionType.LIST_ITEM:
            # 列表项
            return f"- {self.content}"
        
        elif self.type == SectionType.TABLE:
            # 表格（假设已经是markdown格式）
            return self.content
        
        else:
            # 普通段落
            return self.content


@dataclass
class DocumentStructure:
    """
    文档层级结构
    
    存储文档的完整结构化信息，便于后续处理和转换
    """
    sections: List[DocumentSection] = field(default_factory=list)  # 章节列表
    
    def to_markdown(self) -> str:
        """
        将整个文档结构转换为Markdown
        
        Returns:
            markdown: 完整的Markdown文档
        """
        markdown_parts = []
        
        for section in self.sections:
            md = section.to_markdown()
            if md:
                markdown_parts.append(md)
        
        return '\n\n'.join(markdown_parts)
    
    def get_outline(self) -> str:
        """
        生成文档大纲（仅标题）
        
        Returns:
            outline: 大纲字符串
        """
        outline_lines = []
        
        for section in self.sections:
            if section.type.value.startswith('h'):
                level = int(section.type.value[1])
                indent = "  " * (level - 1)
                outline_lines.append(f"{indent}- {section.content}")
        
        return '\n'.join(outline_lines)
    
    def get_headings(self, level: Optional[int] = None) -> List[DocumentSection]:
        """
        获取所有标题
        
        Args:
            level: 指定标题级别（1-6），None则返回所有标题
        
        Returns:
            headings: 标题列表
        """
        heading_types = [
            SectionType.HEADING_1, SectionType.HEADING_2,
            SectionType.HEADING_3, SectionType.HEADING_4,
            SectionType.HEADING_5, SectionType.HEADING_6
        ]
        
        if level is not None:
            target_type = SectionType(f"h{level}")
            return [s for s in self.sections if s.type == target_type]
        else:
            return [s for s in self.sections if s.type in heading_types]


@dataclass
class ParsedMarkdown:
    """
    解析完成的Markdown文档数据类
    
    解析器将各种格式转换为统一的Markdown格式
    """
    # 基础信息
    source_format: DocumentFormat          # 源文件格式
    file_path: str                         # 文件路径
    markdown_content: str                  # Markdown格式内容
    
    # 结构化信息
    structure: Optional[DocumentStructure] = None  # 文档层级结构
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    total_chars: int = 0                   # 总字符数
    total_words: int = 0                   # 总词数
    total_pages: Optional[int] = None      # 总页数（如果适用）
    
    # 时间戳
    parsed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后自动计算统计信息"""
        if not self.total_chars:
            self.total_chars = len(self.markdown_content)
        
        if not self.total_words:
            # 简单的词数统计（按空格分割）
            self.total_words = len(self.markdown_content.split())
    
    def get_outline(self) -> str:
        """
        获取文档大纲
        
        Returns:
            outline: 大纲字符串
        """
        if self.structure:
            return self.structure.get_outline()
        return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "source_format": self.source_format.value,
            "file_path": self.file_path,
            "markdown_content": self.markdown_content,
            "metadata": self.metadata,
            "total_chars": self.total_chars,
            "total_words": self.total_words,
            "total_pages": self.total_pages,
            "parsed_at": self.parsed_at.isoformat(),
        }
        
        if self.structure:
            result["outline"] = self.structure.get_outline()
        
        return result
