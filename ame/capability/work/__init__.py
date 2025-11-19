"""
Work能力模块

包含：
- ProjectAnalyzer: 项目分析器
- TodoManager: 待办管理器
- AdviceGenerator: 建议生成器
"""

from .project_analyzer import ProjectAnalyzer, ProjectAnalysis
from .todo_manager import TodoManager
from .advice_generator import (
    AdviceGenerator,
    AdviceReport,
    WorkPattern,
    TimeRange
)

__all__ = [
    "ProjectAnalyzer",
    "ProjectAnalysis",
    "TodoManager",
    "AdviceGenerator",
    "AdviceReport",
    "WorkPattern",
    "TimeRange",
]
