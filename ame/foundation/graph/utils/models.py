"""
图谱数据模型与枚举类型
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


# ========== 枚举类型 ==========

class NodeLabel(str, Enum):
    """节点标签（生活+工作场景）- 只存储原始事实"""
    
    # ========== 生活场景节点 ==========
    MEMORY = "Memory"           # 记忆节点（日记、聊天记录等）
    PERSON = "Person"           # 人物（家人、朋友等）
    EVENT = "Event"             # 事件（发生的事情）
    EMOTION = "Emotion"         # 情绪标签（开心、难过等）
    LOCATION = "Location"       # 地点（家、公司等）
    TOPIC = "Topic"             # 话题（兴趣、关注点）
    
    # ========== 工作场景节点 ==========
    TODO = "Todo"               # 待办任务
    PROJECT = "Project"         # 项目
    MILESTONE = "Milestone"     # 里程碑
    TAG = "Tag"                 # 标签（分类用）
    
    # ========== 通用节点 ==========
    DOCUMENT = "Document"       # 文档
    ENTITY = "Entity"           # 实体（通用命名实体）
    TIMESTAMP = "Timestamp"     # 时间点（用于时间序列分析）


class RelationType(str, Enum):
    """关系类型（生活+工作场景）- 只存储原始事实关系"""
    
    # ========== 生活场景关系 ==========
    MENTIONS = "MENTIONS"           # 提到（记忆提到人物/地点/话题）
    FEELS = "FEELS"                 # 感受（记忆关联情绪）
    PARTICIPATES = "PARTICIPATES"   # 参与（人物参与事件）
    OCCURS_AT = "OCCURS_AT"         # 发生于（事件发生的时间）
    LOCATED_AT = "LOCATED_AT"       # 位于（事件发生的地点）
    RELATES_TO = "RELATES_TO"       # 关联（通用关联关系）
    TALKS_ABOUT = "TALKS_ABOUT"     # 讨论（记忆讨论的话题）
    
    # ========== 工作场景关系 ==========
    DEPENDS_ON = "DEPENDS_ON"       # 依赖（任务依赖关系）
    BELONGS_TO = "BELONGS_TO"       # 属于（任务属于项目）
    CONTAINS = "CONTAINS"           # 包含（项目包含任务）
    BLOCKS = "BLOCKS"               # 阻塞（任务阻塞关系）
    DUE_AT = "DUE_AT"               # 截止于（任务的截止时间）
    CONTRIBUTES_TO = "CONTRIBUTES_TO"  # 贡献到（任务贡献到里程碑）
    CREATED_AT = "CREATED_AT"       # 创建于（创建时间）
    COMPLETED_AT = "COMPLETED_AT"   # 完成于（完成时间）
    TAGGED_AS = "TAGGED_AS"         # 标记为（分类标签）
    
    # ========== 通用关系 ==========
    REFERENCES = "REFERENCES"       # 引用（文档引用关系）
    FOLLOWS = "FOLLOWS"             # 跟随（时间序列关系）


class GraphType(str, Enum):
    """图谱类型"""
    LIFE = "life"               # 生活图谱
    WORK = "work"               # 工作图谱


# ========== 数据类 ==========

@dataclass
class GraphNode:
    """图节点"""
    id: str
    label: NodeLabel
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """确保必要属性"""
        if 'created_at' not in self.properties:
            self.properties['created_at'] = datetime.now().isoformat()


@dataclass
class GraphEdge:
    """图边（支持时间属性）"""
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    # 时间属性
    create_time: Optional[datetime] = None      # 生效时间
    invalid_time: Optional[datetime] = None     # 失效时间
    
    def __post_init__(self):
        """初始化时间属性"""
        if self.create_time is None:
            self.create_time = datetime.now()
        
        # 将时间属性加入properties
        self.properties['create_time'] = self.create_time.isoformat()
        if self.invalid_time:
            self.properties['invalid_time'] = self.invalid_time.isoformat()
    
    def is_valid(self, at_time: Optional[datetime] = None) -> bool:
        """判断边在指定时间是否有效"""
        check_time = at_time or datetime.now()
        
        if check_time < self.create_time:
            return False
        
        if self.invalid_time and check_time >= self.invalid_time:
            return False
        
        return True


@dataclass
class QueryResult:
    """查询结果"""
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)
    raw_data: Any = None
