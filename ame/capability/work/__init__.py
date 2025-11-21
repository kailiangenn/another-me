"""
Work能力模块

包含：
- ProjectAnalyzer: 项目分析器
- TodoManager: 待办管理器
- AdviceGenerator: 建议生成器
"""

from .document_parser import DocumentParser, DocumentParseResult
from .project_analyzer import ProjectAnalyzer, ProjectAnalysis
from .todo_parser import TodoParser
from .todo_manager import TodoManager
from .pattern_analyzer import PatternAnalyzer, WorkPattern, PatternAnalysisReport
from .advice_generator import (
    AdviceGenerator,
    AdviceReport,
    TimeRange
)

__all__ = [
    "DocumentParser",
    "DocumentParseResult",
    "ProjectAnalyzer",
    "ProjectAnalysis",
    "TodoParser",
    "TodoManager",
    "PatternAnalyzer",
    "WorkPattern",
    "PatternAnalysisReport",
    "AdviceGenerator",
    "AdviceReport",
    "TimeRange",
]
