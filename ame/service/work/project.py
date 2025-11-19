"""
项目认知服务 - 基于文档分析生成项目认知报告

遵循架构规范：
- 通过CapabilityFactory获取所有能力
- 不直接使用Foundation层组件
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from ame.capability.factory import CapabilityFactory
from ame.capability.work import ProjectAnalysis


@dataclass
class ProjectAnalysisResult:
    """项目分析结果"""
    markdown_content: str
    entities: List
    concepts: List[str]
    analyzed_at: datetime


class WorkProjectService:
    """项目认知服务
    
    遵循架构规范：
    - 通过CapabilityFactory获取所有能力
    - 不直接使用Foundation层组件
    """
    
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        llm_api_key: str,
        llm_model: str = "gpt-3.5-turbo",
        llm_base_url: Optional[str] = None
    ):
        """初始化
        
        Args:
            capability_factory: 能力工厂
            llm_api_key: LLM API密钥
            llm_model: LLM模型名称
            llm_base_url: LLM API基础URL
        """
        self.factory = capability_factory
        
        # 通过工厂创建能力
        self.project_analyzer = self.factory.create_project_analyzer(
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
            cache_key="work_project_analyzer"
        )
        
        logger.info("WorkProjectService初始化完成")
    
    async def analyze_project(
        self,
        user_id: str,
        doc_paths: List[str],
        project_name: str,
        user_prompt: Optional[str] = None
    ) -> ProjectAnalysisResult:
        """分析项目
        
        Args:
            user_id: 用户ID（用于日志记录）
            doc_paths: 文档路径列表
            project_name: 项目名称
            user_prompt: 用户自定义提示词（如"重点分析架构"）
            
        Returns:
            项目分析结果
        """
        logger.info(f"用户 {user_id} 开始分析项目: {project_name}")
        
        try:
            # 调用ProjectAnalyzer能力
            analysis = await self.project_analyzer.analyze(
                doc_paths=doc_paths,
                project_name=project_name,
                custom_prompt=user_prompt
            )
            
            # 转换为服务层结果对象
            result = ProjectAnalysisResult(
                markdown_content=analysis.markdown_content,
                entities=analysis.entities,
                concepts=analysis.concepts,
                analyzed_at=analysis.analyzed_at
            )
            
            logger.info(f"项目 {project_name} 分析完成，提取到 {len(result.entities)} 个实体")
            return result
            
        except Exception as e:
            logger.error(f"项目分析失败: {e}")
            raise
    
    async def batch_analyze_projects(
        self,
        user_id: str,
        projects: List[dict]
    ) -> List[ProjectAnalysisResult]:
        """批量分析项目
        
        Args:
            user_id: 用户ID
            projects: 项目列表，每个项目包含:
                - name: 项目名称
                - doc_paths: 文档路径列表
                - custom_prompt: 自定义提示词（可选）
                
        Returns:
            项目分析结果列表
        """
        logger.info(f"用户 {user_id} 批量分析 {len(projects)} 个项目")
        
        results = []
        for project in projects:
            try:
                result = await self.analyze_project(
                    user_id=user_id,
                    doc_paths=project["doc_paths"],
                    project_name=project["name"],
                    user_prompt=project.get("custom_prompt")
                )
                results.append(result)
            except Exception as e:
                logger.error(f"项目 {project['name']} 分析失败: {e}")
                continue
        
        logger.info(f"批量分析完成，成功 {len(results)}/{len(projects)} 个项目")
        return results
