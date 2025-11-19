"""
项目分析器 - 分析项目文档，提取结构化信息，生成Markdown格式的项目认知报告
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from loguru import logger

from ame.foundation.llm import LLMCallerBase
from ame.foundation.file import DocumentParsePipeline
from ame.foundation.nlp import EntityExtractor, Entity


@dataclass
class ProjectAnalysis:
    """项目分析结果"""
    markdown_content: str           # Markdown格式的项目报告
    project_name: str
    entities: List[Entity] = field(default_factory=list)  # 提取的实体（技术栈、模块等）
    concepts: List[str] = field(default_factory=list)     # 核心概念
    metadata: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)


class ProjectAnalyzer:
    """项目分析器
    
    结合文档解析、实体提取、LLM分析生成项目认知报告。
    """
    
    def __init__(
        self,
        llm_caller: LLMCallerBase,
        doc_parser: DocumentParsePipeline,
        entity_extractor: EntityExtractor
    ):
        """初始化
        
        Args:
            llm_caller: LLM调用器
            doc_parser: 文档解析器
            entity_extractor: 实体提取器
        """
        self.llm = llm_caller
        self.doc_parser = doc_parser
        self.entity_extractor = entity_extractor
        logger.debug("ProjectAnalyzer初始化完成")
    
    async def analyze(
        self,
        doc_paths: List[str],
        project_name: str,
        custom_prompt: Optional[str] = None
    ) -> ProjectAnalysis:
        """分析项目文档
        
        Args:
            doc_paths: 文档路径列表
            project_name: 项目名称
            custom_prompt: 用户自定义提示词（如"重点分析架构"）
            
        Returns:
            项目分析结果
        """
        if not doc_paths:
            logger.error("文档路径列表不能为空")
            raise ValueError("文档路径列表不能为空")
        
        logger.info(f"开始分析项目: {project_name}, 文档数量: {len(doc_paths)}")
        
        # 1. 解析所有文档
        all_content = []
        for doc_path in doc_paths:
            try:
                parsed_doc = await self.doc_parser.parse(doc_path)
                all_content.append(parsed_doc.content)
                logger.debug(f"成功解析文档: {doc_path}")
            except Exception as e:
                logger.error(f"解析文档失败: {doc_path}, 错误: {e}")
                continue
        
        if not all_content:
            logger.error("没有成功解析任何文档")
            raise ValueError("没有成功解析任何文档")
        
        combined_content = "\n\n".join(all_content)
        
        # 2. 提取实体（技术栈、模块、概念）
        entities = []
        try:
            entities = await self.entity_extractor.extract(
                combined_content,
                use_llm=True,
                use_jieba=True
            )
            logger.info(f"提取到 {len(entities)} 个实体")
        except Exception as e:
            logger.warning(f"实体提取失败: {e}")
        
        # 3. 提取核心概念（从实体中筛选CONCEPT类型）
        from ame.foundation.nlp.core.models import EntityType
        concepts = [e.text for e in entities if e.type == EntityType.CONCEPT]
        
        # 4. 使用LLM生成项目分析报告
        markdown_content = await self._generate_analysis_report(
            project_name=project_name,
            content=combined_content,
            entities=entities,
            custom_prompt=custom_prompt
        )
        
        return ProjectAnalysis(
            markdown_content=markdown_content,
            project_name=project_name,
            entities=entities,
            concepts=concepts,
            metadata={
                "doc_count": len(doc_paths),
                "entity_count": len(entities),
                "concept_count": len(concepts)
            }
        )
    
    async def _generate_analysis_report(
        self,
        project_name: str,
        content: str,
        entities: List[Entity],
        custom_prompt: Optional[str] = None
    ) -> str:
        """使用LLM生成Markdown格式的项目分析报告
        
        Args:
            project_name: 项目名称
            content: 文档内容
            entities: 提取的实体
            custom_prompt: 用户自定义提示词
            
        Returns:
            Markdown格式的报告
        """
        # 构建实体摘要
        entity_summary = self._build_entity_summary(entities)
        
        # 构建提示词
        base_prompt = f"""你是一位资深的项目分析专家，请基于以下信息分析项目"{project_name}"。

**提取的关键实体:**
{entity_summary}

**文档内容:**
{content[:3000]}...  # 截取前3000字符

请生成一份结构化的Markdown格式项目认知报告，包含以下内容：

# {project_name} 项目分析报告

## 1. 项目概述
- 项目背景和目标
- 核心功能

## 2. 技术架构
- 技术栈
- 架构设计
- 核心模块

## 3. 关键实体
- 重要组件和概念

## 4. 总结与建议
- 项目特点
- 潜在改进点

"""
        
        if custom_prompt:
            base_prompt += f"\n**用户特殊要求:** {custom_prompt}\n"
        
        base_prompt += "\n请直接输出Markdown格式的报告，不要添加任何解释。"
        
        # 调用LLM生成
        messages = [{"role": "user", "content": base_prompt}]
        
        try:
            response = await self.llm.generate(
                messages,
                max_tokens=2000,
                temperature=0.3
            )
            
            markdown_content = response.content.strip()
            
            # 清理可能的markdown代码块标记
            if markdown_content.startswith("```markdown"):
                markdown_content = markdown_content.replace("```markdown", "", 1)
            if markdown_content.startswith("```"):
                markdown_content = markdown_content.replace("```", "", 1)
            if markdown_content.endswith("```"):
                markdown_content = markdown_content.rsplit("```", 1)[0]
            
            logger.info("项目分析报告生成成功")
            return markdown_content.strip()
            
        except Exception as e:
            logger.error(f"LLM生成项目分析报告失败: {e}")
            # 返回基础报告
            return f"# {project_name} 项目分析报告\n\n生成失败，请稍后重试。\n\n错误信息: {str(e)}"
    
    def _build_entity_summary(self, entities: List[Entity]) -> str:
        """构建实体摘要字符串
        
        Args:
            entities: 实体列表
            
        Returns:
            实体摘要文本
        """
        if not entities:
            return "无"
        
        from ame.foundation.nlp.core.models import EntityType
        
        # 按类型分组
        grouped = {}
        for entity in entities:
            type_name = entity.type.value
            if type_name not in grouped:
                grouped[type_name] = []
            grouped[type_name].append(entity.text)
        
        # 构建摘要
        summary_lines = []
        for entity_type, items in grouped.items():
            unique_items = list(set(items))[:10]  # 去重并限制数量
            summary_lines.append(f"- {entity_type}: {', '.join(unique_items)}")
        
        return "\n".join(summary_lines)
