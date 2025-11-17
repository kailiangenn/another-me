"""
情绪识别抽象基类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class EmotionType(Enum):
    """情绪类型"""
    POSITIVE = "positive"       # 积极
    NEGATIVE = "negative"       # 消极
    NEUTRAL = "neutral"         # 中性
    HAPPY = "happy"             # 开心
    SAD = "sad"                 # 悲伤
    ANGRY = "angry"             # 愤怒
    ANXIOUS = "anxious"         # 焦虑
    FRUSTRATED = "frustrated"   # 沮丧
    EXCITED = "excited"         # 兴奋
    CALM = "calm"               # 平静


@dataclass
class EmotionResult:
    """情绪识别结果"""
    type: str                                       # 情绪类型（positive/negative/neutral/...）
    intensity: float                                # 情绪强度（0.0-1.0）
    confidence: float                               # 置信度（0.0-1.0）
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "metadata": self.metadata
        }


class EmotionDetectorBase(ABC):
    """情绪识别抽象基类"""
    
    @abstractmethod
    async def detect(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionResult:
        """
        识别情绪
        
        Args:
            text: 输入文本
            context: 上下文信息（可选）
        
        Returns:
            result: 情绪识别结果
        """
        pass
    
    @abstractmethod
    def get_detector_name(self) -> str:
        """获取识别器名称"""
        pass
