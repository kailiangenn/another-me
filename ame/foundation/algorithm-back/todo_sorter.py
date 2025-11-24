"""
待办排序算法 - 基于拓扑排序和优先级的智能排序

Enhancements:
- 支持可配置权重
- 支持自定义评分函数
- 优化的紧急度计算
"""

from typing import List, Dict, Set, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from loguru import logger


class Priority(Enum):
    """优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


@dataclass
class TodoItem:
    """待办项"""
    id: str
    title: str
    priority: Priority           # 优先级
    due_date: Optional[datetime] = None  # 截止日期
    dependencies: List[str] = None  # 依赖的task_id列表
    status: TaskStatus = TaskStatus.PENDING
    description: str = ""
    created_at: datetime = None
    
    def __post_init__(self):
        """初始化"""
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # 转换字符串优先级为枚举
        if isinstance(self.priority, str):
            self.priority = Priority(self.priority)
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)


@dataclass
class SortedTodoList:
    """排序后的待办列表"""
    sorted_todos: List[TodoItem]  # 排序后的列表
    groups: Dict[str, List[TodoItem]]  # 按优先级分组
    blocked_todos: List[TodoItem]  # 被阻塞的待办（存在循环依赖）
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TodoSorter:
    """待办排序器（拓扑排序 + 优先级）
    
    Enhancements:
    - 支持可配置权重
    - 支持自定义评分函数
    """
    
    def __init__(
        self,
        urgency_weight: float = 0.4,
        importance_weight: float = 0.4,
        dependency_weight: float = 0.2,
        custom_scorer: Optional[Callable[[TodoItem], float]] = None
    ):
        """
        初始化
        
        Args:
            urgency_weight: 紧急度权重
            importance_weight: 重要性权重
            dependency_weight: 依赖关系权重
            custom_scorer: 自定义评分函数
        """
        # 权重归一化
        total = urgency_weight + importance_weight + dependency_weight
        self.urgency_weight = urgency_weight / total
        self.importance_weight = importance_weight / total
        self.dependency_weight = dependency_weight / total
        self.custom_scorer = custom_scorer
        
        logger.info(
            f"TodoSorter初始化: 紧急度={self.urgency_weight:.2f}, "
            f"重要性={self.importance_weight:.2f}, "
            f"依赖关系={self.dependency_weight:.2f}"
        )
    
    def set_weights(
        self,
        urgency_weight: float,
        importance_weight: float,
        dependency_weight: float
    ) -> None:
        """
        设置权重
        
        Args:
            urgency_weight: 紧急度权重
            importance_weight: 重要性权重
            dependency_weight: 依赖关系权重
        """
        total = urgency_weight + importance_weight + dependency_weight
        self.urgency_weight = urgency_weight / total
        self.importance_weight = importance_weight / total
        self.dependency_weight = dependency_weight / total
        
        logger.info(
            f"更新权重: 紧急度={self.urgency_weight:.2f}, "
            f"重要性={self.importance_weight:.2f}, "
            f"依赖关系={self.dependency_weight:.2f}"
        )
    
    def set_custom_scorer(self, scorer: Callable[[TodoItem], float]) -> None:
        """
        设置自定义评分函数
        
        Args:
            scorer: 自定义评分函数 (todo: TodoItem) -> float
        """
        self.custom_scorer = scorer
        logger.info("已设置自定义评分函数")
    
    def sort(
        self, 
        todos: List[TodoItem],
        consider_dependencies: bool = True,
        consider_due_date: bool = True
    ) -> SortedTodoList:
        """排序待办
        
        Args:
            todos: 待办列表
            consider_dependencies: 是否考虑依赖关系
            consider_due_date: 是否考虑截止日期
            
        Returns:
            排序后的待办列表
        """
        if not todos:
            return SortedTodoList(
                sorted_todos=[],
                groups={},
                blocked_todos=[],
                metadata={"total": 0}
            )
        
        # 过滤掉已完成的任务
        pending_todos = [t for t in todos if t.status != TaskStatus.COMPLETED]
        
        if consider_dependencies:
            sorted_todos, blocked = self._topological_sort(
                pending_todos,
                consider_due_date=consider_due_date
            )
        else:
            sorted_todos = self._priority_sort(
                pending_todos,
                consider_due_date=consider_due_date
            )
            blocked = []
        
        # 按优先级分组
        groups = self._group_by_priority(sorted_todos)
        
        return SortedTodoList(
            sorted_todos=sorted_todos,
            groups=groups,
            blocked_todos=blocked,
            metadata={
                "total": len(sorted_todos),
                "blocked": len(blocked),
                "consider_dependencies": consider_dependencies,
                "consider_due_date": consider_due_date
            }
        )
    
    def _topological_sort(
        self, 
        todos: List[TodoItem],
        consider_due_date: bool = True
    ) -> tuple[List[TodoItem], List[TodoItem]]:
        """拓扑排序（处理依赖关系）
        
        使用Kahn算法确保A依赖B时，B排在A前面
        
        Args:
            todos: 待办列表
            consider_due_date: 是否考虑截止日期
            
        Returns:
            (排序后的列表, 被阻塞的任务列表)
        """
        # 构建依赖图
        graph = {todo.id: todo for todo in todos}
        in_degree = {todo.id: 0 for todo in todos}
        out_edges = {todo.id: [] for todo in todos}
        
        # 计算入度和出边
        for todo in todos:
            for dep_id in todo.dependencies:
                if dep_id in graph:  # 只考虑存在的依赖
                    in_degree[todo.id] += 1
                    out_edges[dep_id].append(todo.id)
                else:
                    logger.warning(f"任务 {todo.id} 依赖的任务 {dep_id} 不存在")
        
        # Kahn算法
        queue = [tid for tid, degree in in_degree.items() if degree == 0]
        sorted_ids = []
        
        while queue:
            # 按优先级和截止日期排序
            queue.sort(
                key=lambda tid: self._priority_score(
                    graph[tid],
                    consider_due_date=consider_due_date
                ),
                reverse=True  # 高分在前
            )
            
            current_id = queue.pop(0)
            sorted_ids.append(current_id)
            
            # 减少依赖此任务的其他任务的入度
            for next_id in out_edges[current_id]:
                in_degree[next_id] -= 1
                if in_degree[next_id] == 0:
                    queue.append(next_id)
        
        # 检查是否有循环依赖
        sorted_todos = [graph[tid] for tid in sorted_ids]
        blocked_todos = [graph[tid] for tid in graph.keys() if tid not in sorted_ids]
        
        if blocked_todos:
            logger.warning(f"发现 {len(blocked_todos)} 个被阻塞的任务（可能存在循环依赖）")
        
        return sorted_todos, blocked_todos
    
    def _priority_sort(
        self, 
        todos: List[TodoItem],
        consider_due_date: bool = True
    ) -> List[TodoItem]:
        """简单优先级排序（不考虑依赖）
        
        Args:
            todos: 待办列表
            consider_due_date: 是否考虑截止日期
            
        Returns:
            排序后的列表
        """
        return sorted(
            todos,
            key=lambda t: self._priority_score(t, consider_due_date=consider_due_date),
            reverse=True  # 高分在前
        )
    
    def _priority_score(
        self, 
        todo: TodoItem,
        consider_due_date: bool = True
    ) -> float:
        """计算优先级分数
        
        综合考虑优先级、截止日期等因素
        
        Args:
            todo: 待办项
            consider_due_date: 是否考虑截止日期
            
        Returns:
            优先级分数（越高越优先）
        """
        # 如果有自定义评分函数，使用它
        if self.custom_scorer:
            return self.custom_scorer(todo)
        
        # 基础优先级分数（重要性）
        priority_map = {
            Priority.HIGH: 100,
            Priority.MEDIUM: 50,
            Priority.LOW: 10
        }
        importance_score = priority_map.get(todo.priority, 10)
        
        # 计算紧急度分数
        urgency_score = self._calc_urgency(todo) if consider_due_date else 0
        
        # 计算依赖关系分数（依赖越少分数越高）
        dependency_score = 100 - (len(todo.dependencies) * 10)
        dependency_score = max(0, dependency_score)
        
        # 加权综合分数
        total_score = (
            self.importance_weight * importance_score +
            self.urgency_weight * urgency_score +
            self.dependency_weight * dependency_score
        )
        
        return total_score
    
    def _calc_urgency(self, todo: TodoItem) -> float:
        """
        计算紧急度分数
        
        Args:
            todo: 待办项
            
        Returns:
            紧急度分数 (0-100)
        """
        if not todo.due_date:
            return 0
        
        days_left = (todo.due_date - datetime.now()).days
        
        if days_left < 0:
            # 已过期，最高紧急度
            return 100
        elif days_left == 0:
            # 今天到期
            return 90
        elif days_left == 1:
            # 明天到期
            return 80
        elif days_left <= 3:
            # 3天内到期
            return 70 - (days_left * 5)
        elif days_left <= 7:
            # 一周内到期
            return 50 - ((days_left - 3) * 5)
        elif days_left <= 14:
            # 两周内到期
            return 30 - ((days_left - 7) * 2)
        elif days_left <= 30:
            # 一月内到期
            return max(0, 20 - ((days_left - 14) // 2))
        else:
            # 超过一月
            return 0
    
    def _group_by_priority(self, todos: List[TodoItem]) -> Dict[str, List[TodoItem]]:
        """按优先级分组
        
        Args:
            todos: 待办列表
            
        Returns:
            优先级分组字典
        """
        groups = {
            "high": [],
            "medium": [],
            "low": []
        }
        
        for todo in todos:
            priority_key = todo.priority.value
            if priority_key in groups:
                groups[priority_key].append(todo)
        
        return groups
    
    def _find_blocked(self, todos: List[TodoItem]) -> List[TodoItem]:
        """查找被阻塞的任务
        
        Args:
            todos: 待办列表
            
        Returns:
            被阻塞的任务列表
        """
        # 简单实现：检查依赖是否都已完成
        todo_dict = {t.id: t for t in todos}
        blocked = []
        
        for todo in todos:
            if todo.status == TaskStatus.PENDING:
                for dep_id in todo.dependencies:
                    dep_task = todo_dict.get(dep_id)
                    if dep_task and dep_task.status != TaskStatus.COMPLETED:
                        blocked.append(todo)
                        break
        
        return blocked
