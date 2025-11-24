"""
文本转Markdown组件

将文档结构转换为Markdown格式
"""

from typing import Dict, Any
from loguru import logger

from ..utils.models import DocumentFormat, ParsedMarkdown, DocumentStructure
from .structure_extractor import StructureExtractor


class Trans2Markdown:
    """
    文本转Markdown转换器
    
    功能：基于DocumentStructure生成Markdown内容
    """
    
    def __init__(self):
        """初始化转换器"""
        self.structure_extractor = StructureExtractor()
    
    async def convert(
        self,
        content: str,
        source_format: DocumentFormat,
        file_path: str,
        metadata: Dict[str, Any] = None
    ) -> ParsedMarkdown:
        """
        转换文本为Markdown格式
        
        Args:
            content: 原始内容
            source_format: 源文件格式
            file_path: 文件路径
            metadata: 元数据
        
        Returns:
            parsed_markdown: Markdown数据类
        """
        if metadata is None:
            metadata = {}
        
        # 1. 提取文档结构
        structure = self.structure_extractor.extract(
            content=content,
            source_format=source_format,
            metadata=metadata
        )
        
        # 2. 将结构转换为Markdown
        markdown_content = structure.to_markdown()
        
        # 3. 如果转换失败或为空，使用原始内容
        if not markdown_content:
            logger.warning(f"结构转换为空，使用原始内容: {file_path}")
            markdown_content = content
        
        return ParsedMarkdown(
            source_format=source_format,
            file_path=file_path,
            markdown_content=markdown_content,
            structure=structure,  # 保存结构信息
            metadata=metadata
        )

