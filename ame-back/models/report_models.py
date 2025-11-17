"""
报告数据模型
定义周报、日报、心情分析等结构化数据模型
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pydantic import BaseModel, Field


class TaskSummary(BaseModel):
    """任务摘要"""
    title: str
    description: Optional[str] = None
    status: str = "ongoing"  # ongoing/completed/blocked
    importance: float = 0.5
    mentioned_times: int = 1
    
    class Config:
        use_enum_values = True


class Achievement(BaseModel):
    """成就记录"""
    title: str
    description: str
    timestamp: datetime
    importance: float = 0.8
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WeeklyReport(BaseModel):
    """工作周报"""
    user_id: str
    period: Tuple[datetime, datetime]
    content: str  # Markdown 格式的完整周报
    key_tasks: List[TaskSummary] = Field(default_factory=list)
    achievements: List[Achievement] = Field(default_factory=list)
    challenges: List[str] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class DailyReport(BaseModel):
    """工作日报"""
    user_id: str
    date: datetime
    content: str  # Markdown 格式的完整日报
    tasks_completed: List[TaskSummary] = Field(default_factory=list)
    tasks_ongoing: List[TaskSummary] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    tomorrow_plan: List[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TaskInfo(BaseModel):
    """任务信息（用于待办整理）"""
    content: str
    priority_score: float = 0.0
    entities: List[str] = Field(default_factory=list)
    due_date: Optional[datetime] = None
    is_blocking_others: bool = False
    has_dependencies: bool = False
    category: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class OrganizedTodos(BaseModel):
    """整理后的待办事项"""
    high_priority: List[TaskInfo] = Field(default_factory=list)
    medium_priority: List[TaskInfo] = Field(default_factory=list)
    low_priority: List[TaskInfo] = Field(default_factory=list)
    formatted_text: str  # Markdown 格式的整理结果
    original_count: int
    organized_count: int
    
    class Config:
        use_enum_values = True


class ProjectProgress(BaseModel):
    """项目进度"""
    project_name: str
    completion_rate: float = 0.0
    status: Dict[str, Any] = Field(default_factory=dict)
    timeline: List[Dict[str, Any]] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    report: str  # Markdown 格式的进度报告
    
    class Config:
        use_enum_values = True


class EmotionResult(BaseModel):
    """情绪识别结果"""
    type: str  # happy/sad/angry/anxious/excited/neutral等
    intensity: float  # 0.0-1.0
    confidence: float = 0.8
    
    class Config:
        use_enum_values = True


class MoodTrend(BaseModel):
    """情绪趋势"""
    current_emotion: str
    average_intensity: float
    trend_direction: str  # improving/declining/stable
    alert: bool = False  # 是否需要关注
    
    class Config:
        use_enum_values = True


class MoodAnalysis(BaseModel):
    """心情分析结果"""
    emotion_type: str
    emotion_intensity: float
    triggers: List[str] = Field(default_factory=list)
    trend: Optional[MoodTrend] = None
    suggestions: str  # AI 生成的建议
    analysis_time: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class InterestTopic(BaseModel):
    """兴趣主题"""
    topic: str
    frequency: int
    first_mentioned: datetime
    last_mentioned: datetime
    trend: str = "stable"  # growing/stable/declining
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class InterestReport(BaseModel):
    """兴趣追踪报告"""
    user_id: str
    period_days: int
    top_interests: List[InterestTopic] = Field(default_factory=list)
    new_interests: List[str] = Field(default_factory=list)
    declining_interests: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    report: str  # Markdown 格式的兴趣报告
    generated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
