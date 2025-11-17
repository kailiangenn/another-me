"""
领域模型 - 统一的数据结构定义
支持双存储架构：Faiss（向量）+ Falkor（图谱）+ SQLite（元数据）
"""
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import uuid


class DocumentType(str, Enum):
    """文档类型枚举"""
    RAG_KNOWLEDGE = "rag_knowledge"          # RAG 知识文档
    MEM_CONVERSATION = "mem_conversation"    # MEM 对话记忆
    WORK_LOG = "work_log"                    # 工作日志
    LIFE_RECORD = "life_record"              # 生活记录


class DataLayer(str, Enum):
    """数据分层（热温冷）"""
    HOT = "hot"      # 0-7天（Faiss + Falkor）
    WARM = "warm"    # 7-30天（Faiss + Falkor）
    COLD = "cold"    # 30天+（仅 Falkor）


class MemoryRetentionType(str, Enum):
    """记忆保留类型（新增）"""
    PERMANENT = "permanent"        # 永久存储（重要对话、学习内容）
    TEMPORARY = "temporary"        # 临时记忆（7天后自动清理）
    CASUAL_CHAT = "casual_chat"    # 普通聊天（不存储或仅24小时）


class DocumentStatus(str, Enum):
    """文档状态"""
    PROCESSING = "processing"  # 处理中
    ACTIVE = "active"          # 活跃
    ARCHIVED = "archived"      # 归档
    DELETED = "deleted"        # 已删除


class Document(BaseModel):
    """
    统一文档模型
    支持双存储架构：向量检索 + 图谱分析
    """
    # 基础字段
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str
    doc_type: DocumentType
    source: str
    timestamp: datetime
    
    # Faiss 向量存储字段
    embedding: Optional[List[float]] = None
    faiss_index: Optional[int] = None           # Faiss 内部索引ID
    layer: DataLayer = DataLayer.HOT            # 数据分层
    stored_in_faiss: bool = False
    
    # Falkor 图谱存储字段
    graph_node_id: Optional[str] = None         # 图谱节点ID
    entities: List[str] = Field(default_factory=list)      # NER提取的实体
    relations: List[Dict] = Field(default_factory=list)    # 关系三元组
    stored_in_graph: bool = False
    
    # 元数据与状态
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: DocumentStatus = DocumentStatus.PROCESSING
    importance: float = 0.5                     # 重要性评分（0-1）
    
    # 记忆保留类型（用于对话过滤）
    retention_type: MemoryRetentionType = MemoryRetentionType.PERMANENT
    
    # 时间戳
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于数据库存储）"""
        return {
            "id": self.id,
            "content": self.content,
            "doc_type": self.doc_type,
            "source": self.source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "faiss_index": self.faiss_index,
            "layer": self.layer,
            "stored_in_faiss": self.stored_in_faiss,
            "graph_node_id": self.graph_node_id,
            "entities": self.entities,
            "relations": self.relations,
            "stored_in_graph": self.stored_in_graph,
            "metadata": self.metadata,
            "status": self.status,
            "importance": self.importance,
            "retention_type": self.retention_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """从字典创建对象"""
        # 转换时间字段
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if isinstance(data.get("updated_at"), str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        
        return cls(**data)


class SearchResult(BaseModel):
    """检索结果"""
    doc_id: str
    content: str
    score: float                               # 相似度分数
    source: str                                # 来源：faiss/graph/hybrid
    metadata: Dict[str, Any] = Field(default_factory=dict)
    entities: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True
