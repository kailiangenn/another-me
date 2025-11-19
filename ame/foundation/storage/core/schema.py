"""
图谱Schema定义 - 封闭的节点标签和关系类型

设计原则：
1. 预定义常见生活和工作场景
2. 不允许外部扩展（原子能力层面）
3. Capability层只能使用预定义的标签和关系
"""

from enum import Enum
from typing import Dict, List, Tuple


class NodeLabel(str, Enum):
    """
    节点标签枚举（封闭定义）
    
    生活领域 (Life):
    - 人物、事件、情绪、兴趣、地点、记忆
    
    工作领域 (Work):
    - 项目、任务、文档、会议、概念
    """
    
    # ===== 生活领域节点 =====
    PERSON = "Person"              # 人物（家人、朋友、同事）
    EVENT = "Event"                # 事件（聚会、旅行、纪念日）
    EMOTION = "Emotion"            # 情绪（开心、焦虑、兴奋）
    INTEREST = "Interest"          # 兴趣（爱好、主题）
    LOCATION = "Location"          # 地点（餐厅、城市、景点）
    MEMORY = "Memory"              # 记忆片段（重要时刻）
    TOPIC = "Topic"                # 话题（讨论主题）
    
    # ===== 工作领域节点 =====
    PROJECT = "Project"            # 项目
    TASK = "Task"                  # 任务/待办
    DOCUMENT = "Document"          # 文档
    MEETING = "Meeting"            # 会议
    CONCEPT = "Concept"            # 技术概念/知识点
    MILESTONE = "Milestone"        # 里程碑
    ISSUE = "Issue"                # 问题/Bug
    
    # ===== 通用节点 =====
    ENTITY = "Entity"              # 通用实体（兜底）


class RelationType(str, Enum):
    """
    关系类型枚举（封闭定义）
    
    生活关系 (Life):
    - 人际关系、情感关系、时空关系
    
    工作关系 (Work):
    - 依赖关系、归属关系、参与关系
    """
    
    # ===== 生活领域关系 =====
    KNOWS = "KNOWS"                    # 认识（Person -> Person）
    FAMILY = "FAMILY"                  # 家人关系（Person -> Person）
    FRIEND = "FRIEND"                  # 朋友关系（Person -> Person）
    ATTENDS = "ATTENDS"                # 参加（Person -> Event）
    FEELS = "FEELS"                    # 感受（Person -> Emotion）
    INTERESTED_IN = "INTERESTED_IN"    # 感兴趣（Person -> Interest）
    HAPPENED_AT = "HAPPENED_AT"        # 发生在（Event -> Location）
    LOCATED_IN = "LOCATED_IN"          # 位于（Location -> Location）
    REMEMBERS = "REMEMBERS"            # 记得（Person -> Memory）
    DISCUSSES = "DISCUSSES"            # 讨论（Person -> Topic）
    RELATES_TO = "RELATES_TO"          # 关联（通用关系）
    
    # ===== 工作领域关系 =====
    WORKS_ON = "WORKS_ON"              # 从事（Person -> Project/Task）
    DEPENDS_ON = "DEPENDS_ON"          # 依赖（Task -> Task）
    BELONGS_TO = "BELONGS_TO"          # 属于（Task -> Project）
    REFERENCES = "REFERENCES"          # 引用（Document -> Document/Concept）
    ASSIGNED_TO = "ASSIGNED_TO"        # 分配给（Task -> Person）
    PARTICIPATES = "PARTICIPATES"      # 参与（Person -> Meeting/Project）
    CONTAINS = "CONTAINS"              # 包含（Project -> Task）
    BLOCKS = "BLOCKS"                  # 阻塞（Issue -> Task）
    MENTIONS = "MENTIONS"              # 提及（Document -> Entity）
    ACHIEVES = "ACHIEVES"              # 达成（Task -> Milestone）
    
    # ===== 通用关系 =====
    LINKED_TO = "LINKED_TO"            # 链接到（通用）
    CREATED_BY = "CREATED_BY"          # 创建者（通用）


class GraphSchema:
    """
    Schema验证和约束定义
    
    定义每种节点/关系的必需属性
    """
    
    # 节点必需属性
    NODE_REQUIRED_PROPS = {
        NodeLabel.PERSON: ["name"],
        NodeLabel.EVENT: ["title", "date"],
        NodeLabel.EMOTION: ["type", "intensity"],
        NodeLabel.INTEREST: ["name"],
        NodeLabel.LOCATION: ["name"],
        NodeLabel.MEMORY: ["content"],
        NodeLabel.TOPIC: ["name"],
        
        NodeLabel.PROJECT: ["name"],
        NodeLabel.TASK: ["title", "status"],
        NodeLabel.DOCUMENT: ["title"],
        NodeLabel.MEETING: ["title", "date"],
        NodeLabel.CONCEPT: ["name"],
        NodeLabel.MILESTONE: ["title", "target_date"],
        NodeLabel.ISSUE: ["title", "status"],
        
        NodeLabel.ENTITY: [],  # 通用实体无强制属性
    }
    
    # 节点推荐属性（可选但建议）
    NODE_RECOMMENDED_PROPS = {
        NodeLabel.PERSON: ["user_id", "source"],
        NodeLabel.TASK: ["priority", "due_date"],
        NodeLabel.PROJECT: ["status", "owner"],
    }
    
    # 关系推荐属性
    EDGE_RECOMMENDED_PROPS = {
        RelationType.DEPENDS_ON: ["dependency_type"],  # hard/soft
        RelationType.ASSIGNED_TO: ["assigned_date"],
        RelationType.FEELS: ["timestamp"],
    }
    
    @classmethod
    def validate_node(cls, label: NodeLabel, properties: dict) -> Tuple[bool, str]:
        """
        验证节点是否符合Schema
        
        Returns:
            (is_valid, error_message)
        """
        required = cls.NODE_REQUIRED_PROPS.get(label, [])
        
        for prop in required:
            if prop not in properties:
                return False, f"节点 {label.value} 缺少必需属性: {prop}"
        
        return True, ""
    
    @classmethod
    def get_life_labels(cls) -> List[NodeLabel]:
        """获取生活领域节点标签"""
        return [
            NodeLabel.PERSON,
            NodeLabel.EVENT,
            NodeLabel.EMOTION,
            NodeLabel.INTEREST,
            NodeLabel.LOCATION,
            NodeLabel.MEMORY,
            NodeLabel.TOPIC,
        ]
    
    @classmethod
    def get_work_labels(cls) -> List[NodeLabel]:
        """获取工作领域节点标签"""
        return [
            NodeLabel.PROJECT,
            NodeLabel.TASK,
            NodeLabel.DOCUMENT,
            NodeLabel.MEETING,
            NodeLabel.CONCEPT,
            NodeLabel.MILESTONE,
            NodeLabel.ISSUE,
        ]


class RelationTimeSemantics:
    """
    关系时间语义定义
    
    说明每种关系类型的时间属性含义
    """
    
    # 生活领域关系时间语义
    LIFE_TIME_SEMANTICS = {
        RelationType.INTERESTED_IN: {
            "valid_from": "开始感兴趣的时间",
            "valid_until": "不再感兴趣的时间（None=仍然感兴趣）"
        },
        RelationType.KNOWS: {
            "valid_from": "认识的时间",
            "valid_until": "失联的时间（None=仍保持联系）"
        },
        RelationType.FEELS: {
            "valid_from": "情绪产生时间",
            "valid_until": "情绪消退时间（None=情绪仍在）"
        },
        RelationType.ATTENDS: {
            "valid_from": "参加活动的时间",
            "valid_until": "活动结束时间"
        },
    }
    
    # 工作领域关系时间语义
    WORK_TIME_SEMANTICS = {
        RelationType.WORKS_ON: {
            "valid_from": "开始工作的时间",
            "valid_until": "完成/停止工作的时间（None=仍在进行）"
        },
        RelationType.DEPENDS_ON: {
            "valid_from": "依赖建立时间",
            "valid_until": "依赖解除时间（None=仍然依赖）"
        },
        RelationType.ASSIGNED_TO: {
            "valid_from": "分配时间",
            "valid_until": "任务完成/重新分配时间（None=仍在负责）"
        },
    }
    
    @classmethod
    def get_time_meaning(cls, relation: RelationType, domain: str = "life") -> Dict[str, str]:
        """
        获取关系的时间语义
        
        Args:
            relation: 关系类型
            domain: 领域（life/work）
        
        Returns:
            时间语义字典
        """
        if domain == "life":
            return cls.LIFE_TIME_SEMANTICS.get(relation, {})
        else:
            return cls.WORK_TIME_SEMANTICS.get(relation, {})
