"""
图存储抽象基类（内化组件能力）
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from ..utils.models import (
    GraphNode, 
    GraphEdge, 
    QueryResult, 
    NodeLabel, 
    RelationType,
    GraphType
)
from ..utils.exceptions import GraphStoreError
from ..components.schema import LifeGraphSchema, WorkGraphSchema
from ..components.query_builder import QueryBuilder
from ..components.time_handler import TimeHandler


class GraphStoreBase(ABC):
    """
    图存储抽象基类（模板方法模式）
    
    设计理念：
    - 内化组件能力（Schema、QueryBuilder、TimeHandler）
    - 子类只需实现 _xxx 私有方法（底层数据库操作）
    - 用户调用公共方法时，自动使用内置组件进行预处理
    """
    
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 6379, 
        base_name: str = "another_me"
    ):
        self.host = host
        self.port = port
        self.base_name = base_name
        
        # 两张图谱表
        self.life_graph_name = f"{base_name}_life"
        self.work_graph_name = f"{base_name}_work"
        
        # ✨ 内化组件（自动初始化）
        self.life_schema = LifeGraphSchema()
        self.work_schema = WorkGraphSchema()
        self.query_builder = QueryBuilder()
        self.time_handler = TimeHandler()
        
        logger.info(f"GraphStore initialized: {base_name} (life & work tables)")
    
    def _get_schema(self, graph_type: GraphType):
        """根据图谱类型获取对应的 Schema"""
        if graph_type == GraphType.LIFE:
            return self.life_schema
        elif graph_type == GraphType.WORK:
            return self.work_schema
        else:
            raise GraphStoreError(f"Unknown graph type: {graph_type}")
    
    def _get_graph_name(self, graph_type: GraphType) -> str:
        """根据图谱类型获取对应的表名"""
        if graph_type == GraphType.LIFE:
            return self.life_graph_name
        elif graph_type == GraphType.WORK:
            return self.work_graph_name
        else:
            raise GraphStoreError(f"Unknown graph type: {graph_type}")
    
    # ========== 连接管理（公共方法）==========
    
    def connect(self) -> None:
        """连接数据库（调用子类实现）"""
        try:
            self._connect()
            logger.info(f"Connected to graph store at {self.host}:{self.port}")
            # 初始化两张表
            self._init_graph(GraphType.LIFE)
            self._init_graph(GraphType.WORK)
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            raise
    
    def disconnect(self) -> None:
        """断开连接（调用子类实现）"""
        try:
            self._disconnect()
            logger.info("Disconnected from graph store")
        except Exception as e:
            logger.error(f"Failed to disconnect: {str(e)}")
            raise
    
    # ========== 节点操作（公共方法，内化 Schema 验证）==========
    
    def add_node(self, node: GraphNode, graph_type: GraphType) -> bool:
        """
        添加节点（公共方法）
        自动进行 Schema 验证
        
        Args:
            node: 节点对象
            graph_type: 指定操作哪张表（LIFE 或 WORK）
        """
        try:
            # 1. Schema 验证（内化）
            schema = self._get_schema(graph_type)
            graph_name = self._get_graph_name(graph_type)
            schema.validate_node(node)
            
            # 2. 调用子类实现的底层方法
            result = self._add_node(node, graph_name)
            
            if result:
                logger.info(f"Node added to {graph_type.value}: {node.id} ({node.label})")
            return result
        except Exception as e:
            logger.error(f"Failed to add node {node.id} to {graph_type.value}: {str(e)}")
            raise
    
    def get_node(self, node_id: str, graph_type: GraphType) -> Optional[GraphNode]:
        """
        获取节点（调用子类实现）
        
        Args:
            node_id: 节点 ID
            graph_type: 指定操作哪张表
        """
        try:
            graph_name = self._get_graph_name(graph_type)
            return self._get_node(node_id, graph_name)
        except Exception as e:
            logger.error(f"Failed to get node {node_id} from {graph_type.value}: {str(e)}")
            return None
    
    def get_nodes_by_properties(
        self, 
        properties: Dict[str, Any], 
        label: Optional[NodeLabel] = None,
        graph_type: GraphType = GraphType.LIFE
    ) -> List[GraphNode]:
        """
        根据属性获取节点列表
        
        Args:
            properties: 属性键值对
            label: 节点标签（可选）
            graph_type: 指定操作哪张表
        """
        try:
            # 使用 QueryBuilder 构建查询
            query_builder = self.query_builder.reset()
            cypher = query_builder \
                .match_nodes_by_properties(properties, label, "n") \
                .return_nodes("n") \
                .build()
            
            params = query_builder.get_params()
            graph_name = self._get_graph_name(graph_type)
            result = self._query(cypher, params, graph_name)
            
            return result.nodes
        except Exception as e:
            logger.error(f"Failed to get nodes by properties in {graph_type.value}: {str(e)}")
            return []
    
    def update_node(self, node_id: str, properties: Dict[str, Any], graph_type: GraphType) -> bool:
        """
        更新节点属性（调用子类实现）
        
        Args:
            node_id: 节点 ID
            properties: 要更新的属性
            graph_type: 指定操作哪张表
        """
        try:
            graph_name = self._get_graph_name(graph_type)
            result = self._update_node(node_id, properties, graph_name)
            if result:
                logger.info(f"Node updated in {graph_type.value}: {node_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to update node {node_id} in {graph_type.value}: {str(e)}")
            return False
    
    def delete_node(self, node_id: str, graph_type: GraphType) -> bool:
        """
        删除节点（调用子类实现）
        
        Args:
            node_id: 节点 ID
            graph_type: 指定操作哪张表
        """
        try:
            graph_name = self._get_graph_name(graph_type)
            result = self._delete_node(node_id, graph_name)
            if result:
                logger.info(f"Node deleted from {graph_type.value}: {node_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete node {node_id} from {graph_type.value}: {str(e)}")
            return False
    
    def delete_nodes_by_properties(
        self, 
        properties: Dict[str, Any], 
        label: Optional[NodeLabel] = None,
        graph_type: GraphType = GraphType.LIFE
    ) -> int:
        """
        根据属性删除节点
        
        Args:
            properties: 属性键值对
            label: 节点标签（可选）
            graph_type: 指定操作哪张表
            
        Returns:
            删除的节点数量
        """
        try:
            # 先查询要删除的节点
            nodes_to_delete = self.get_nodes_by_properties(properties, label, graph_type)
            
            # 删除每个节点
            deleted_count = 0
            for node in nodes_to_delete:
                if self.delete_node(node.id, graph_type):
                    deleted_count += 1
            
            logger.info(f"Deleted {deleted_count} nodes from {graph_type.value}")
            return deleted_count
        except Exception as e:
            logger.error(f"Failed to delete nodes by properties in {graph_type.value}: {str(e)}")
            return 0
    
    # ========== 边操作（公共方法，内化 Schema 验证）==========
    
    def add_edge(self, edge: GraphEdge, graph_type: GraphType) -> bool:
        """
        添加边（公共方法）
        自动进行 Schema 验证
        
        Args:
            edge: 边对象（带有 create_time 和 invalid_time）
            graph_type: 指定操作哪张表
        """
        try:
            # 1. Schema 验证（内化）
            schema = self._get_schema(graph_type)
            graph_name = self._get_graph_name(graph_type)
            schema.validate_edge(edge)
            
            # 2. 调用子类实现的底层方法
            result = self._add_edge(edge, graph_name)
            
            if result:
                logger.info(f"Edge added to {graph_type.value}: {edge.source_id} -[{edge.relation_type}]-> {edge.target_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to add edge to {graph_type.value}: {str(e)}")
            raise
    
    def get_edges(
        self, 
        source_id: str, 
        target_id: Optional[str] = None,
        graph_type: GraphType = GraphType.LIFE
    ) -> List[GraphEdge]:
        """
        获取边（调用子类实现）
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID（可选）
            graph_type: 指定操作哪张表
        """
        try:
            graph_name = self._get_graph_name(graph_type)
            return self._get_edges(source_id, target_id, graph_name)
        except Exception as e:
            logger.error(f"Failed to get edges from {graph_type.value}: {str(e)}")
            return []
    
    def delete_edge(
        self, 
        source_id: str, 
        target_id: str, 
        relation_type: RelationType,
        graph_type: GraphType
    ) -> bool:
        """
        删除边（调用子类实现）
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID
            relation_type: 关系类型
            graph_type: 指定操作哪张表
        """
        try:
            graph_name = self._get_graph_name(graph_type)
            result = self._delete_edge(source_id, target_id, relation_type, graph_name)
            if result:
                logger.info(f"Edge deleted from {graph_type.value}: {source_id} -[{relation_type}]-> {target_id}")
            return result
        except Exception as e:
            logger.error(f"Failed to delete edge from {graph_type.value}: {str(e)}")
            return False
    
    # ========== 查询操作（公共方法）==========
    
    def query(self, cypher: str, graph_type: GraphType, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """
        执行 Cypher 查询（公共方法）
        用户可以直接传 Cypher，也可以用 query_builder
        
        Args:
            cypher: Cypher 查询语句
            graph_type: 指定操作哪张表
            params: 查询参数
        """
        try:
            params = params or {}
            graph_name = self._get_graph_name(graph_type)
            logger.debug(f"Executing query on {graph_type.value}: {cypher}")
            return self._query(cypher, params, graph_name)
        except Exception as e:
            logger.error(f"Query failed on {graph_type.value}: {str(e)}")
            raise
    
    def find_neighbors(
        self,
        node_id: str,
        graph_type: GraphType,
        relation_type: Optional[RelationType] = None,
        direction: str = "out"  # "out", "in", "both"
    ) -> List[GraphNode]:
        """
        查找邻居节点（公共方法，内化 QueryBuilder）
        
        Args:
            node_id: 节点 ID
            graph_type: 指定操作哪张表
            relation_type: 关系类型（可选）
            direction: 方向（out/in/both）
        """
        try:
            # 使用 QueryBuilder 构建查询（内化）
            cypher = self.query_builder.reset() \
                .match_node_by_id(node_id, "n") \
                .with_relation(relation_type, direction, "n", "m", "r") \
                .return_neighbors("m") \
                .build()
            
            params = self.query_builder.get_params()
            graph_name = self._get_graph_name(graph_type)
            result = self._query(cypher, params, graph_name)
            
            return result.nodes
        except Exception as e:
            logger.error(f"Failed to find neighbors for {node_id} in {graph_type.value}: {str(e)}")
            return []
    
    def find_neighbors_at_time(
        self,
        node_id: str,
        graph_type: GraphType,
        at_time: Optional[datetime] = None,
        relation_type: Optional[RelationType] = None,
        direction: str = "out"
    ) -> List[GraphNode]:
        """
        时间点查询邻居（公共方法，内化 QueryBuilder + TimeHandler）
        
        Args:
            node_id: 节点 ID
            graph_type: 指定操作哪张表
            at_time: 查询的时间点
            relation_type: 关系类型（可选）
            direction: 方向（out/in/both）
        """
        try:
            check_time = at_time or datetime.now()
            
            # 使用 QueryBuilder 构建查询（内化）
            cypher = self.query_builder.reset() \
                .match_node_by_id(node_id, "n") \
                .with_relation(relation_type, direction, "n", "m", "r") \
                .where_time_valid(check_time, "r") \
                .return_neighbors("m") \
                .build()
            
            params = self.query_builder.get_params()
            graph_name = self._get_graph_name(graph_type)
            result = self._query(cypher, params, graph_name)
            
            logger.debug(f"Found {len(result.nodes)} valid neighbors at {check_time} in {graph_type.value}")
            return result.nodes
        except Exception as e:
            logger.error(f"Failed to find neighbors at time for {node_id} in {graph_type.value}: {str(e)}")
            return []
    
    def find_path(
        self,
        start_node_id: str,
        end_node_id: str,
        graph_type: GraphType,
        max_depth: int = 3,
        relationship_types: Optional[List[RelationType]] = None
    ) -> List[GraphEdge]:
        """
        查找两个节点之间的路径
        
        Args:
            start_node_id: 起始节点 ID
            end_node_id: 结束节点 ID
            graph_type: 指定操作哪张表
            max_depth: 最大深度
            relationship_types: 关系类型列表（可选）
            
        Returns:
            路径中的边列表
        """
        try:
            # 使用 QueryBuilder 构建查询
            cypher = self.query_builder.reset() \
                .find_path(start_node_id, end_node_id, max_depth, relationship_types) \
                .build()
            
            params = self.query_builder.get_params()
            graph_name = self._get_graph_name(graph_type)
            result = self._query(cypher, params, graph_name)
            
            return result.edges
        except Exception as e:
            logger.error(f"Failed to find path in {graph_type.value}: {str(e)}")
            return []
    
    def search_nodes(
        self,
        graph_type: GraphType,
        label: Optional[NodeLabel] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None,
        order_direction: str = "ASC"
    ) -> List[GraphNode]:
        """
        搜索节点（高级查询接口）
        
        Args:
            graph_type: 指定操作哪张表
            label: 节点标签（可选）
            properties: 属性过滤条件（可选）
            limit: 限制返回数量（可选）
            order_by: 排序字段（可选）
            order_direction: 排序方向（ASC/DESC）
            
        Returns:
            节点列表
        """
        try:
            # 构建查询
            query_builder = self.query_builder.reset()
            
            # 匹配节点
            if properties:
                query_builder.match_nodes_by_properties(properties, label, "n")
            else:
                query_builder.match_node(label, "n")
            
            # 返回节点
            query_builder.return_nodes("n")
            
            # 排序
            if order_by:
                query_builder.order_by(order_by, order_direction, "n")
            
            # 限制数量
            if limit:
                query_builder.limit(limit)
            
            cypher = query_builder.build()
            params = query_builder.get_params()
            graph_name = self._get_graph_name(graph_type)
            result = self._query(cypher, params, graph_name)
            
            return result.nodes
        except Exception as e:
            logger.error(f"Failed to search nodes in {graph_type.value}: {str(e)}")
            return []
    
    def count_nodes(
        self,
        graph_type: GraphType,
        label: Optional[NodeLabel] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        统计节点数量
        
        Args:
            graph_type: 指定操作哪张表
            label: 节点标签（可选）
            properties: 属性过滤条件（可选）
            
        Returns:
            节点数量
        """
        try:
            # 构建查询
            query_builder = self.query_builder.reset()
            
            # 匹配节点
            if properties:
                query_builder.match_nodes_by_properties(properties, label, "n")
            else:
                query_builder.match_node(label, "n")
            
            # 返回计数
            query_builder.return_count("n")
            
            cypher = query_builder.build()
            params = query_builder.get_params()
            graph_name = self._get_graph_name(graph_type)
            result = self._query(cypher, params, graph_name)
            
            # 解析计数结果
            if result.raw_data and result.raw_data.result_set:
                return result.raw_data.result_set[0][0]
            return 0
        except Exception as e:
            logger.error(f"Failed to count nodes in {graph_type.value}: {str(e)}")
            return 0
    
    def invalidate_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        graph_type: GraphType,
        invalid_time: Optional[datetime] = None
    ) -> bool:
        """
        使边失效（公共方法，内化 TimeHandler）
        用于关系演化：不删除边，而是标记失效
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID
            relation_type: 关系类型
            graph_type: 指定操作哪张表
            invalid_time: 失效时间（默认为当前时间）
        """
        try:
            # 1. 获取边
            edges = self.get_edges(source_id, target_id, graph_type)
            target_edge = None
            
            for edge in edges:
                if edge.relation_type == relation_type:
                    target_edge = edge
                    break
            
            if not target_edge:
                logger.warning(f"Edge not found in {graph_type.value}: {source_id} -[{relation_type}]-> {target_id}")
                return False
            
            # 2. 使用 TimeHandler 设置失效时间（内化）
            self.time_handler.invalidate_edge(target_edge, invalid_time)
            
            # 3. 更新数据库
            graph_name = self._get_graph_name(graph_type)
            return self._update_edge(target_edge, graph_name)
        except Exception as e:
            logger.error(f"Failed to invalidate edge in {graph_type.value}: {str(e)}")
            return False
    
    # ========== 抽象方法（子类必须实现）==========
    
    @abstractmethod
    def _connect(self) -> None:
        """子类实现：连接数据库"""
        pass
    
    @abstractmethod
    def _disconnect(self) -> None:
        """子类实现：断开连接"""
        pass
    
    @abstractmethod
    def _init_graph(self, graph_type: GraphType) -> None:
        """
        子类实现：初始化图谱表（创建或加载）
        
        Args:
            graph_type: 图谱类型（LIFE 或 WORK）
        """
        pass
    
    @abstractmethod
    def _add_node(self, node: GraphNode, graph_name: str) -> bool:
        """
        子类实现：底层添加节点逻辑
        
        Args:
            node: 节点对象
            graph_name: 表名（life_graph 或 work_graph）
        """
        pass
    
    @abstractmethod
    def _get_node(self, node_id: str, graph_name: str) -> Optional[GraphNode]:
        """
        子类实现：底层获取节点逻辑
        
        Args:
            node_id: 节点 ID
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _update_node(self, node_id: str, properties: Dict[str, Any], graph_name: str) -> bool:
        """
        子类实现：底层更新节点逻辑
        
        Args:
            node_id: 节点 ID
            properties: 要更新的属性
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _delete_node(self, node_id: str, graph_name: str) -> bool:
        """
        子类实现：底层删除节点逻辑
        
        Args:
            node_id: 节点 ID
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _add_edge(self, edge: GraphEdge, graph_name: str) -> bool:
        """
        子类实现：底层添加边逻辑
        
        Args:
            edge: 边对象（带有 create_time 和 invalid_time）
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _get_edges(self, source_id: str, target_id: Optional[str], graph_name: str) -> List[GraphEdge]:
        """
        子类实现：底层获取边逻辑
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID（可选）
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _delete_edge(self, source_id: str, target_id: str, relation_type: RelationType, graph_name: str) -> bool:
        """
        子类实现：底层删除边逻辑
        
        Args:
            source_id: 源节点 ID
            target_id: 目标节点 ID
            relation_type: 关系类型
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _query(self, cypher: str, params: Dict[str, Any], graph_name: str) -> QueryResult:
        """
        子类实现：底层执行 Cypher 查询
        
        Args:
            cypher: Cypher 查询语句
            params: 查询参数
            graph_name: 表名
        """
        pass
    
    @abstractmethod
    def _update_edge(self, edge: GraphEdge, graph_name: str) -> bool:
        """
        子类实现：底层更新边逻辑（用于失效时间更新）
        
        Args:
            edge: 边对象
            graph_name: 表名
        """
        pass
