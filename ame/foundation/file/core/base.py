"""
文件解析器基类

定义统一的解析器接口，支持多种文档格式解析
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger

from ..utils.models import DocumentFormat, ParsedMarkdown
from ..utils.exceptions import UnsupportedFormatError
from ..components.trans2markdown import Trans2Markdown


class FileParserBase(ABC):
    """
    文件解析器基类
    
    架构设计：
    1. 子类必须实现具体的 _parse_* 方法（如 _parse_pdf, _parse_docx等）
    2. 统一的 parse 方法调用组件能力，映射到具体解析方法
    3. 自动将解析结果转换为Markdown格式
    
    子类需实现：
    - can_parse(): 判断是否支持该文件
    - _parse_pdf(), _parse_docx() 等具体解析方法
    """
    
    # 支持的文件扩展名（子类需要定义）
    SUPPORTED_EXTENSIONS: set = set()
    
    def __init__(self):
        """初始化解析器"""
        self.trans2markdown = Trans2Markdown()
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        判断是否可以解析该文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            can_parse: 是否可以解析
        """
        pass
    
    async def parse(self, file_path: str) -> ParsedMarkdown:
        """
        解析文档（统一入口）
        
        流程：
        1. 验证文件存在
        2. 识别文件格式
        3. 调用对应的 _parse_* 方法
        4. 转换为Markdown格式
        
        Args:
            file_path: 文件路径
        
        Returns:
            parsed_markdown: Markdown格式的解析结果
        
        Raises:
            FileNotFoundError: 文件不存在
            UnsupportedFormatError: 不支持的文件格式
        """
        # 1. 验证文件
        path = self._validate_file_exists(file_path)
        
        # 2. 识别格式
        doc_format = self._identify_format(path)
        
        if doc_format == DocumentFormat.UNKNOWN:
            raise UnsupportedFormatError(
                format=path.suffix,
                message=f"不支持的文件格式: {path.suffix}"
            )
        
        logger.info(f"开始解析文件: {path.name}, 格式: {doc_format.value}")
        
        # 3. 映射到具体解析方法
        content, metadata = await self._dispatch_parse(path, doc_format)
        
        # 4. 转换为Markdown
        parsed_markdown = await self.trans2markdown.convert(
            content=content,
            source_format=doc_format,
            file_path=str(path),
            metadata=metadata
        )
        
        logger.info(
            f"解析完成: {path.name}, "
            f"字符数={parsed_markdown.total_chars}, "
            f"格式={doc_format.value}"
        )
        
        return parsed_markdown
    
    async def _dispatch_parse(
        self,
        path: Path,
        doc_format: DocumentFormat
    ) -> tuple[str, Dict[str, Any]]:
        """
        分发到具体的解析方法
        
        Args:
            path: 文件路径
            doc_format: 文档格式
        
        Returns:
            (content, metadata): 内容和元数据
        """
        # 格式到方法的映射
        format_method_map = {
            DocumentFormat.PDF: self._parse_pdf,
            DocumentFormat.DOCX: self._parse_docx,
            DocumentFormat.DOC: self._parse_doc,
            DocumentFormat.PPT: self._parse_ppt,
            DocumentFormat.MARKDOWN: self._parse_markdown,
            DocumentFormat.TEXT: self._parse_text,
        }
        
        parse_method = format_method_map.get(doc_format)
        
        if parse_method is None:
            raise UnsupportedFormatError(
                format=doc_format.value,
                message=f"未实现的解析方法: {doc_format.value}"
            )
        
        return await parse_method(path)
    
    # ==================== 子类需要实现的具体解析方法 ====================
    
    async def _parse_pdf(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """
        解析PDF文件
        
        Args:
            path: 文件路径
        
        Returns:
            (content, metadata): 内容和元数据
        """
        raise NotImplementedError("子类需要实现 _parse_pdf 方法")
    
    async def _parse_docx(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """
        解析DOCX文件
        
        Args:
            path: 文件路径
        
        Returns:
            (content, metadata): 内容和元数据
        """
        raise NotImplementedError("子类需要实现 _parse_docx 方法")
    
    async def _parse_doc(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """
        解析DOC文件
        
        Args:
            path: 文件路径
        
        Returns:
            (content, metadata): 内容和元数据
        """
        raise NotImplementedError("子类需要实现 _parse_doc 方法")
    
    async def _parse_ppt(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """
        解析PPT文件
        
        Args:
            path: 文件路径
        
        Returns:
            (content, metadata): 内容和元数据
        """
        raise NotImplementedError("子类需要实现 _parse_ppt 方法")
    
    async def _parse_markdown(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """
        解析Markdown文件
        
        Args:
            path: 文件路径
        
        Returns:
            (content, metadata): 内容和元数据
        """
        raise NotImplementedError("子类需要实现 _parse_markdown 方法")
    
    async def _parse_text(self, path: Path) -> tuple[str, Dict[str, Any]]:
        """
        解析纯文本文件
        
        Args:
            path: 文件路径
        
        Returns:
            (content, metadata): 内容和元数据
        """
        raise NotImplementedError("子类需要实现 _parse_text 方法")
    
    # ==================== 工具方法 ====================
    
    def _validate_file_exists(self, file_path: str) -> Path:
        """
        验证文件是否存在
        
        Args:
            file_path: 文件路径
        
        Returns:
            path: Path对象
        
        Raises:
            FileNotFoundError: 文件不存在
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"不是文件: {file_path}")
        
        return path
    
    def _get_file_extension(self, file_path: str) -> str:
        """
        获取文件扩展名（小写，不含点）
        
        Args:
            file_path: 文件路径
        
        Returns:
            extension: 扩展名
        """
        return Path(file_path).suffix.lower().lstrip(".")
    
    def _identify_format(self, path: Path) -> DocumentFormat:
        """
        识别文档格式
        
        Args:
            path: 文件路径
        
        Returns:
            format: 文档格式
        """
        extension = path.suffix.lower().lstrip(".")
        
        format_map = {
            "pdf": DocumentFormat.PDF,
            "docx": DocumentFormat.DOCX,
            "doc": DocumentFormat.DOC,
            "ppt": DocumentFormat.PPT,
            "pptx": DocumentFormat.PPT,
            "md": DocumentFormat.MARKDOWN,
            "markdown": DocumentFormat.MARKDOWN,
            "txt": DocumentFormat.TEXT,
            "text": DocumentFormat.TEXT,
        }
        
        return format_map.get(extension, DocumentFormat.UNKNOWN)
