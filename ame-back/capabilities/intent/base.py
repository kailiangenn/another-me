"""
Intent 抽象基类
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum


class UserIntent(Enum):
    """用户意图类型"""
    SEARCH = "search"  # 搜索知识
    CHAT = "chat"  # 闲聊
    MEMORIZE = "memorize"  # 存储记忆
    RECALL = "recall"  # 回忆
    ANALYZE = "analyze"  # 分析
    UNKNOWN = "unknown"  # 未知


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: UserIntent
    confidence: float  # 0-1
    
    # 实体和槽位
    entities: Dict[str, Any]
    slots: Dict[str, Any]
    
    # 额外信息
    sub_intent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IntentRecognizerBase(ABC):
    """意图识别器抽象基类"""
    
    @abstractmethod
    async def recognize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentResult:
        """
        识别用户意图
        
        Args:
            text: 用户输入
            context: 上下文信息
        
        Returns:
            IntentResult: 意图识别结果
        """
        pass
