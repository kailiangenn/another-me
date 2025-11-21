"""
模式分析器 - 分析用户的工作模式和习惯

从WorkGraph中提取历史数据,分析用户的工作习惯、时间偏好、效率模式等。
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from loguru import logger

from ame.foundation.storage import GraphStoreBase
from ame.foundation.algorithm import TodoItem, TaskStatus, Priority


@dataclass
class WorkPattern:
    """工作模式"""
    pattern_type: str                      # 模式类型(time/priority/completion等)
    description: str                        # 模式描述
    confidence: float                       # 置信度(0-1)
    evidence: List[str] = field(default_factory=list)  # 证据
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PatternAnalysisReport:
    """模式分析报告"""
    user_id: str
    time_range: str                        # 分析时间范围
    patterns: List[WorkPattern] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    analyzed_at: datetime = field(default_factory=datetime.now)


class PatternAnalyzer:
    """工作模式分析器
    
    分析用户的工作习惯和模式:
    - 工作时间偏好
    - 任务优先级分布
    - 完成率和拖延模式
    - 高效时段识别
    """
    
    def __init__(self, graph_store: GraphStoreBase):
        """初始化
        
        Args:
            graph_store: 图存储(WorkGraph)
        """
        self.graph = graph_store
        logger.debug("PatternAnalyzer初始化完成")
    
    async def analyze(
        self,
        user_id: str,
        days: int = 30,
        min_tasks: int = 5
    ) -> PatternAnalysisReport:
        """分析用户工作模式
        
        Args:
            user_id: 用户ID
            days: 分析的天数范围
            min_tasks: 最少任务数(低于此数量则置信度降低)
            
        Returns:
            模式分析报告
        """
        logger.info(f"开始分析用户 {user_id} 的工作模式(最近{days}天)")
        
        # 1. 获取历史任务数据
        tasks = await self._fetch_historical_tasks(user_id, days)
        
        if len(tasks) < min_tasks:
            logger.warning(f"任务数量不足({len(tasks)} < {min_tasks}),分析置信度较低")
        
        # 2. 分析各类模式
        patterns = []
        
        # 时间模式
        time_patterns = self._analyze_time_patterns(tasks)
        patterns.extend(time_patterns)
        
        # 优先级模式
        priority_patterns = self._analyze_priority_patterns(tasks)
        patterns.extend(priority_patterns)
        
        # 完成模式
        completion_patterns = self._analyze_completion_patterns(tasks)
        patterns.extend(completion_patterns)
        
        # 拖延模式
        procrastination_patterns = self._analyze_procrastination_patterns(tasks)
        patterns.extend(procrastination_patterns)
        
        # 3. 生成统计数据
        statistics = self._generate_statistics(tasks)
        
        # 4. 生成建议
        suggestions = self._generate_suggestions(patterns, statistics)
        
        report = PatternAnalysisReport(
            user_id=user_id,
            time_range=f"最近{days}天",
            patterns=patterns,
            statistics=statistics,
            suggestions=suggestions
        )
        
        logger.info(f"模式分析完成: 发现 {len(patterns)} 个模式")
        return report
    
    async def _fetch_historical_tasks(
        self,
        user_id: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """获取历史任务数据
        
        Args:
            user_id: 用户ID
            days: 天数
            
        Returns:
            任务数据列表
        """
        try:
            # 计算起始时间
            start_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Cypher查询
            query = """
            MATCH (u:User {id: $user_id})-[:HAS_TASK]->(t:Task)
            WHERE t.created_at >= $start_date
            RETURN t
            ORDER BY t.created_at DESC
            """
            
            params = {
                "user_id": user_id,
                "start_date": start_date
            }
            
            result = await self.graph.execute_query(query, params)
            
            tasks = []
            if result and "data" in result:
                for row in result["data"]:
                    task_node = row.get("t")
                    if task_node:
                        tasks.append(task_node.properties)
            
            return tasks
            
        except Exception as e:
            logger.error(f"获取历史任务失败: {e}")
            return []
    
    def _analyze_time_patterns(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkPattern]:
        """分析时间模式
        
        Args:
            tasks: 任务列表
            
        Returns:
            时间模式列表
        """
        patterns = []
        
        if not tasks:
            return patterns
        
        # 统计创建任务的时间分布
        hour_counter = Counter()
        
        for task in tasks:
            created_at_str = task.get("created_at")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                    hour_counter[created_at.hour] += 1
                except Exception:
                    continue
        
        if not hour_counter:
            return patterns
        
        # 找出高峰时段
        peak_hours = hour_counter.most_common(3)
        
        if peak_hours:
            peak_hour, count = peak_hours[0]
            confidence = min(count / len(tasks), 1.0)
            
            # 判断时段
            if 6 <= peak_hour < 12:
                time_desc = "早晨(6-12点)"
            elif 12 <= peak_hour < 18:
                time_desc = "下午(12-18点)"
            elif 18 <= peak_hour < 22:
                time_desc = "晚上(18-22点)"
            else:
                time_desc = "深夜(22-6点)"
            
            pattern = WorkPattern(
                pattern_type="time_preference",
                description=f"倾向于在{time_desc}创建任务",
                confidence=confidence,
                evidence=[f"{peak_hour}点创建了{count}个任务"],
                metadata={"peak_hours": [h for h, _ in peak_hours]}
            )
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_priority_patterns(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkPattern]:
        """分析优先级模式
        
        Args:
            tasks: 任务列表
            
        Returns:
            优先级模式列表
        """
        patterns = []
        
        if not tasks:
            return patterns
        
        # 统计优先级分布
        priority_counter = Counter()
        
        for task in tasks:
            priority = task.get("priority", "medium")
            priority_counter[priority] += 1
        
        total = len(tasks)
        
        # 分析主要优先级偏好
        most_common_priority, count = priority_counter.most_common(1)[0]
        ratio = count / total
        
        if ratio > 0.6:
            pattern = WorkPattern(
                pattern_type="priority_preference",
                description=f"大多数任务({ratio*100:.1f}%)设置为{most_common_priority}优先级",
                confidence=ratio,
                evidence=[f"{count}/{total}个任务为{most_common_priority}优先级"],
                metadata={"priority_distribution": dict(priority_counter)}
            )
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_completion_patterns(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkPattern]:
        """分析完成模式
        
        Args:
            tasks: 任务列表
            
        Returns:
            完成模式列表
        """
        patterns = []
        
        if not tasks:
            return patterns
        
        # 统计完成率
        completed_count = sum(1 for t in tasks if t.get("status") == "completed")
        total_count = len(tasks)
        completion_rate = completed_count / total_count if total_count > 0 else 0
        
        # 分析完成时长
        completion_times = []
        for task in tasks:
            if task.get("status") == "completed":
                created_str = task.get("created_at")
                completed_str = task.get("completed_at")
                
                if created_str and completed_str:
                    try:
                        created = datetime.fromisoformat(created_str)
                        completed = datetime.fromisoformat(completed_str)
                        duration = (completed - created).total_seconds() / 3600  # 小时
                        completion_times.append(duration)
                    except Exception:
                        continue
        
        # 完成率模式
        if completion_rate >= 0.7:
            desc = "高完成率"
            confidence = completion_rate
        elif completion_rate >= 0.4:
            desc = "中等完成率"
            confidence = 0.6
        else:
            desc = "低完成率"
            confidence = 0.7
        
        pattern = WorkPattern(
            pattern_type="completion_rate",
            description=f"{desc}: {completion_rate*100:.1f}%的任务已完成",
            confidence=confidence,
            evidence=[f"{completed_count}/{total_count}个任务已完成"],
            metadata={"completion_rate": completion_rate}
        )
        patterns.append(pattern)
        
        # 平均完成时长模式
        if completion_times:
            avg_time = sum(completion_times) / len(completion_times)
            pattern = WorkPattern(
                pattern_type="completion_speed",
                description=f"平均任务完成时长: {avg_time:.1f}小时",
                confidence=0.7,
                evidence=[f"基于{len(completion_times)}个已完成任务"],
                metadata={"avg_completion_hours": avg_time}
            )
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_procrastination_patterns(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[WorkPattern]:
        """分析拖延模式
        
        Args:
            tasks: 任务列表
            
        Returns:
            拖延模式列表
        """
        patterns = []
        
        if not tasks:
            return patterns
        
        # 统计逾期任务
        now = datetime.now()
        overdue_count = 0
        
        for task in tasks:
            if task.get("status") != "completed":
                due_date_str = task.get("due_date")
                if due_date_str:
                    try:
                        due_date = datetime.fromisoformat(due_date_str)
                        if due_date < now:
                            overdue_count += 1
                    except Exception:
                        continue
        
        if overdue_count > 0:
            total = len([t for t in tasks if t.get("due_date")])
            ratio = overdue_count / total if total > 0 else 0
            
            pattern = WorkPattern(
                pattern_type="procrastination",
                description=f"存在拖延倾向: {overdue_count}个任务已逾期",
                confidence=min(ratio, 0.9),
                evidence=[f"{overdue_count}个任务超过截止日期"],
                metadata={"overdue_count": overdue_count, "overdue_ratio": ratio}
            )
            patterns.append(pattern)
        
        return patterns
    
    def _generate_statistics(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成统计数据
        
        Args:
            tasks: 任务列表
            
        Returns:
            统计数据
        """
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "completed")
        in_progress = sum(1 for t in tasks if t.get("status") == "in_progress")
        pending = sum(1 for t in tasks if t.get("status") == "pending")
        
        return {
            "total_tasks": total,
            "completed_tasks": completed,
            "in_progress_tasks": in_progress,
            "pending_tasks": pending,
            "completion_rate": completed / total if total > 0 else 0
        }
    
    def _generate_suggestions(
        self,
        patterns: List[WorkPattern],
        statistics: Dict[str, Any]
    ) -> List[str]:
        """根据模式生成建议
        
        Args:
            patterns: 模式列表
            statistics: 统计数据
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # 根据完成率给建议
        completion_rate = statistics.get("completion_rate", 0)
        if completion_rate < 0.5:
            suggestions.append("您的任务完成率较低,建议减少同时进行的任务数量,专注于优先级高的任务。")
        
        # 根据拖延模式给建议
        has_procrastination = any(p.pattern_type == "procrastination" for p in patterns)
        if has_procrastination:
            suggestions.append("检测到拖延倾向,建议为任务设置更合理的截止日期,并使用番茄工作法提高执行力。")
        
        # 根据时间偏好给建议
        time_patterns = [p for p in patterns if p.pattern_type == "time_preference"]
        if time_patterns:
            peak_hours = time_patterns[0].metadata.get("peak_hours", [])
            if peak_hours:
                suggestions.append(f"您倾向于在{peak_hours[0]}点左右创建任务,建议在此时段处理重要工作。")
        
        # 默认建议
        if not suggestions:
            suggestions.append("继续保持良好的工作习惯!")
        
        return suggestions
