"""
工作建议服务 - 基于工作数据生成建议报告

遵循架构规范：
- 通过CapabilityFactory获取所有能力
- 不直接使用Foundation层组件
"""

from typing import Optional
from loguru import logger

from ame.capability.factory import CapabilityFactory
from ame.capability.work import AdviceReport, TimeRange


class WorkAdviceService:
    """工作建议服务
    
    遵循架构规范：
    - 通过CapabilityFactory获取所有能力
    - 不直接使用Foundation层组件
    """
    
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        llm_api_key: str,
        llm_model: str = "gpt-3.5-turbo",
        llm_base_url: Optional[str] = None,
        graph_host: str = "localhost",
        graph_port: int = 6379,
        graph_name: str = "work_graph",
        graph_password: Optional[str] = None
    ):
        """初始化
        
        Args:
            capability_factory: 能力工厂
            llm_api_key: LLM API密钥
            llm_model: LLM模型名称
            llm_base_url: LLM API基础URL
            graph_host: 图数据库主机
            graph_port: 图数据库端口
            graph_name: 图名称
            graph_password: 图数据库密码
        """
        self.factory = capability_factory
        
        # 通过工厂创建能力
        self.advice_generator = self.factory.create_advice_generator(
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
            graph_host=graph_host,
            graph_port=graph_port,
            graph_name=graph_name,
            graph_password=graph_password,
            cache_key="work_advice_generator"
        )
        
        logger.info("WorkAdviceService初始化完成")
    
    async def generate_advice(
        self,
        user_id: str,
        time_range: Optional[TimeRange] = None
    ) -> AdviceReport:
        """生成工作建议
        
        Args:
            user_id: 用户ID
            time_range: 统计时间范围（默认最近30天）
            
        Returns:
            建议报告
        """
        logger.info(f"用户 {user_id} 请求生成工作建议")
        
        try:
            report = await self.advice_generator.generate(
                user_id=user_id,
                time_range=time_range
            )
            
            logger.info(f"工作建议生成成功，效率评分: {report.pattern.efficiency_score:.1f}")
            return report
            
        except Exception as e:
            logger.error(f"生成工作建议失败: {e}")
            raise
    
    async def generate_weekly_advice(
        self,
        user_id: str
    ) -> AdviceReport:
        """生成周报建议（最近7天）
        
        Args:
            user_id: 用户ID
            
        Returns:
            建议报告
        """
        logger.info(f"用户 {user_id} 请求生成周报建议")
        
        return await self.generate_advice(
            user_id=user_id,
            time_range=TimeRange.last_7_days()
        )
    
    async def generate_monthly_advice(
        self,
        user_id: str
    ) -> AdviceReport:
        """生成月报建议（最近30天）
        
        Args:
            user_id: 用户ID
            
        Returns:
            建议报告
        """
        logger.info(f"用户 {user_id} 请求生成月报建议")
        
        return await self.generate_advice(
            user_id=user_id,
            time_range=TimeRange.last_30_days()
        )
    
    def format_advice_as_markdown(self, report: AdviceReport) -> str:
        """将建议报告格式化为Markdown
        
        Args:
            report: 建议报告
            
        Returns:
            Markdown格式的报告
        """
        pattern = report.pattern
        time_range = report.time_range
        
        # 构建Markdown内容
        md_content = f"""# 工作建议报告

**统计时间:** {time_range.start.strftime('%Y-%m-%d')} 至 {time_range.end.strftime('%Y-%m-%d')}

## 📊 工作数据概览

- **总任务数:** {pattern.total_tasks}
- **已完成:** {pattern.completed_tasks}
- **待办中:** {pattern.pending_tasks}
- **已逾期:** {pattern.overdue_tasks}
- **平均完成时间:** {pattern.avg_completion_time:.1f} 天
- **延期率:** {pattern.delay_rate * 100:.1f}%
- **效率评分:** {pattern.efficiency_score:.1f}/100

## 🎯 效率分析

{report.efficiency_analysis}

## 💪 能力评估

{report.capability_assessment}

## 💡 改进建议

"""
        
        for i, suggestion in enumerate(report.improvement_suggestions, 1):
            md_content += f"{i}. {suggestion}\n"
        
        md_content += f"\n---\n*报告生成时间: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return md_content
    
    async def generate_formatted_advice(
        self,
        user_id: str,
        time_range: Optional[TimeRange] = None
    ) -> str:
        """生成格式化的工作建议（Markdown格式）
        
        Args:
            user_id: 用户ID
            time_range: 统计时间范围
            
        Returns:
            Markdown格式的建议报告
        """
        report = await self.generate_advice(user_id, time_range)
        return self.format_advice_as_markdown(report)
