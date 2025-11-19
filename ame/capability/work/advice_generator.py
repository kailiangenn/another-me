"""
建议生成器 - 基于WorkGraph数据统计生成工作建议报告
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from loguru import logger

from ame.foundation.llm import LLMCallerBase
from ame.foundation.storage import GraphStoreBase


@dataclass
class TimeRange:
    """时间范围"""
    start: datetime
    end: datetime
    
    @classmethod
    def last_30_days(cls):
        """最近30天"""
        return cls(
            start=datetime.now() - timedelta(days=30),
            end=datetime.now()
        )
    
    @classmethod
    def last_7_days(cls):
        """最近7天"""
        return cls(
            start=datetime.now() - timedelta(days=7),
            end=datetime.now()
        )
    
    @classmethod
    def custom(cls, start: datetime, end: datetime):
        """自定义时间范围"""
        return cls(start=start, end=end)


@dataclass
class WorkPattern:
    """工作模式分析"""
    avg_completion_time: float          # 平均完成时间（天）
    delay_rate: float                   # 延期率 0-1
    active_hours: List[int] = field(default_factory=list)  # 活跃时段
    preferred_domains: List[str] = field(default_factory=list)  # 偏好领域
    efficiency_score: float = 0.0       # 效率评分 0-100
    total_tasks: int = 0                # 总任务数
    completed_tasks: int = 0            # 已完成任务数
    pending_tasks: int = 0              # 待办任务数
    overdue_tasks: int = 0              # 逾期任务数


@dataclass
class AdviceReport:
    """建议报告"""
    efficiency_analysis: str                    # 效率分析
    capability_assessment: str                  # 能力评估
    improvement_suggestions: List[str] = field(default_factory=list)  # 改进建议
    pattern: Optional[WorkPattern] = None
    generated_at: datetime = field(default_factory=datetime.now)
    time_range: Optional[TimeRange] = None


class AdviceGenerator:
    """建议生成器
    
    基于WorkGraph数据分析生成工作建议。
    """
    
    def __init__(
        self,
        llm_caller: LLMCallerBase,
        graph_store: GraphStoreBase
    ):
        """初始化
        
        Args:
            llm_caller: LLM调用器
            graph_store: 图存储（WorkGraph）
        """
        self.llm = llm_caller
        self.graph = graph_store
        logger.debug("AdviceGenerator初始化完成")
    
    async def generate(
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
        if not time_range:
            time_range = TimeRange.last_30_days()
        
        logger.info(f"为用户 {user_id} 生成工作建议，时间范围: {time_range.start} ~ {time_range.end}")
        
        # 1. 从WorkGraph统计数据
        pattern = await self._analyze_work_pattern(user_id, time_range)
        
        # 2. 使用LLM生成个性化建议
        advice = await self._generate_advice_with_llm(user_id, pattern, time_range)
        
        return advice
    
    async def _analyze_work_pattern(
        self,
        user_id: str,
        time_range: TimeRange
    ) -> WorkPattern:
        """分析工作模式
        
        Args:
            user_id: 用户ID
            time_range: 时间范围
            
        Returns:
            工作模式分析结果
        """
        try:
            # 统计任务数量
            stats = await self._query_task_statistics(user_id, time_range)
            
            # 计算效率指标
            total_tasks = stats.get("total_tasks", 0)
            completed_tasks = stats.get("completed_tasks", 0)
            pending_tasks = stats.get("pending_tasks", 0)
            overdue_tasks = stats.get("overdue_tasks", 0)
            
            # 计算延期率
            delay_rate = (overdue_tasks / total_tasks) if total_tasks > 0 else 0
            
            # 计算完成率
            completion_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0
            
            # 计算效率评分（综合考虑完成率和延期率）
            efficiency_score = max(0, min(100, (completion_rate * 100) - (delay_rate * 50)))
            
            # 计算平均完成时间
            avg_completion_time = stats.get("avg_completion_time", 0)
            
            # 获取偏好领域
            preferred_domains = stats.get("preferred_domains", [])
            
            return WorkPattern(
                avg_completion_time=avg_completion_time,
                delay_rate=delay_rate,
                active_hours=[],  # TODO: 需要更详细的时间数据支持
                preferred_domains=preferred_domains,
                efficiency_score=efficiency_score,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                pending_tasks=pending_tasks,
                overdue_tasks=overdue_tasks
            )
            
        except Exception as e:
            logger.error(f"分析工作模式失败: {e}")
            # 返回默认值
            return WorkPattern(
                avg_completion_time=0,
                delay_rate=0,
                efficiency_score=0
            )
    
    async def _query_task_statistics(
        self,
        user_id: str,
        time_range: TimeRange
    ) -> Dict:
        """查询任务统计数据
        
        Args:
            user_id: 用户ID
            time_range: 时间范围
            
        Returns:
            统计数据字典
        """
        try:
            # 构建Cypher查询
            query = """
            MATCH (u:User {id: $user_id})-[:HAS_TASK]->(t:Task)
            WHERE datetime(t.created_at) >= datetime($start_time) 
              AND datetime(t.created_at) <= datetime($end_time)
            WITH t,
                 CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END as is_completed,
                 CASE WHEN t.status = 'pending' THEN 1 ELSE 0 END as is_pending,
                 CASE WHEN t.due_date IS NOT NULL AND datetime(t.due_date) < datetime() AND t.status <> 'completed' THEN 1 ELSE 0 END as is_overdue
            RETURN 
                count(t) as total_tasks,
                sum(is_completed) as completed_tasks,
                sum(is_pending) as pending_tasks,
                sum(is_overdue) as overdue_tasks,
                collect(DISTINCT t.project_name) as projects
            """
            
            params = {
                "user_id": user_id,
                "start_time": time_range.start.isoformat(),
                "end_time": time_range.end.isoformat()
            }
            
            result = await self.graph.execute_query(query, params)
            
            if result and "data" in result and len(result["data"]) > 0:
                row = result["data"][0]
                
                # 查询平均完成时间（已完成任务）
                avg_time_query = """
                MATCH (u:User {id: $user_id})-[:HAS_TASK]->(t:Task)
                WHERE t.status = 'completed' 
                  AND datetime(t.created_at) >= datetime($start_time)
                  AND datetime(t.created_at) <= datetime($end_time)
                  AND t.updated_at IS NOT NULL
                WITH duration.between(datetime(t.created_at), datetime(t.updated_at)).days as days
                RETURN avg(days) as avg_days
                """
                
                avg_result = await self.graph.execute_query(avg_time_query, params)
                avg_completion_time = 0
                
                if avg_result and "data" in avg_result and len(avg_result["data"]) > 0:
                    avg_completion_time = avg_result["data"][0].get("avg_days", 0) or 0
                
                return {
                    "total_tasks": row.get("total_tasks", 0),
                    "completed_tasks": row.get("completed_tasks", 0),
                    "pending_tasks": row.get("pending_tasks", 0),
                    "overdue_tasks": row.get("overdue_tasks", 0),
                    "preferred_domains": [p for p in row.get("projects", []) if p],
                    "avg_completion_time": avg_completion_time
                }
            
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "pending_tasks": 0,
                "overdue_tasks": 0,
                "preferred_domains": [],
                "avg_completion_time": 0
            }
            
        except Exception as e:
            logger.error(f"查询任务统计数据失败: {e}")
            return {}
    
    async def _generate_advice_with_llm(
        self,
        user_id: str,
        pattern: WorkPattern,
        time_range: TimeRange
    ) -> AdviceReport:
        """使用LLM生成个性化建议
        
        Args:
            user_id: 用户ID
            pattern: 工作模式分析
            time_range: 时间范围
            
        Returns:
            建议报告
        """
        # 构建提示词
        prompt = f"""你是一位专业的工作效率顾问，请基于用户的工作数据分析，生成个性化的工作建议。

**统计时间范围:** {time_range.start.strftime('%Y-%m-%d')} 至 {time_range.end.strftime('%Y-%m-%d')}

**工作数据统计:**
- 总任务数: {pattern.total_tasks}
- 已完成任务: {pattern.completed_tasks}
- 待办任务: {pattern.pending_tasks}
- 逾期任务: {pattern.overdue_tasks}
- 平均完成时间: {pattern.avg_completion_time:.1f} 天
- 延期率: {pattern.delay_rate * 100:.1f}%
- 效率评分: {pattern.efficiency_score:.1f}/100
- 偏好领域: {', '.join(pattern.preferred_domains) if pattern.preferred_domains else '无'}

请生成以下内容：

1. **效率分析** (200字以内)
   - 分析用户的工作效率表现
   - 指出数据中反映的优势和不足

2. **能力评估** (200字以内)
   - 评估用户的任务管理能力
   - 分析工作模式和习惯

3. **改进建议** (3-5条具体建议)
   - 提供可操作的改进措施
   - 针对发现的问题给出解决方案

请直接输出内容，不要使用markdown标题，使用以下格式：
【效率分析】
...

【能力评估】
...

【改进建议】
1. ...
2. ...
3. ...
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(
                messages,
                max_tokens=1000,
                temperature=0.5
            )
            
            content = response.content.strip()
            
            # 解析响应
            efficiency_analysis = ""
            capability_assessment = ""
            suggestions = []
            
            # 简单的文本解析
            if "【效率分析】" in content:
                parts = content.split("【效率分析】")[1].split("【能力评估】")
                efficiency_analysis = parts[0].strip()
                
                if len(parts) > 1:
                    parts2 = parts[1].split("【改进建议】")
                    capability_assessment = parts2[0].strip()
                    
                    if len(parts2) > 1:
                        suggestions_text = parts2[1].strip()
                        # 提取建议列表
                        for line in suggestions_text.split("\n"):
                            line = line.strip()
                            if line and (line[0].isdigit() or line.startswith("-")):
                                # 去掉序号
                                suggestion = line.lstrip("0123456789.- ").strip()
                                if suggestion:
                                    suggestions.append(suggestion)
            else:
                # 如果格式不符合，直接使用全文作为效率分析
                efficiency_analysis = content
                capability_assessment = "基于当前数据，建议持续跟踪工作表现。"
                suggestions = ["继续保持良好的工作习惯", "定期回顾任务完成情况"]
            
            return AdviceReport(
                efficiency_analysis=efficiency_analysis or "分析中...",
                capability_assessment=capability_assessment or "评估中...",
                improvement_suggestions=suggestions,
                pattern=pattern,
                time_range=time_range
            )
            
        except Exception as e:
            logger.error(f"LLM生成建议失败: {e}")
            return AdviceReport(
                efficiency_analysis=f"效率评分: {pattern.efficiency_score:.1f}/100，完成率: {pattern.completed_tasks}/{pattern.total_tasks}",
                capability_assessment="建议继续跟踪工作表现以获得更准确的评估。",
                improvement_suggestions=[
                    "合理规划任务优先级",
                    "控制待办数量，避免过载",
                    "定期回顾任务进度"
                ],
                pattern=pattern,
                time_range=time_range
            )
