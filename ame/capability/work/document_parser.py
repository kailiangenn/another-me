"""
文档解析器 - 解析项目文档并提取结构化信息

基于Foundation层的DocumentPipeline,针对Work场景进行封装和增强。
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from loguru import logger

from ame.foundation.file import DocumentParsePipeline, ParsedDocument
from ame.foundation.nlp import EntityExtractor, Entity


@dataclass
class DocumentParseResult:
    """文档解析结果"""
    file_path: str
    format: str
    content: str
    sections: List[Dict[str, Any]] = field(default_factory=list)
    entities: List[Entity] = field(default_factory=list)
    outline: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DocumentParser:
    """Work场景文档解析器
    
    提供文档解析、结构提取、实体识别等功能。
    """
    
    def __init__(
        self,
        use_pdfplumber: bool = False,
        entity_extractor: Optional[EntityExtractor] = None
    ):
        """初始化
        
        Args:
            use_pdfplumber: PDF解析是否使用pdfplumber
            entity_extractor: 实体提取器(可选)
        """
        self.doc_pipeline = DocumentParsePipeline(use_pdfplumber=use_pdfplumber)
        self.entity_extractor = entity_extractor
        logger.debug("DocumentParser初始化完成")
    
    async def parse(
        self,
        file_path: str,
        extract_entities: bool = True,
        extract_outline: bool = True
    ) -> DocumentParseResult:
        """解析单个文档
        
        Args:
            file_path: 文件路径
            extract_entities: 是否提取实体
            extract_outline: 是否提取大纲
            
        Returns:
            文档解析结果
        """
        logger.info(f"开始解析文档: {file_path}")
        
        # 1. 使用Foundation层的DocumentPipeline解析文档
        parsed_doc = await self.doc_pipeline.parse(file_path)
        
        # 2. 提取大纲
        outline = []
        if extract_outline:
            outline = self._extract_outline(parsed_doc)
        
        # 3. 提取实体
        entities = []
        if extract_entities and self.entity_extractor:
            try:
                entities = await self.entity_extractor.extract(
                    parsed_doc.content,
                    use_llm=False,  # Work场景优先用规则
                    use_jieba=True
                )
                logger.debug(f"提取到 {len(entities)} 个实体")
            except Exception as e:
                logger.warning(f"实体提取失败: {e}")
        
        # 4. 转换sections为字典格式
        sections_dict = [
            {
                "type": section.type.value,
                "content": section.content,
                "level": section.level,
                "page_number": section.page_number,
                "line_number": section.line_number
            }
            for section in parsed_doc.sections
        ]
        
        result = DocumentParseResult(
            file_path=file_path,
            format=parsed_doc.format.value,
            content=parsed_doc.content,
            sections=sections_dict,
            entities=entities,
            outline=outline,
            metadata={
                "total_chars": parsed_doc.total_chars,
                "total_pages": parsed_doc.total_pages,
                "section_count": len(parsed_doc.sections),
                "entity_count": len(entities)
            }
        )
        
        logger.info(f"文档解析完成: {Path(file_path).name}")
        return result
    
    async def parse_batch(
        self,
        file_paths: List[str],
        extract_entities: bool = True,
        extract_outline: bool = True,
        ignore_errors: bool = True
    ) -> List[DocumentParseResult]:
        """批量解析文档
        
        Args:
            file_paths: 文件路径列表
            extract_entities: 是否提取实体
            extract_outline: 是否提取大纲
            ignore_errors: 是否忽略错误
            
        Returns:
            解析结果列表
        """
        logger.info(f"开始批量解析 {len(file_paths)} 个文档")
        
        results = []
        for file_path in file_paths:
            try:
                result = await self.parse(
                    file_path,
                    extract_entities=extract_entities,
                    extract_outline=extract_outline
                )
                results.append(result)
            except Exception as e:
                if ignore_errors:
                    logger.warning(f"解析文档失败: {file_path}, 错误: {e}")
                else:
                    raise
        
        logger.info(f"批量解析完成: {len(results)}/{len(file_paths)} 个文档")
        return results
    
    def _extract_outline(self, parsed_doc: ParsedDocument) -> List[Dict[str, Any]]:
        """提取文档大纲
        
        Args:
            parsed_doc: 解析后的文档
            
        Returns:
            大纲列表
        """
        from ame.foundation.file.core.models import SectionType
        
        outline = []
        
        for section in parsed_doc.sections:
            # 只提取标题类型的section
            if section.type in [
                SectionType.HEADING_1,
                SectionType.HEADING_2,
                SectionType.HEADING_3,
                SectionType.HEADING_4,
                SectionType.HEADING_5,
                SectionType.HEADING_6
            ]:
                outline.append({
                    "level": section.level or 1,
                    "title": section.content,
                    "page": section.page_number,
                    "line": section.line_number
                })
        
        return outline
    
    def get_supported_formats(self) -> Dict[str, List[str]]:
        """获取支持的文件格式
        
        Returns:
            格式映射字典
        """
        return self.doc_pipeline.get_supported_formats()
    
    def is_supported(self, file_path: str) -> bool:
        """判断文件是否支持
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否支持
        """
        return self.doc_pipeline.is_supported(file_path)
