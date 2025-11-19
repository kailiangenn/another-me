"""
Connect Service - 配置测试服务
"""

from .connect_service import ConnectService
from .test_llm import TestSummary, TestResult, TestConfig as LLMTestConfig
from .test_storage import TestConfig as StorageTestConfig

__all__ = [
    "ConnectService",
    "TestSummary",
    "TestResult",
    "LLMTestConfig",
    "StorageTestConfig",
]
