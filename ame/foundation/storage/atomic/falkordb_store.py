"""
FalkorDB 图数据库实现

特性：
- 支持多Graph（相当于多表）
- 自动创建Graph（不存在则创建）
- 基于Redis协议
- 支持时间范围查询
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger

try:
    from falkordb import FalkorDB
except ImportError:
    logger.warning("falkordb未安装，请运行: pip install falkordb")
    raise

from .base import GraphStoreBase
from ..core.models import GraphNode, GraphEdge
from ..core.schema import NodeLabel, RelationType
from ..core.exceptions import ConnectionError as StorageConnectionError, QueryError


class FalkorDBStore(GraphStoreBase):
    """
    FalkorDB 实现
    
    参数：
        host: Redis主机地址
        port: Redis端口
        graph_name: Graph名称（生活图谱/工作图谱）
        password: Redis密码（可选）
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "default_graph",
        password: Optional[str] = None,
        db: int = 0
    ):
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self.password = password
        self.db = db
        
        self.client: Optional[FalkorDB] = None
        self.graph = None
    
    async def connect(self) -> None:
        """建立连接并创建Graph（如果不存在）"""
        if FalkorDB is None:
            raise ImportError("falkordb未安装，请运行: pip install falkordb")
        
        try:
            # 创建FalkorDB客户端
            self.client = FalkorDB(
                host=self.host,
                port=self.port,
                password=self.password,
                # decode_responses=True
            )
            
            # 选择或创建Graph
            self.graph = self.client.select_graph(self.graph_name)
            
            logger.info(
                f"FalkorDB连接成功: {self.host}:{self.port}, "
                f"Graph={self.graph_name}"
            )
            
            # 创建索引（优化查询性能）
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"FalkorDB连接失败: {e}")
            raise StorageConnectionError(f"无法连接到FalkorDB: {e}", self.host, self.port)
    
    async def disconnect(self) -> None:
        """断开连接"""
        if self.client:
            self.client.connection.close()
            logger.info(f"FalkorDB已断开: Graph={self.graph_name}")
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            if not self.graph:
                return False
            
            # 执行简单查询测试连接
            self.graph.query("RETURN 1")
            return True
        except Exception:
            return False
    
    async def _create_indexes(self) -> None:
        """创建索引（提升查询性能）"""
        try:
            # 为常用属性创建索引
            index_configs = [
                ("Person", "name"),
                ("Person", "user_id"),
                ("Task", "status"),
                ("Task", "user_id"),
                ("Project", "name"),
                ("Document", "title"),
            ]
            
            for label, prop in index_configs:
                try:
                    self.graph.query(f"CREATE INDEX FOR (n:{label}) ON (n.{prop})")
                except Exception:
                    # 索引可能已存在，忽略错误
                    pass
            
            logger.debug(f"索引创建完成: Graph={self.graph_name}")
        
        except Exception as e:
            logger.warning(f"创建索引时出错: {e}")
    
    # ===== 节点操作 =====
    
    async def create_node(self, node: GraphNode) -> str:
        """创建节点"""
        try:
            # 构建属性字符串
            props_str = self._build_properties_string(node.properties)
            
            # Cypher查询
            cypher = f"""
            CREATE (n:{node.label.value} {{{props_str}}})
            RETURN id(n) as node_id
            """
            
            result = self.graph.query(cypher)
            
            if result.result_set:
                node_id = str(result.result_set[0][0])
                logger.debug(f"节点创建成功: {node.label.value}, ID={node_id}")
                return node_id
            else:
                raise QueryError("创建节点失败：未返回ID")
        
        except Exception as e:
            logger.error(f"创建节点失败: {e}")
            raise QueryError(f"创建节点失败: {e}")
    
    async def get_node(self, node_id: str) -> Optional[GraphNode]:
        """获取节点"""
        try:
            cypher = f"MATCH (n) WHERE id(n) = {node_id} RETURN n"
            result = self.graph.query(cypher)
            
            if result.result_set and len(result.result_set) > 0:
                return self._parse_node(result.result_set[0][0])
            return None
        
        except Exception as e:
            logger.error(f"获取节点失败: {e}")
            return None
    
    async def update_node(self, node_id: str, properties: Dict[str, Any]) -> bool:
        """更新节点属性"""
        try:
            set_clauses = []
            for key, value in properties.items():
                if isinstance(value, str):
                    set_clauses.append(f"n.{key} = '{value}'")
                elif isinstance(value, bool):
                    set_clauses.append(f"n.{key} = {str(value).lower()}")
                elif value is None:
                    set_clauses.append(f"n.{key} = null")
                else:
                    set_clauses.append(f"n.{key} = {value}")
            
            set_str = ", ".join(set_clauses)
            
            cypher = f"""
            MATCH (n) WHERE id(n) = {node_id}
            SET {set_str}
            RETURN n
            """
            
            result = self.graph.query(cypher)
            return result.properties_set > 0
        
        except Exception as e:
            logger.error(f"更新节点失败: {e}")
            return False
    
    async def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        try:
            cypher = f"""
            MATCH (n) WHERE id(n) = {node_id}
            DETACH DELETE n
            """
            
            result = self.graph.query(cypher)
            return result.nodes_deleted > 0
        
        except Exception as e:
            logger.error(f"删除节点失败: {e}")
            return False
    
    async def find_nodes(
        self,
        label: Optional[NodeLabel] = None,
        properties: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[GraphNode]:
        """查找节点"""
        try:
            # 构建查询
            label_str = f":{label.value}" if label else ""
            
            where_clauses = []
            if properties:
                for key, value in properties.items():
                    if isinstance(value, str):
                        where_clauses.append(f"n.{key} = '{value}'")
                    elif isinstance(value, bool):
                        where_clauses.append(f"n.{key} = {str(value).lower()}")
                    elif value is None:
                        where_clauses.append(f"n.{key} IS NULL")
                    else:
                        where_clauses.append(f"n.{key} = {value}")
            
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            cypher = f"""
            MATCH (n{label_str})
            {where_str}
            RETURN n
            LIMIT {limit}
            """
            
            result = self.graph.query(cypher)
            
            nodes = []
            if result.result_set:
                for row in result.result_set:
                    node = self._parse_node(row[0])
                    if node:
                        nodes.append(node)
            
            return nodes
        
        except Exception as e:
            logger.error(f"查找节点失败: {e}")
            return []
    
    # ===== 边操作 =====
    
    async def create_edge(self, edge: GraphEdge) -> str:
        """创建边"""
        try:
            # 将时间属性添加到properties中
            properties = edge.properties.copy()
            properties['valid_from'] = edge.valid_from.isoformat()
            if edge.valid_until:
                properties['valid_until'] = edge.valid_until.isoformat()
            properties['weight'] = edge.weight
            
            props_str = self._build_properties_string(properties)
            
            cypher = f"""
            MATCH (a), (b)
            WHERE id(a) = {edge.source_id} AND id(b) = {edge.target_id}
            CREATE (a)-[r:{edge.relation.value} {{{props_str}}}]->(b)
            RETURN id(r) as edge_id
            """
            
            result = self.graph.query(cypher)
            
            if result.result_set:
                edge_id = str(result.result_set[0][0])
                logger.debug(f"边创建成功: {edge.relation.value}, ID={edge_id}")
                return edge_id
            else:
                raise QueryError("创建边失败：未返回ID")
        
        except Exception as e:
            logger.error(f"创建边失败: {e}")
            raise QueryError(f"创建边失败: {e}")
    
    async def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """获取边"""
        try:
            cypher = f"""
            MATCH ()-[r]->()
            WHERE id(r) = {edge_id}
            RETURN r, startNode(r), endNode(r)
            """
            result = self.graph.query(cypher)
            
            if result.result_set and len(result.result_set) > 0:
                row = result.result_set[0]
                return self._parse_edge(row[0], row[1], row[2])
            return None
        
        except Exception as e:
            logger.error(f"获取边失败: {e}")
            return None
    
    async def update_edge(self, edge_id: str, properties: Dict[str, Any]) -> bool:
        """更新边属性"""
        try:
            set_clauses = []
            for key, value in properties.items():
                if isinstance(value, str):
                    set_clauses.append(f"r.{key} = '{value}'")
                elif isinstance(value, bool):
                    set_clauses.append(f"r.{key} = {str(value).lower()}")
                elif value is None:
                    set_clauses.append(f"r.{key} = null")
                else:
                    set_clauses.append(f"r.{key} = {value}")
            
            set_str = ", ".join(set_clauses)
            
            cypher = f"""
            MATCH ()-[r]->()
            WHERE id(r) = {edge_id}
            SET {set_str}
            RETURN r
            """
            
            result = self.graph.query(cypher)
            return result.properties_set > 0
        
        except Exception as e:
            logger.error(f"更新边失败: {e}")
            return False
    
    async def delete_edge(self, edge_id: str) -> bool:
        """删除边"""
        try:
            cypher = f"""
            MATCH ()-[r]->()
            WHERE id(r) = {edge_id}
            DELETE r
            """
            
            result = self.graph.query(cypher)
            return result.relationships_deleted > 0
        
        except Exception as e:
            logger.error(f"删除边失败: {e}")
            return False
    
    async def find_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation: Optional[RelationType] = None,
        only_valid: bool = False
    ) -> List[GraphEdge]:
        """查找边"""
        try:
            # 构建模式
            rel_str = f":{relation.value}" if relation else ""
            
            match_parts = []
            where_clauses = []
            
            if source_id and target_id:
                match_parts.append(f"MATCH (a)-[r{rel_str}]->(b)")
                where_clauses.append(f"id(a) = {source_id} AND id(b) = {target_id}")
            elif source_id:
                match_parts.append(f"MATCH (a)-[r{rel_str}]->(b)")
                where_clauses.append(f"id(a) = {source_id}")
            elif target_id:
                match_parts.append(f"MATCH (a)-[r{rel_str}]->(b)")
                where_clauses.append(f"id(b) = {target_id}")
            else:
                match_parts.append(f"MATCH (a)-[r{rel_str}]->(b)")
            
            # 只返回当前有效的边
            if only_valid:
                now_iso = datetime.now().isoformat()
                where_clauses.append(
                    f"r.valid_from <= '{now_iso}' AND "
                    f"(r.valid_until IS NULL OR r.valid_until >= '{now_iso}')"
                )
            
            match_str = match_parts[0] if match_parts else "MATCH (a)-[r]->(b)"
            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            cypher = f"""
            {match_str}
            {where_str}
            RETURN r, a, b
            LIMIT 1000
            """
            
            result = self.graph.query(cypher)
            
            edges = []
            if result.result_set:
                for row in result.result_set:
                    edge = self._parse_edge(row[0], row[1], row[2])
                    if edge:
                        edges.append(edge)
            
            return edges
        
        except Exception as e:
            logger.error(f"查找边失败: {e}")
            return []
    
    # ===== 图查询 =====
    
    async def get_neighbors(
        self,
        node_id: str,
        relation: Optional[RelationType] = None,
        direction: str = "outgoing"
    ) -> List[GraphNode]:
        """获取邻居节点（1跳）"""
        try:
            rel_str = f":{relation.value}" if relation else ""
            
            if direction == "outgoing":
                pattern = f"(n)-[r{rel_str}]->(m)"
            elif direction == "incoming":
                pattern = f"(n)<-[r{rel_str}]-(m)"
            else:  # both
                pattern = f"(n)-[r{rel_str}]-(m)"
            
            cypher = f"""
            MATCH {pattern}
            WHERE id(n) = {node_id}
            RETURN m
            """
            
            result = self.graph.query(cypher)
            
            neighbors = []
            if result.result_set:
                for row in result.result_set:
                    neighbor = self._parse_node(row[0])
                    if neighbor:
                        neighbors.append(neighbor)
            
            return neighbors
        
        except Exception as e:
            logger.error(f"获取邻居失败: {e}")
            return []
    
    async def get_edges_between(
        self,
        source_id: str,
        target_id: str
    ) -> List[GraphEdge]:
        """获取两个节点之间的所有边"""
        return await self.find_edges(source_id=source_id, target_id=target_id)
    
    # ===== 时间范围查询 =====
    
    async def find_valid_edges_at(
        self,
        timestamp: datetime,
        source_id: Optional[str] = None,
        relation: Optional[RelationType] = None
    ) -> List[GraphEdge]:
        """查找在指定时间点有效的边"""
        try:
            rel_str = f":{relation.value}" if relation else ""
            
            where_clauses = []
            if source_id:
                where_clauses.append(f"id(a) = {source_id}")
            
            # 时间范围过滤
            timestamp_iso = timestamp.isoformat()
            where_clauses.append(
                f"r.valid_from <= '{timestamp_iso}' AND "
                f"(r.valid_until IS NULL OR r.valid_until >= '{timestamp_iso}')"
            )
            
            where_str = f"WHERE {' AND '.join(where_clauses)}"
            
            cypher = f"""
            MATCH (a)-[r{rel_str}]->(b)
            {where_str}
            RETURN r, a, b
            """
            
            result = self.graph.query(cypher)
            
            edges = []
            if result.result_set:
                for row in result.result_set:
                    edge = self._parse_edge(row[0], row[1], row[2])
                    if edge:
                        edges.append(edge)
            
            return edges
        
        except Exception as e:
            logger.error(f"查找有效边失败: {e}")
            return []
    
    # ===== 原生查询 =====
    
    async def execute_cypher(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行原生Cypher查询"""
        try:
            result = self.graph.query(query, params or {})
            return result
        except Exception as e:
            logger.error(f"Cypher查询失败: {e}")
            raise QueryError(f"Cypher查询失败: {e}", query)
    
    # ===== 工具方法 =====
    
    def _build_properties_string(self, properties: Dict[str, Any]) -> str:
        """构建属性字符串"""
        parts = []
        for key, value in properties.items():
            if isinstance(value, str):
                # 转义单引号
                escaped_value = value.replace("'", "\\'")
                parts.append(f"{key}: '{escaped_value}'")
            elif isinstance(value, bool):
                parts.append(f"{key}: {str(value).lower()}")
            elif value is None:
                parts.append(f"{key}: null")
            else:
                parts.append(f"{key}: {value}")
        return ", ".join(parts)
    
    def _parse_node(self, node_data) -> Optional[GraphNode]:
        """解析FalkorDB节点数据为GraphNode"""
        try:
            # FalkorDB返回的Node对象
            if not node_data:
                return None
            
            # 获取标签
            labels = node_data.labels if hasattr(node_data, 'labels') else []
            if not labels:
                return None
            
            label_str = labels[0]
            # 转换为NodeLabel枚举
            try:
                label = NodeLabel(label_str)
            except ValueError:
                label = NodeLabel.ENTITY  # 默认为ENTITY
            
            # 获取属性
            properties = dict(node_data.properties) if hasattr(node_data, 'properties') else {}
            
            # 获取ID
            node_id = str(node_data.id) if hasattr(node_data, 'id') else None
            
            return GraphNode(
                id=node_id,
                label=label,
                properties=properties
            )
        
        except Exception as e:
            logger.error(f"解析节点数据失败: {e}")
            return None
    
    def _parse_edge(self, edge_data, start_node, end_node) -> Optional[GraphEdge]:
        """解析FalkorDB边数据为GraphEdge"""
        try:
            if not edge_data:
                return None
            
            # 获取关系类型
            relation_str = edge_data.relation if hasattr(edge_data, 'relation') else ""
            try:
                relation = RelationType(relation_str)
            except ValueError:
                relation = RelationType.LINKED_TO  # 默认
            
            # 获取属性
            properties = dict(edge_data.properties) if hasattr(edge_data, 'properties') else {}
            
            # 提取时间属性
            valid_from_str = properties.pop('valid_from', None)
            valid_until_str = properties.pop('valid_until', None)
            weight = properties.pop('weight', 1.0)
            
            # 解析时间
            valid_from = datetime.fromisoformat(valid_from_str) if valid_from_str else datetime.now()
            valid_until = datetime.fromisoformat(valid_until_str) if valid_until_str else None
            
            # 获取ID
            edge_id = str(edge_data.id) if hasattr(edge_data, 'id') else None
            
            # 获取源和目标节点ID
            source_id = str(start_node.id) if hasattr(start_node, 'id') else None
            target_id = str(end_node.id) if hasattr(end_node, 'id') else None
            
            return GraphEdge(
                id=edge_id,
                source_id=source_id,
                target_id=target_id,
                relation=relation,
                properties=properties,
                weight=float(weight),
                valid_from=valid_from,
                valid_until=valid_until
            )
        
        except Exception as e:
            logger.error(f"解析边数据失败: {e}")
            return None
