"""
PDF 文件解析器

支持:
- .pdf 文件
- 文本提取
- 页码信息
- 简单结构识别

依赖: PyPDF2 或 pdfplumber
"""

from typing import List, Optional
from pathlib import Path
from loguru import logger

from .base import FileParserBase
from ..core.models import ParsedDocument, DocumentSection, DocumentFormat, SectionType
from ..core.exceptions import DependencyMissingError, ParseError


class PDFParser(FileParserBase):
    """
    PDF 解析器
    
    特性:
    - 提取文本内容
    - 保留页码信息
    - 支持多页文档
    
    依赖:
    - PyPDF2 (推荐)
    - pdfplumber (备选)
    """
    
    SUPPORTED_EXTENSIONS = {"pdf"}
    
    def __init__(self, use_pdfplumber: bool = False):
        """
        初始化 PDF 解析器
        
        Args:
            use_pdfplumber: 是否使用 pdfplumber（默认使用 PyPDF2）
        """
        self.use_pdfplumber = use_pdfplumber
        self._check_dependencies()
    
    def _check_dependencies(self):
        """检查依赖是否安装"""
        if self.use_pdfplumber:
            try:
                import pdfplumber
                self.pdf_lib = pdfplumber
            except ImportError:
                logger.warning("pdfplumber 未安装，回退到 PyPDF2")
                self.use_pdfplumber = False
        
        if not self.use_pdfplumber:
            try:
                import PyPDF2
                self.pdf_lib = PyPDF2
            except ImportError:
                error_msg = "PDF 解析依赖未安装"
                logger.error(error_msg)
                self.pdf_lib = None
    
    def can_parse(self, file_path: str) -> bool:
        """判断是否支持该文件"""
        extension = self._get_file_extension(file_path)
        return extension in self.SUPPORTED_EXTENSIONS and self.pdf_lib is not None
    
    async def parse(self, file_path: str) -> ParsedDocument:
        """
        解析 PDF 文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            parsed_doc: 解析结果
        
        Raises:
            ImportError: PDF 解析库未安装
        """
        if self.pdf_lib is None:
            raise DependencyMissingError(
                "PyPDF2 或 pdfplumber",
                "pip install PyPDF2 或 pip install pdfplumber"
            )
        
        # 验证文件
        path = self._validate_file_exists(file_path)
        
        try:
            if self.use_pdfplumber:
                return await self._parse_with_pdfplumber(path)
            else:
                return await self._parse_with_pypdf2(path)
        
        except Exception as e:
            logger.error(f"PDF 文件解析失败: {file_path}, 错误: {e}")
            raise
    
    async def _parse_with_pypdf2(self, path: Path) -> ParsedDocument:
        """
        使用 PyPDF2 解析
        
        Args:
            path: 文件路径
        
        Returns:
            parsed_doc: 解析结果
        """
        import PyPDF2
        
        sections = []
        raw_content_parts = []
        
        with open(path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)
            
            for page_num, page in enumerate(reader.pages, start=1):
                # 提取文本
                text = page.extract_text()
                
                if not text.strip():
                    continue
                
                raw_content_parts.append(text)
                
                # 按段落分割
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                
                for para in paragraphs:
                    sections.append(DocumentSection(
                        type=SectionType.PARAGRAPH,
                        content=para,
                        page_number=page_num,
                        metadata={"source": "PyPDF2"}
                    ))
        
        raw_content = "\n\n".join(raw_content_parts)
        
        return ParsedDocument(
            format=DocumentFormat.PDF,
            file_path=str(path),
            raw_content=raw_content,
            sections=sections,
            total_pages=total_pages,
            metadata={
                "parser": "PyPDF2",
                "file_size": path.stat().st_size,
            }
        )
    
    async def _parse_with_pdfplumber(self, path: Path) -> ParsedDocument:
        """
        使用 pdfplumber 解析（质量更高）
        
        Args:
            path: 文件路径
        
        Returns:
            parsed_doc: 解析结果
        """
        import pdfplumber
        
        sections = []
        raw_content_parts = []
        
        with pdfplumber.open(path) as pdf:
            total_pages = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # 提取文本
                text = page.extract_text()
                
                if not text:
                    continue
                
                raw_content_parts.append(text)
                
                # 按段落分割
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                
                for para in paragraphs:
                    sections.append(DocumentSection(
                        type=SectionType.PARAGRAPH,
                        content=para,
                        page_number=page_num,
                        metadata={"source": "pdfplumber"}
                    ))
                
                # 提取表格（pdfplumber 特性）
                tables = page.extract_tables()
                if tables:
                    for table_idx, table in enumerate(tables):
                        table_text = self._format_table(table)
                        sections.append(DocumentSection(
                            type=SectionType.TABLE,
                            content=table_text,
                            page_number=page_num,
                            metadata={
                                "source": "pdfplumber",
                                "table_index": table_idx
                            }
                        ))
        
        raw_content = "\n\n".join(raw_content_parts)
        
        return ParsedDocument(
            format=DocumentFormat.PDF,
            file_path=str(path),
            raw_content=raw_content,
            sections=sections,
            total_pages=total_pages,
            metadata={
                "parser": "pdfplumber",
                "file_size": path.stat().st_size,
            }
        )
    
    def _format_table(self, table: List[List[Optional[str]]]) -> str:
        """
        格式化表格为文本
        
        Args:
            table: 表格数据（二维列表）
        
        Returns:
            formatted: 格式化后的文本
        """
        if not table:
            return ""
        
        lines = []
        for row in table:
            # 过滤 None 并连接单元格
            cells = [str(cell) if cell else "" for cell in row]
            lines.append(" | ".join(cells))
        
        return "\n".join(lines)
