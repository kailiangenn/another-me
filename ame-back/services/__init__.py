"""
Services Layer - 业务服务层

提供面向具体业务场景的高层服务

服务分类：
- work: 工作场景服务（周报、待办、会议、项目）
- life: 生活场景服务（心情、兴趣、记忆）
- conversation: 对话服务（模仿、聊天）
- knowledge: 知识库服务（文档管理、搜索）

说明：
这些服务组合 Capabilities Layer 的能力模块，提供端到端的业务功能
"""

__version__ = "0.1.0"

# Conversation Services
from .conversation import MimicService

# Knowledge Services
from .knowledge import SearchService, DocumentService

# Work Services
from .work import ReportService, TodoService, MeetingService, ProjectService

# Life Services
from .life import MoodService, InterestService, MemoryService

__all__ = [
    # Conversation
    "MimicService",
    
    # Knowledge
    "SearchService",
    "DocumentService",
    
    # Work
    "ReportService",
    "TodoService",
    "MeetingService",
    "ProjectService",
    
    # Life
    "MoodService",
    "InterestService",
    "MemoryService",
]
