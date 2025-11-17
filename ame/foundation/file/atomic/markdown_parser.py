"""
Markdown 文件解析器

支持:
- .md 文件
- 标题层级识别
- 代码块提取
- 列表、引用等结构
"""

import logging
import re
from typing import List
from pathlib import Path

from .base import FileParserBase
from ..core.models import ParsedDocument, DocumentSection, DocumentFormat, SectionType
from ..core.exceptions import ParseError

logger = logging.getLogger(__name__)


class MarkdownParser(FileParserBase):
    """
    Markdown 解析器
    
    特性:
    - 识别标题（# - ######）
    - 提取代码块
    - 识别引用、列表
    - 保留原始格式
    """
    
    SUPPORTED_EXTENSIONS = {"md", "markdown", "mdown", "mkd"}
    
    # 正则表达式
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r"```[\s\S]*?```", re.MULTILINE)
    QUOTE_PATTERN = re.compile(r"^>\s+(.+)$", re.MULTILINE)
    LIST_PATTERN = re.compile(r"^[\*\-\+]\s+(.+)$|^\d+\.\s+(.+)$", re.MULTILINE)
    
    def can_parse(self, file_path: str) -> bool:
        """判断是否支持该文件"""
        extension = self._get_file_extension(file_path)
        return extension in self.SUPPORTED_EXTENSIONS
    
    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 Markdown 文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            parsed_doc: 解析结果
        """
        # 验证文件
        path = self._validate_file_exists(file_path)
        
        try:
            # 读取内容
            with open(path, "r", encoding="utf-8") as f:
                raw_content = f.read()
            
            # 解析结构
            sections = self._parse_markdown_structure(raw_content)
            
            # 构建结果
            return ParsedDocument(
                format=DocumentFormat.MARKDOWN,
                file_path=str(path),
                raw_content=raw_content,
                sections=sections,
                metadata={
                    "file_size": path.stat().st_size,
                    "has_code_blocks": any(s.type == SectionType.CODE_BLOCK for s in sections),
                }
            )
        
        except Exception as e:
            logger.error(f"Markdown 文件解析失败: {file_path}, {e}", exc_info=True)
            raise
    
    def _parse_markdown_structure(self, content: str) -> List[DocumentSection]:
        """
        解析 Markdown 结构
        
        策略:
        1. 先提取代码块（避免干扰其他解析）
        2. 提取标题
        3. 提取引用
        4. 剩余部分作为段落
        
        Args:
            content: Markdown 内容
        
        Returns:
            sections: 章节列表
        """
        sections = []
        
        # 1. 提取代码块并占位
        code_blocks = []
        placeholder_prefix = "<<<CODE_BLOCK_"
        
        def code_replacer(match):
            idx = len(code_blocks)
            code_blocks.append(match.group(0))
            return f"{placeholder_prefix}{idx}>>>"
        
        content_without_code = self.CODE_BLOCK_PATTERN.sub(code_replacer, content)
        
        # 2. 按行处理
        lines = content_without_code.split("\n")
        
        current_paragraph = []
        position = 0
        line_num = 0
        
        for line in lines:
            line_stripped = line.strip()
            
            # 空行 - 结束当前段落
            if not line_stripped:
                if current_paragraph:
                    sections.append(self._create_paragraph_section(
                        "\n".join(current_paragraph),
                        position,
                        line_num
                    ))
                    current_paragraph = []
                line_num += 1
                position += len(line) + 1
                continue
            
            # 标题
            heading_match = self.HEADING_PATTERN.match(line_stripped)
            if heading_match:
                # 先保存当前段落
                if current_paragraph:
                    sections.append(self._create_paragraph_section(
                        "\n".join(current_paragraph),
                        position,
                        line_num
                    ))
                    current_paragraph = []
                
                # 添加标题
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                
                sections.append(DocumentSection(
                    type=self._get_heading_type(level),
                    content=title,
                    level=level,
                    start_position=position,
                    end_position=position + len(line),
                    line_number=line_num
                ))
                
                line_num += 1
                position += len(line) + 1
                continue
            
            # 引用
            quote_match = self.QUOTE_PATTERN.match(line_stripped)
            if quote_match:
                if current_paragraph:
                    sections.append(self._create_paragraph_section(
                        "\n".join(current_paragraph),
                        position,
                        line_num
                    ))
                    current_paragraph = []
                
                sections.append(DocumentSection(
                    type=SectionType.QUOTE,
                    content=quote_match.group(1),
                    start_position=position,
                    end_position=position + len(line),
                    line_number=line_num
                ))
                
                line_num += 1
                position += len(line) + 1
                continue
            
            # 列表
            list_match = self.LIST_PATTERN.match(line_stripped)
            if list_match:
                item_content = list_match.group(1) or list_match.group(2)
                
                sections.append(DocumentSection(
                    type=SectionType.LIST_ITEM,
                    content=item_content,
                    start_position=position,
                    end_position=position + len(line),
                    line_number=line_num
                ))
                
                line_num += 1
                position += len(line) + 1
                continue
            
            # 检查是否是代码块占位符
            if placeholder_prefix in line_stripped:
                if current_paragraph:
                    sections.append(self._create_paragraph_section(
                        "\n".join(current_paragraph),
                        position,
                        line_num
                    ))
                    current_paragraph = []
                
                # 提取代码块
                idx = int(line_stripped.split(placeholder_prefix)[1].split(">>>")[0])
                code_content = code_blocks[idx]
                
                sections.append(DocumentSection(
                    type=SectionType.CODE_BLOCK,
                    content=code_content,
                    start_position=position,
                    end_position=position + len(code_content),
                    line_number=line_num
                ))
                
                line_num += code_content.count("\n")
                position += len(code_content) + 1
                continue
            
            # 普通文本 - 累积到段落
            current_paragraph.append(line_stripped)
            line_num += 1
            position += len(line) + 1
        
        # 处理最后的段落
        if current_paragraph:
            sections.append(self._create_paragraph_section(
                "\n".join(current_paragraph),
                position,
                line_num
            ))
        
        return sections
    
    def _get_heading_type(self, level: int) -> SectionType:
        """将标题级别转换为 SectionType"""
        mapping = {
            1: SectionType.HEADING_1,
            2: SectionType.HEADING_2,
            3: SectionType.HEADING_3,
            4: SectionType.HEADING_4,
            5: SectionType.HEADING_5,
            6: SectionType.HEADING_6,
        }
        return mapping.get(level, SectionType.HEADING_6)
    
    def _create_paragraph_section(
        self,
        content: str,
        position: int,
        line_num: int
    ) -> DocumentSection:
        """创建段落对象"""
        return DocumentSection(
            type=SectionType.PARAGRAPH,
            content=content,
            start_position=position,
            end_position=position + len(content),
            line_number=line_num
        )
