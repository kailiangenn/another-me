"""
NLP核心模型定义
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


class IntentType(Enum):
    """意图类型枚举"""
    CHAT = "chat"              # 普通聊天
    QUERY_SELF = "query_self"  # 查询自己的信息（兴趣、记忆等）
    ANALYZE = "analyze"        # 请求分析（情绪、行为等）
    COMFORT = "comfort"        # 需要安慰、倾诉
    CUSTOM = "custom"          # 自定义意图
    UNKNOWN = "unknown"        # 未知意图


class EntityType(Enum):
    """实体类型枚举"""
    PERSON = "person"          # 人名
    LOCATION = "location"      # 地点
    ORGANIZATION = "organization"  # 组织
    CONCEPT = "concept"        # 概念/技术
    TIME = "time"              # 时间
    EVENT = "event"            # 事件
    OTHER = "other"            # 其他


class EmotionType(Enum):
    """情绪类型枚举"""
    JOY = "joy"                # 喜悦
    SADNESS = "sadness"        # 悲伤
    ANGER = "anger"            # 愤怒
    FEAR = "fear"              # 恐惧
    SURPRISE = "surprise"      # 惊讶
    DISGUST = "disgust"        # 厌恶
    NEUTRAL = "neutral"        # 中性


@dataclass
class IntentResult:
    """意图识别结果"""
    intent: IntentType
    confidence: float          # 0-1 置信度
    keywords: List[str] = field(default_factory=list)  # 关键词
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据
    
    def __post_init__(self):
        """验证数据"""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"confidence必须在0-1之间，当前值: {self.confidence}")


@dataclass
class Entity:
    """实体对象"""
    text: str                  # 实体文本
    type: EntityType           # 实体类型
    start: int = 0             # 起始位置
    end: int = 0               # 结束位置
    confidence: float = 1.0    # 置信度
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外信息
    
    def __post_init__(self):
        """验证数据"""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"confidence必须在0-1之间，当前值: {self.confidence}")


@dataclass
class EmotionResult:
    """情感分析结果"""
    emotion: EmotionType       # 情绪类型
    intensity: float           # 强度 0-1
    valence: float             # 效价 -1到1（负向到正向）
    keywords: List[str] = field(default_factory=list)  # 情绪关键词
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """验证数据"""
        if not 0 <= self.intensity <= 1:
            raise ValueError(f"intensity必须在0-1之间，当前值: {self.intensity}")
        if not -1 <= self.valence <= 1:
            raise ValueError(f"valence必须在-1到1之间，当前值: {self.valence}")


@dataclass
class Summary:
    """摘要结果"""
    content: str                          # 摘要内容
    key_points: List[str] = field(default_factory=list)  # 关键点
    entities: List[Entity] = field(default_factory=list)  # 提取的实体
    emotions: List[EmotionResult] = field(default_factory=list)  # 情绪变化
    topics: List[str] = field(default_factory=list)  # 讨论话题
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NLPAnalysisResult:
    """综合NLP分析结果"""
    text: str                             # 原始文本
    intent: Optional[IntentResult] = None
    entities: List[Entity] = field(default_factory=list)
    emotion: Optional[EmotionResult] = None
    summary: Optional[Summary] = None
    analyzed_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
