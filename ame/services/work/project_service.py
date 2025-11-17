"""
项目进度追踪服务
职责: 项目状态分析、时间线生成、风险识别
"""
from typing import List, Dict
from datetime import datetime

from ame.capabilities.factory import CapabilityFactory
from ame.models.report_models import ProjectProgress


class ProjectService:
    """项目进度追踪服务"""
    
    def __init__(self, capability_factory: CapabilityFactory):
        """初始化项目进度追踪服务
        
        Args:
            capability_factory: 能力工厂实例
        """
        self.factory = capability_factory
        
        # 使用 advanced pipeline 进行项目相关文档检索
        self.retriever = capability_factory.create_retriever(
            pipeline_mode="advanced",
            cache_key="project_retriever"
        )
        
        # 数据分析器，用于项目状态分析
        self.analyzer = capability_factory.create_data_analyzer(
            with_retriever=True,
            cache_key="project_analyzer"
        )
    
    async def track_progress(
        self,
        project_name: str,
        user_id: str
    ) -> ProjectProgress:
        """
        追踪项目进度
        
        Args:
            project_name: 项目名称
            user_id: 用户ID
        
        Returns:
            ProjectProgress: 项目进度对象
        """
        # Step 1: 检索项目相关记录
        project_docs = await self.retriever.retrieve(
            query=f"项目:{project_name}",
            top_k=50,
            filters={"user_id": user_id}
        )
        
        # Step 2: 状态分析
        status_stats = self._analyze_project_status(project_docs)
        
        # Step 3: 时间线生成
        timeline = self._generate_project_timeline(project_docs)
        
        # Step 4: 风险识别
        risks = self._identify_project_risks(project_docs, timeline)
        
        # Step 5: 生成进度报告
        report = self._generate_project_report(
            project_name, status_stats, timeline, risks
        )
        
        return ProjectProgress(
            project_name=project_name,
            completion_rate=status_stats.get("completion_rate", 0.0),
            status=status_stats,
            timeline=timeline,
            risks=risks,
            report=report
        )
    
    def _analyze_project_status(self, docs: List) -> Dict[str, any]:
        """分析项目状态"""
        total = len(docs)
        return {
            "total_tasks": total,
            "completed": 0,
            "in_progress": total,
            "completion_rate": 0.0
        }
    
    def _generate_project_timeline(self, docs: List) -> List[Dict]:
        """生成项目时间线"""
        timeline = []
        for doc in docs[:10]:
            timeline.append({
                "date": doc.timestamp.isoformat() if hasattr(doc, 'timestamp') else datetime.now().isoformat(),
                "event": "项目活动",
                "description": doc.content[:50] if hasattr(doc, 'content') else ""
            })
        return timeline
    
    def _identify_project_risks(
        self,
        docs: List,
        timeline: List[Dict]
    ) -> List[str]:
        """识别项目风险"""
        risks = []
        if len(docs) < 5:
            risks.append("项目记录较少，可能存在进度跟踪不足的风险")
        return risks
    
    def _generate_project_report(
        self,
        project_name: str,
        status: Dict,
        timeline: List[Dict],
        risks: List[str]
    ) -> str:
        """生成项目进度报告"""
        report = f"# {project_name} 项目进度报告\n\n"
        report += f"**完成率**: {status.get('completion_rate', 0) * 100:.1f}%\n\n"
        report += f"**总任务数**: {status.get('total_tasks', 0)}\n\n"
        
        if risks:
            report += "## 风险提示\n\n"
            for risk in risks:
                report += f"- {risk}\n"
        
        return report
