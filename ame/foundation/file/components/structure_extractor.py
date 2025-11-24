"""
文档结构提取组件

从原始文本或元数据中提取文档的层级结构
"""

import re
from typing import List, Dict, Any
from loguru import logger

from ..utils.models import DocumentSection, SectionType, DocumentStructure, DocumentFormat


class StructureExtractor:
    """
    文档结构提取器
    
    功能：
    1. 从不同格式的文档中提取层级结构
    2. 智能识别标题、段落、列表等
    3. 生成统一的DocumentStructure对象
    """
    
    def extract(
        self,
        content: str,
        source_format: DocumentFormat,
        metadata: Dict[str, Any] = None
    ) -> DocumentStructure:
        """
        提取文档结构
        
        Args:
            content: 文档内容
            source_format: 源文件格式
            metadata: 元数据（可能包含已解析的结构信息）
        
        Returns:
            structure: 文档结构对象
        """
        if metadata is None:
            metadata = {}
        
        # 优先使用元数据中的结构化信息
        if 'sections' in metadata:
            return self._from_metadata_sections(metadata['sections'])
        
        # 根据不同格式应用不同的提取策略
        if source_format == DocumentFormat.MARKDOWN:
            return self._extract_from_markdown(content)
        elif source_format == DocumentFormat.TEXT:
            return self._extract_from_text(content)
        elif source_format == DocumentFormat.PDF:
            return self._extract_from_pdf(content, metadata)
        elif source_format == DocumentFormat.DOCX:
            return self._extract_from_text(content)  # 降级处理
        elif source_format == DocumentFormat.PPT:
            return self._extract_from_ppt(content, metadata)
        else:
            logger.warning(f"未知格式 {source_format}，使用默认文本提取")
            return self._extract_from_text(content)
    
    def _from_metadata_sections(self, sections_data: List[Dict[str, Any]]) -> DocumentStructure:
        """
        从元数据中的sections构建结构
        
        Args:
            sections_data: sections列表
        
        Returns:
            structure: 文档结构
        """
        sections = []
        
        for data in sections_data:
            section_type_str = data.get('type', 'paragraph')
            
            # 转换为SectionType
            try:
                section_type = SectionType(section_type_str)
            except ValueError:
                section_type = SectionType.UNKNOWN
            
            section = DocumentSection(
                type=section_type,
                content=data.get('content', ''),
                level=data.get('level', 0),
                metadata=data.get('metadata', {}),
                page_number=data.get('page_number'),
                line_number=data.get('line_number')
            )
            sections.append(section)
        
        return DocumentStructure(sections=sections)
    
    def _extract_from_markdown(self, content: str) -> DocumentStructure:
        """
        从Markdown提取结构
        
        Args:
            content: Markdown内容
        
        Returns:
            structure: 文档结构
        """
        sections = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 检测标题
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2)
                
                sections.append(DocumentSection(
                    type=SectionType(f"h{level}"),
                    content=title,
                    level=level,
                    line_number=i
                ))
                i += 1
                continue
            
            # 检测代码块
            if line.startswith('```'):
                code_lines = []
                i += 1
                while i < len(lines) and not lines[i].startswith('```'):
                    code_lines.append(lines[i])
                    i += 1
                
                sections.append(DocumentSection(
                    type=SectionType.CODE_BLOCK,
                    content='\n'.join(code_lines),
                    line_number=i - len(code_lines)
                ))
                i += 1
                continue
            
            # 检测引用
            if line.startswith('>'):
                quote_lines = [line.lstrip('> ').strip()]
                i += 1
                while i < len(lines) and lines[i].startswith('>'):
                    quote_lines.append(lines[i].lstrip('> ').strip())
                    i += 1
                
                sections.append(DocumentSection(
                    type=SectionType.QUOTE,
                    content='\n'.join(quote_lines),
                    line_number=i - len(quote_lines)
                ))
                continue
            
            # 检测列表
            list_match = re.match(r'^[\*\-\+]\s+(.+)$', line)
            if list_match:
                sections.append(DocumentSection(
                    type=SectionType.LIST_ITEM,
                    content=list_match.group(1),
                    line_number=i
                ))
                i += 1
                continue
            
            # 普通段落
            if line.strip():
                # 收集连续的非空行
                para_lines = [line]
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith('#'):
                    para_lines.append(lines[i])
                    i += 1
                
                sections.append(DocumentSection(
                    type=SectionType.PARAGRAPH,
                    content=' '.join(para_lines),
                    line_number=i - len(para_lines)
                ))
                continue
            
            i += 1
        
        return DocumentStructure(sections=sections)
    
    def _extract_from_text(self, content: str) -> DocumentStructure:
        """
        从纯文本提取结构（智能检测标题）
        
        Args:
            content: 文本内容
        
        Returns:
            structure: 文档结构
        """
        sections = []
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检测是否像标题
            if self._looks_like_heading(para):
                level = self._detect_heading_level(para)
                sections.append(DocumentSection(
                    type=SectionType(f"h{level}"),
                    content=para,
                    level=level
                ))
            else:
                sections.append(DocumentSection(
                    type=SectionType.PARAGRAPH,
                    content=para
                ))
        
        return DocumentStructure(sections=sections)
    
    def _extract_from_pdf(self, content: str, metadata: Dict[str, Any]) -> DocumentStructure:
        """
        从PDF提取结构
        
        Args:
            content: PDF文本内容
            metadata: 元数据
        
        Returns:
            structure: 文档结构
        """
        sections = []
        lines = content.split('\n')
        current_para = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if current_para:
                    para_text = ' '.join(current_para)
                    
                    if self._looks_like_heading(para_text):
                        level = self._detect_heading_level(para_text)
                        sections.append(DocumentSection(
                            type=SectionType(f"h{level}"),
                            content=para_text,
                            level=level
                        ))
                    else:
                        sections.append(DocumentSection(
                            type=SectionType.PARAGRAPH,
                            content=para_text
                        ))
                    current_para = []
            else:
                # 检查是否是独立的标题行
                if self._looks_like_heading(line) and not current_para:
                    level = self._detect_heading_level(line)
                    sections.append(DocumentSection(
                        type=SectionType(f"h{level}"),
                        content=line,
                        level=level
                    ))
                else:
                    current_para.append(line)
        
        if current_para:
            para_text = ' '.join(current_para)
            if self._looks_like_heading(para_text):
                level = self._detect_heading_level(para_text)
                sections.append(DocumentSection(
                    type=SectionType(f"h{level}"),
                    content=para_text,
                    level=level
                ))
            else:
                sections.append(DocumentSection(
                    type=SectionType.PARAGRAPH,
                    content=para_text
                ))
        
        return DocumentStructure(sections=sections)
    
    def _extract_from_ppt(self, content: str, metadata: Dict[str, Any]) -> DocumentStructure:
        """
        从PPT提取结构
        
        Args:
            content: PPT文本内容
            metadata: 元数据
        
        Returns:
            structure: 文档结构
        """
        sections = []
        slides = content.split('--- Slide ')
        
        for i, slide in enumerate(slides):
            if not slide.strip():
                continue
            
            lines = slide.split('\n')
            
            # 处理幻灯片标题
            if i > 0 and lines:
                first_line = lines[0].strip()
                match = re.match(r'^(\d+)\s*---\s*(.*)$', first_line)
                if match:
                    slide_num = match.group(1)
                    title = match.group(2).strip() if match.group(2) else f"幻灯片 {slide_num}"
                    sections.append(DocumentSection(
                        type=SectionType.HEADING_2,
                        content=title,
                        level=2,
                        metadata={"slide_num": slide_num}
                    ))
                    lines = lines[1:]
            
            # 处理幻灯片内容
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # 检测列表项
                if re.match(r'^[•\-\*○■]\s+', line) or re.match(r'^\d+[\.]\s+', line):
                    clean_line = re.sub(r'^[•\-\*○■]\s+', '', line)
                    clean_line = re.sub(r'^\d+[\.]\s+', '', clean_line)
                    sections.append(DocumentSection(
                        type=SectionType.LIST_ITEM,
                        content=clean_line
                    ))
                elif self._looks_like_heading(line):
                    sections.append(DocumentSection(
                        type=SectionType.HEADING_3,
                        content=line,
                        level=3
                    ))
                else:
                    sections.append(DocumentSection(
                        type=SectionType.PARAGRAPH,
                        content=line
                    ))
        
        return DocumentStructure(sections=sections)
    
    # ==================== 辅助方法 ====================
    
    def _looks_like_heading(self, text: str) -> bool:
        """判断文本是否像标题"""
        if len(text) > 80:
            return False
        
        if text.endswith('。') or text.endswith('.'):
            return False
        
        # 检查章节编号
        if re.match(r'^(\d+\.?\d*|第[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u5343\u4e07]+[章节]|Chapter\s+\d+)', text):
            return True
        
        # 检查是否大写
        if text.isupper() and len(text) > 3:
            return True
        
        return False
    
    def _detect_heading_level(self, text: str) -> int:
        """检测标题级别"""
        # 一级标题
        if re.match(r'^(Chapter\s+\d+|第[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u5343\u4e07]+章)', text, re.IGNORECASE):
            return 1
        
        # 二级标题
        if re.match(r'^(Section\s+\d+|第[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u5343\u4e07]+节|\d+\.0)', text, re.IGNORECASE):
            return 2
        
        # 三级标题
        if re.match(r'^\d+\.\d+(?:\.0)?\s', text):
            return 3
        
        # 四级标题
        if re.match(r'^\d+\.\d+\.\d+', text):
            return 4
        
        # 全大写文本作为二级标题
        if text.isupper():
            return 2
        
        # 默认三级标题
        return 3
