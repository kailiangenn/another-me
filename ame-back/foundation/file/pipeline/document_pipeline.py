"""
文档解析管道

特性:
- 自动识别文档格式
- 选择合适的解析器
- 统一的解析接口
- 支持自定义解析器
"""

import logging
from typing import List, Optional, Dict
from pathlib import Path

from ..atomic import (
    FileParserBase,
    TextParser,
    MarkdownParser,
    PDFParser,
    DocxParser,
)
from ..core.models import ParsedDocument, DocumentFormat
from ..core.exceptions import UnsupportedFormatError

logger = logging.getLogger(__name__)


class DocumentParsePipeline:
    """
    文档解析管道
    
    功能:
    - 自动根据文件扩展名选择解析器
    - 支持注册自定义解析器
    - 提供统一的解析接口
    
    使用示例:
        pipeline = DocumentParsePipeline()
        doc = await pipeline.parse("/path/to/document.pdf")
        print(doc.raw_content)
        print(doc.get_outline())
    """
    
    def __init__(self, use_pdfplumber: bool = False):
        """
        初始化解析管道
        
        Args:
            use_pdfplumber: PDF解析是否使用pdfplumber（默认PyPDF2）
        """
        self.parsers: List[FileParserBase] = []
        self._initialize_default_parsers(use_pdfplumber)
    
    def _initialize_default_parsers(self, use_pdfplumber: bool = False):
        """初始化默认解析器"""
        self.parsers = [
            MarkdownParser(),      # Markdown 优先（因为可能被误识别为文本）
            PDFParser(use_pdfplumber=use_pdfplumber),
            DocxParser(),
            TextParser(),          # 文本解析器放最后（兜底）
        ]
        
        logger.info(f"初始化文档解析管道，共 {len(self.parsers)} 个解析器")
    
    def register_parser(self, parser: FileParserBase):
        """
        注册自定义解析器
        
        Args:
            parser: 自定义解析器实例
        """
        self.parsers.insert(0, parser)  # 插入到最前面，优先使用
        logger.info(f"注册自定义解析器: {parser.__class__.__name__}")
    
    async def parse(
        self,
        file_path: str,
        parser_name: Optional[str] = None
    ) -> ParsedDocument:
        """
        解析文档
        
        Args:
            file_path: 文件路径
            parser_name: 指定解析器名称（可选），不指定则自动选择
        
        Returns:
            parsed_doc: 解析结果
        
        Raises:
            FileNotFoundError: 文件不存在
            UnsupportedFormatError: 不支持的文件格式
        """
        # 验证文件存在
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"不是文件: {file_path}")
        
        # 选择解析器
        parser = self._select_parser(str(path), parser_name)
        
        if not parser:
            raise UnsupportedFormatError(path.suffix)
        
        logger.info(f"使用 {parser.__class__.__name__} 解析文件: {path.name}")
        
        # 执行解析
        try:
            parsed_doc = await parser.parse(str(path))
            logger.info(
                f"解析完成: {path.name}, "
                f"字符数={parsed_doc.total_chars}, "
                f"章节数={len(parsed_doc.sections)}"
            )
            return parsed_doc
        
        except Exception as e:
            logger.error(f"文档解析失败: {file_path}, {e}", exc_info=True)
            raise
    
    async def batch_parse(
        self,
        file_paths: List[str],
        ignore_errors: bool = True
    ) -> List[ParsedDocument]:
        """
        批量解析文档
        
        Args:
            file_paths: 文件路径列表
            ignore_errors: 是否忽略单个文件的解析错误
        
        Returns:
            parsed_docs: 解析结果列表
        """
        results = []
        
        for file_path in file_paths:
            try:
                doc = await self.parse(file_path)
                results.append(doc)
            
            except Exception as e:
                if ignore_errors:
                    logger.warning(f"跳过解析失败的文件: {file_path}, {e}")
                else:
                    raise
        
        logger.info(f"批量解析完成: {len(results)}/{len(file_paths)} 个文件")
        return results
    
    def _select_parser(
        self,
        file_path: str,
        parser_name: Optional[str] = None
    ) -> Optional[FileParserBase]:
        """
        选择合适的解析器
        
        Args:
            file_path: 文件路径
            parser_name: 指定解析器名称（可选）
        
        Returns:
            parser: 解析器实例
        """
        # 如果指定了解析器名称
        if parser_name:
            for parser in self.parsers:
                if parser.__class__.__name__ == parser_name:
                    return parser
            
            logger.warning(f"未找到指定的解析器: {parser_name}，自动选择")
        
        # 自动选择
        for parser in self.parsers:
            if parser.can_parse(file_path):
                return parser
        
        return None
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        获取所有支持的文件格式
        
        Returns:
            formats: {解析器名称: [扩展名列表]}
        """
        formats = {}
        
        for parser in self.parsers:
            parser_name = parser.__class__.__name__
            
            # 获取支持的扩展名
            if hasattr(parser, "SUPPORTED_EXTENSIONS"):
                extensions = list(parser.SUPPORTED_EXTENSIONS)
            else:
                extensions = []
            
            formats[parser_name] = extensions
        
        return formats
    
    def is_supported(self, file_path: str) -> bool:
        """
        判断文件是否支持解析
        
        Args:
            file_path: 文件路径
        
        Returns:
            supported: 是否支持
        """
        return self._select_parser(file_path) is not None


# 便捷函数
async def parse_document(
    file_path: str,
    use_pdfplumber: bool = False
) -> ParsedDocument:
    """
    解析文档（便捷函数）
    
    Args:
        file_path: 文件路径
        use_pdfplumber: PDF是否使用pdfplumber
    
    Returns:
        parsed_doc: 解析结果
    
    使用示例:
        from ame.foundation.file import parse_document
        
        doc = await parse_document("example.pdf")
        print(doc.get_outline())
    """
    pipeline = DocumentParsePipeline(use_pdfplumber=use_pdfplumber)
    return await pipeline.parse(file_path)
