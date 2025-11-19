"""
工作图谱管道

职责：
- 连接FalkorDB的"work_graph"
- 提供工作领域的批量操作
- 自动创建Graph（不存在则创建）
- 只允许创建工作领域节点
"""

from loguru import logger
from typing import Optional

from .base import GraphPipelineBase
from ..atomic.falkordb_store import FalkorDBStore
from ..core.schema import GraphSchema, NodeLabel
from ..core.models import GraphNode
from ..core.exceptions import ValidationError


class WorkGraphPipeline(GraphPipelineBase):
    """
    工作图谱管道
    
    特性：
    - Graph名称固定为 "work_graph"
    - 自动创建Graph（不存在则创建）
    - 只允许创建工作领域节点
    """
    
    GRAPH_NAME = "work_graph"
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None
    ):
        # 创建FalkorDB Store
        store = FalkorDBStore(
            host=host,
            port=port,
            graph_name=self.GRAPH_NAME,
            password=password
        )
        
        super().__init__(store)
        
        # 工作领域允许的节点标签
        self.allowed_labels = GraphSchema.get_work_labels()
        
        logger.info(f"工作图谱管道初始化: Graph={self.GRAPH_NAME}")
    
    async def initialize(self) -> None:
        """初始化（连接数据库并创建Graph）"""
        await self.store.connect()
        logger.info(f"工作图谱已就绪: {self.GRAPH_NAME}")
    
    async def validate_and_create_node(self, node: GraphNode) -> str:
        """
        验证节点是否属于工作领域
        
        重写父类方法，增加领域检查
        """
        if node.label not in self.allowed_labels:
            raise ValidationError(
                f"节点标签 {node.label.value} 不属于工作领域。"
                f"允许的标签: {[l.value for l in self.allowed_labels]}",
                node
            )
        
        return await super().validate_and_create_node(node)
