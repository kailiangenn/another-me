"""
Service Layer - 业务服务层

提供场景化的业务服务，遵循依赖注入规范。
"""

from .connect import ConnectService
from .life import LifeChatService
from .work import (
    WorkProjectService,
    WorkTodoService,
    WorkAdviceService,
)

__all__ = [
    "ConnectService",
    "LifeChatService",
    "WorkProjectService",
    "WorkTodoService",
    "WorkAdviceService",
]
