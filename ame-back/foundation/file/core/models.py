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


@dataclass
class DocumentSection:
    """文档章节/段落结构"""
    type: SectionType                           # 章节类型
    content: str                                # 章节内容
    level: int = 0                             # 层级（用于标题）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    # 位置信息
    start_position: Optional[int] = None       # 起始位置
    end_position: Optional[int] = None         # 结束位置
    page_number: Optional[int] = None          # 页码（PDF专用）
    line_number: Optional[int] = None          # 行号


@dataclass
class ParsedDocument:
    """
    解析后的文档结构
    
    包含:
    - 原始内容
    - 结构化章节
    - 元数据
    - 统计信息
    """
    # 基础信息
    format: DocumentFormat                     # 文档格式
    file_path: str                             # 文件路径
    raw_content: str                           # 原始文本内容
    
    # 结构化内容
    sections: List[DocumentSection] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 统计信息
    total_chars: int = 0                       # 总字符数
    total_words: int = 0                       # 总词数
    total_pages: Optional[int] = None          # 总页数（PDF/DOCX）
    
    # 时间戳
    parsed_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后自动计算统计信息"""
        if not self.total_chars:
            self.total_chars = len(self.raw_content)
        
        if not self.total_words:
            # 简单的词数统计（按空格分割）
            self.total_words = len(self.raw_content.split())
    
    def get_headings(self, level: Optional[int] = None) -> List[DocumentSection]:
        """
        获取所有标题
        
        Args:
            level: 指定标题级别（1-6），None则返回所有标题
        
        Returns:
            headings: 标题列表
        """
        heading_types = {
            1: SectionType.HEADING_1,
            2: SectionType.HEADING_2,
            3: SectionType.HEADING_3,
            4: SectionType.HEADING_4,
            5: SectionType.HEADING_5,
            6: SectionType.HEADING_6,
        }
        
        if level is not None:
            target_type = heading_types.get(level)
            return [s for s in self.sections if s.type == target_type]
        else:
            all_heading_types = set(heading_types.values())
            return [s for s in self.sections if s.type in all_heading_types]
    
    def get_paragraphs(self) -> List[DocumentSection]:
        """获取所有段落"""
        return [s for s in self.sections if s.type == SectionType.PARAGRAPH]
    
    def get_sections_by_type(self, section_type: SectionType) -> List[DocumentSection]:
        """按类型获取章节"""
        return [s for s in self.sections if s.type == section_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "format": self.format.value,
            "file_path": self.file_path,
            "raw_content": self.raw_content,
            "sections": [
                {
                    "type": s.type.value,
                    "content": s.content,
                    "level": s.level,
                    "metadata": s.metadata,
                    "start_position": s.start_position,
                    "end_position": s.end_position,
                    "page_number": s.page_number,
                    "line_number": s.line_number,
                }
                for s in self.sections
            ],
            "metadata": self.metadata,
            "total_chars": self.total_chars,
            "total_words": self.total_words,
            "total_pages": self.total_pages,
            "parsed_at": self.parsed_at.isoformat(),
        }
    
    def get_outline(self) -> str:
        """
        生成文档大纲（仅标题）
        
        Returns:
            outline: 大纲字符串
        """
        headings = self.get_headings()
        outline_lines = []
        
        for heading in headings:
            indent = "  " * (heading.level - 1)
            outline_lines.append(f"{indent}- {heading.content}")
        
        return "\n".join(outline_lines)
