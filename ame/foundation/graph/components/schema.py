"""
图谱 Schema 管理（生活/工作双场景）
"""
from typing import Set
from loguru import logger

from ..utils.models import NodeLabel, RelationType, GraphNode, GraphEdge
from ..utils.exceptions import ValidationError


class BaseGraphSchema:
    """图谱 Schema 基类"""
    
    def __init__(self):
        self.allowed_nodes: Set[NodeLabel] = set()
        self.allowed_relations: Set[RelationType] = set()
        self._init_schema()
    
    def _init_schema(self):
        """子类实现：初始化允许的节点和关系"""
        raise NotImplementedError
    
    def validate_node(self, node: GraphNode) -> bool:
        """验证节点是否符合 Schema"""
        if node.label not in self.allowed_nodes:
            raise ValidationError(
                f"Node label '{node.label}' not allowed in this schema. "
                f"Allowed: {[n.value for n in self.allowed_nodes]}",
                data=node
            )
        logger.debug(f"Node validation passed: {node.id} ({node.label})")
        return True
    
    def validate_edge(self, edge: GraphEdge) -> bool:
        """验证边是否符合 Schema"""
        if edge.relation_type not in self.allowed_relations:
            raise ValidationError(
                f"Relation type '{edge.relation_type}' not allowed in this schema. "
                f"Allowed: {[r.value for r in self.allowed_relations]}",
                data=edge
            )
        logger.debug(f"Edge validation passed: {edge.source_id} -[{edge.relation_type}]-> {edge.target_id}")
        return True


class LifeGraphSchema(BaseGraphSchema):
    """生活图谱 Schema"""
    
    def _init_schema(self):
        """初始化生活场景的节点和关系（只存储原始事实）"""
        # 生活场景节点（原始事实）
        self.allowed_nodes = {
            NodeLabel.MEMORY,      # 记忆（日记、聊天）
            NodeLabel.PERSON,      # 人物
            NodeLabel.EVENT,       # 事件
            NodeLabel.EMOTION,     # 情绪标签
            NodeLabel.LOCATION,    # 地点
            NodeLabel.TOPIC,       # 话题
            NodeLabel.TIMESTAMP,   # 时间点
            NodeLabel.ENTITY,      # 通用实体
            NodeLabel.DOCUMENT,    # 文档
        }
        
        # 生活场景关系（原始事实关系）
        self.allowed_relations = {
            RelationType.MENTIONS,      # 提到
            RelationType.FEELS,         # 感受
            RelationType.PARTICIPATES,  # 参与
            RelationType.OCCURS_AT,     # 发生于（时间）
            RelationType.LOCATED_AT,    # 位于（地点）
            RelationType.RELATES_TO,    # 关联
            RelationType.TALKS_ABOUT,   # 讨论（话题）
            RelationType.REFERENCES,    # 引用
            RelationType.FOLLOWS,       # 跟随（时间序列）
        }
        
        logger.debug("LifeGraphSchema initialized (fact-only)")


class WorkGraphSchema(BaseGraphSchema):
    """工作图谱 Schema"""
    
    def _init_schema(self):
        """初始化工作场景的节点和关系（只存储原始事实）"""
        # 工作场景节点（原始事实）
        self.allowed_nodes = {
            NodeLabel.TODO,        # 待办任务
            NodeLabel.PROJECT,     # 项目
            NodeLabel.MILESTONE,   # 里程碑
            NodeLabel.TAG,         # 标签（分类）
            NodeLabel.TIMESTAMP,   # 时间点
            NodeLabel.ENTITY,      # 通用实体
            NodeLabel.DOCUMENT,    # 文档
        }
        
        # 工作场景关系（原始事实关系）
        self.allowed_relations = {
            # 任务管理关系
            RelationType.DEPENDS_ON,        # 依赖
            RelationType.BELONGS_TO,        # 属于
            RelationType.CONTAINS,          # 包含
            RelationType.BLOCKS,            # 阻塞
            RelationType.DUE_AT,            # 截止于
            RelationType.CONTRIBUTES_TO,    # 贡献到
            RelationType.CREATED_AT,        # 创建于
            RelationType.COMPLETED_AT,      # 完成于
            RelationType.TAGGED_AS,         # 标记为
            # 通用关系
            RelationType.REFERENCES,        # 引用
            RelationType.FOLLOWS,           # 跟随（时间序列）
            RelationType.RELATES_TO,        # 关联
        }
        
        logger.debug("WorkGraphSchema initialized (fact-only)")
