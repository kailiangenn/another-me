"""
待办事项管理服务
职责: 智能整理、优先级排序

设计: 通过 CapabilityFactory 注入能力
"""
from typing import List, Dict, Optional
import logging

from ame.capabilities.factory import CapabilityFactory
from ame.capabilities.intent import IntentRecognizer
from ame.models.report_models import OrganizedTodos, TaskInfo

logger = logging.getLogger(__name__)


class TodoService:
    """待办事项管理服务"""
    
    def __init__(self, capability_factory: CapabilityFactory):
        self.factory = capability_factory
        self.llm = factory.llm
        self.intent_recognizer = factory.create_intent_recognizer(cache_key="todo_intent")
        logger.info("TodoService 初始化完成")
    
    async def organize_todos(
        self,
        raw_todos: List[str],
        context: Optional[Dict] = None
    ) -> OrganizedTodos:
        """
        智能整理待办事项
        
        Args:
            raw_todos: 原始待办列表
            context: 上下文信息
        
        Returns:
            OrganizedTodos: 整理后的待办事项
        """
        # Step 1: 任务解析
        parsed_tasks = []
        for todo in raw_todos:
            task_info = await self._parse_task(todo)
            parsed_tasks.append(task_info)
        
        # Step 2: 优先级评估
        prioritized = await self._prioritize_tasks(parsed_tasks, context)
        
        # Step 3: 智能分组
        high_priority = [t for t in prioritized if t.priority_score >= 70]
        medium_priority = [t for t in prioritized if 40 <= t.priority_score < 70]
        low_priority = [t for t in prioritized if t.priority_score < 40]
        
        # Step 4: 生成格式化文本
        formatted_text = self._format_todos(high_priority, medium_priority, low_priority)
        
        return OrganizedTodos(
            high_priority=high_priority,
            medium_priority=medium_priority,
            low_priority=low_priority,
            formatted_text=formatted_text,
            original_count=len(raw_todos),
            organized_count=len(prioritized)
        )
    
    async def _parse_task(self, todo: str) -> TaskInfo:
        """解析单个任务"""
        if self.intent_recognizer:
            intent_result = await self.intent_recognizer.recognize(todo)
            return TaskInfo(
                content=todo,
                entities=intent_result.entities,
                category=intent_result.metadata.get("category")
            )
        else:
            return TaskInfo(content=todo)
    
    async def _prioritize_tasks(
        self,
        tasks: List[TaskInfo],
        context: Optional[Dict]
    ) -> List[TaskInfo]:
        """
        任务优先级算法
        
        评分规则:
        1. 紧急度 (0-40分)
        2. 重要性 (0-40分)
        3. 依赖关系 (0-20分)
        """
        for task in tasks:
            score = 0
            
            # 紧急度评分
            urgency_keywords = {
                "紧急": 40, "今天": 40, "ASAP": 40, "asap": 40,
                "明天": 30, "本周": 25, "近期": 15
            }
            for keyword, points in urgency_keywords.items():
                if keyword in task.content:
                    score += points
                    break
            
            # 重要性评分
            importance_keywords = {
                "重要": 30, "关键": 30, "核心": 25,
                "优先": 20, "必须": 20
            }
            for keyword, points in importance_keywords.items():
                if keyword in task.content:
                    score += points
                    break
            
            # 依赖关系评分
            if task.is_blocking_others:
                score += 20
            elif task.has_dependencies:
                score -= 10
            
            task.priority_score = min(score, 100)
        
        return sorted(tasks, key=lambda t: t.priority_score, reverse=True)
    
    def _format_todos(
        self,
        high: List[TaskInfo],
        medium: List[TaskInfo],
        low: List[TaskInfo]
    ) -> str:
        """格式化为 Markdown"""
        result = "# 整理后的待办事项\n\n"
        
        if high:
            result += "## 🔴 高优先级\n\n"
            for task in high:
                result += f"- [ ] {task.content}\n"
            result += "\n"
        
        if medium:
            result += "## 🟡 中优先级\n\n"
            for task in medium:
                result += f"- [ ] {task.content}\n"
            result += "\n"
        
        if low:
            result += "## 🟢 低优先级\n\n"
            for task in low:
                result += f"- [ ] {task.content}\n"
            result += "\n"
        
        return result
