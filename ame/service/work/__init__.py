"""
Work服务模块

包含：
- WorkProjectService: 项目认知服务
- WorkTodoService: 待办管理服务
- WorkAdviceService: 工作建议服务
"""

from .project import WorkProjectService, ProjectAnalysisResult
from .todo import WorkTodoService
from .suggest import WorkAdviceService

__all__ = [
    "WorkProjectService",
    "ProjectAnalysisResult",
    "WorkTodoService",
    "WorkAdviceService",
]
