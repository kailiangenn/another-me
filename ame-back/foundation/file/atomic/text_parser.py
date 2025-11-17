"""
纯文本文件解析器

支持:
- .txt 文件
- 按段落分割
- 简单结构识别
"""

import logging
from typing import List
from pathlib import Path

from .base import FileParserBase
from ..core.models import ParsedDocument, DocumentSection, DocumentFormat, SectionType
from ..core.exceptions import ParseError

logger = logging.getLogger(__name__)


class TextParser(FileParserBase):
    """
    纯文本解析器
    
    特性:
    - 自动编码检测
    - 按段落分割（空行分隔）
    - 保留原始格式
    """
    
    SUPPORTED_EXTENSIONS = {"txt", "text", "log"}
    
    def can_parse(self, file_path: str) -> bool:
        """判断是否支持该文件"""
        extension = self._get_file_extension(file_path)
        return extension in self.SUPPORTED_EXTENSIONS
    
    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析纯文本文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            parsed_doc: 解析结果
        """
        # 验证文件
        path = self._validate_file_exists(file_path)
        
        try:
            # 读取文本（尝试多种编码）
            raw_content = self._read_text_with_encoding(path)
            
            # 分割段落
            sections = self._split_paragraphs(raw_content)
            
            # 构建结果
            return ParsedDocument(
                format=DocumentFormat.TEXT,
                file_path=str(path),
                raw_content=raw_content,
                sections=sections,
                metadata={
                    "encoding": "utf-8",
                    "file_size": path.stat().st_size,
                }
            )
        
        except Exception as e:
            logger.error(f"文本文件解析失败: {file_path}, {e}", exc_info=True)
            raise
    
    def _read_text_with_encoding(self, path: Path) -> str:
        """
        尝试多种编码读取文本
        
        Args:
            path: 文件路径
        
        Returns:
            content: 文本内容
        """
        encodings = ["utf-8", "gbk", "gb2312", "iso-8859-1", "utf-16"]
        
        for encoding in encodings:
            try:
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, LookupError):
                continue
        
        # 如果所有编码都失败，使用二进制模式并忽略错误
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            logger.warning(f"使用 utf-8 with errors='ignore' 读取文件: {path}")
            return f.read()
    
    def _split_paragraphs(self, content: str) -> List[DocumentSection]:
        """
        按段落分割文本
        
        Args:
            content: 原始文本
        
        Returns:
            sections: 段落列表
        """
        sections = []
        
        # 按空行分割段落
        paragraphs = content.split("\n\n")
        
        position = 0
        line_num = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 计算位置
            start_pos = position
            end_pos = start_pos + len(para)
            
            # 创建段落对象
            section = DocumentSection(
                type=SectionType.PARAGRAPH,
                content=para,
                start_position=start_pos,
                end_position=end_pos,
                line_number=line_num
            )
            
            sections.append(section)
            
            # 更新位置
            position = end_pos + 2  # +2 for "\n\n"
            line_num += para.count("\n") + 1
        
        return sections
