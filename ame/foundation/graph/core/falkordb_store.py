"""
FalkorDB 图存储实现（只实现底层操作）
"""
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from falkordb import FalkorDB
except ImportError:
    logger.warning("FalkorDB not installed, please install: pip install falkordb")
    FalkorDB = None

from .base import GraphStoreBase
from ..utils.models import GraphNode, GraphEdge, QueryResult, NodeLabel, RelationType, GraphType
from ..utils.exceptions import ConnectionError, QueryError, GraphStoreError


class FalkorDBStore(GraphStoreBase):
    """
    FalkorDB 实现（只实现底层方法）
    无需关心 Schema、QueryBuilder、TimeHandler
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        base_name: str = "another_me"
    ):
        super().__init__(host, port, base_name)
        self.client = None
        self.life_graph = None
        self.work_graph = None
    
    # ========== 实现抽象方法 ==========
    
    def _connect(self) -> None:
        """实现：FalkorDB 连接逻辑"""
        if FalkorDB is None:
            raise GraphStoreError("FalkorDB not installed")
        
        try:
            self.client = FalkorDB(host=self.host, port=self.port)
            # 连接时只创建客户端，表的初始化在 _init_graph 中进行
        except Exception as e:
            raise ConnectionError(
                f"Failed to connect to FalkorDB: {str(e)}",
                host=self.host,
                port=self.port
            )
    
    def _disconnect(self) -> None:
        """实现：FalkorDB 断开连接"""
        if self.client:
            self.client.close()
            self.client = None
            self.life_graph = None
            self.work_graph = None
    
    def _init_graph(self, graph_type: GraphType) -> None:
        """
        实现：初始化图谱表（创建或加载）
        
        Args:
            graph_type: 图谱类型（LIFE 或 WORK）
        """
        try:
            if graph_type == GraphType.LIFE:
                self.life_graph = self.client.select_graph(self.life_graph_name)
                logger.info(f"Initialized life graph: {self.life_graph_name}")
            elif graph_type == GraphType.WORK:
                self.work_graph = self.client.select_graph(self.work_graph_name)
                logger.info(f"Initialized work graph: {self.work_graph_name}")
            else:
                raise GraphStoreError(f"Unknown graph type: {graph_type}")
        except Exception as e:
            raise GraphStoreError(f"Failed to initialize {graph_type.value} graph: {str(e)}")

    def _get_graph(self, graph_name: str):
        """根据表名获取对应的图对象"""
        if graph_name == self.life_graph_name:
            return self.life_graph
        elif graph_name == self.work_graph_name:
            return self.work_graph
        else:
            raise GraphStoreError(f"Unknown graph name: {graph_name}")

    def _add_node(self, node: GraphNode, graph_name: str) -> bool:
        """实现：FalkorDB 添加节点（纯底层操作）"""
        try:
            graph = self._get_graph(graph_name)
            
            # 构建属性字符串
            props_list = [f"id: '{node.id}'"]
            for key, value in node.properties.items():
                if isinstance(value, str):
                    props_list.append(f"{key}: '{value}'")
                else:
                    props_list.append(f"{key}: {value}")
            props_str = ", ".join(props_list)
            
            # 执行 Cypher
            cypher = f"CREATE (n:{node.label.value} {{{props_str}}}) RETURN n"
            graph.query(cypher)
            return True
        except Exception as e:
            logger.error(f"FalkorDB add_node failed: {str(e)}")
            raise GraphStoreError(f"Failed to add node: {str(e)}")
    
    def _get_node(self, node_id: str, graph_name: str) -> Optional[GraphNode]:
        """实现：FalkorDB 获取节点"""
        try:
            graph = self._get_graph(graph_name)
            
            cypher = "MATCH (n {id: $id}) RETURN n, labels(n) as labels"
            result = graph.query(cypher, {"id": node_id})
            
            if result.result_set and len(result.result_set) > 0:
                row = result.result_set[0]
                node_data = row[0]
                labels = row[1]
                
                # 提取属性
                properties = {}
                if hasattr(node_data, 'properties'):
                    properties = dict(node_data.properties)
                
                return GraphNode(
                    id=node_id,
                    label=NodeLabel(labels[0]) if labels else NodeLabel.ENTITY,
                    properties=properties
                )
            return None
        except Exception as e:
            logger.error(f"FalkorDB get_node failed: {str(e)}")
            return None
    
    def _update_node(self, node_id: str, properties: Dict[str, Any], graph_name: str) -> bool:
        """实现：FalkorDB 更新节点属性"""
        try:
            graph = self._get_graph(graph_name)
            
            set_clauses = []
            params = {"id": node_id}
            
            for key, value in properties.items():
                param_key = f"prop_{key}"
                set_clauses.append(f"n.{key} = ${param_key}")
                params[param_key] = value
            
            set_clause = ", ".join(set_clauses)
            cypher = f"MATCH (n {{id: $id}}) SET {set_clause} RETURN n"
            
            graph.query(cypher, params)
            return True
        except Exception as e:
            logger.error(f"FalkorDB update_node failed: {str(e)}")
            return False
    
    def _delete_node(self, node_id: str, graph_name: str) -> bool:
        """实现：FalkorDB 删除节点"""
        try:
            graph = self._get_graph(graph_name)
            
            cypher = "MATCH (n {id: $id}) DETACH DELETE n"
            graph.query(cypher, {"id": node_id})
            return True
        except Exception as e:
            logger.error(f"FalkorDB delete_node failed: {str(e)}")
            return False
    
    def _add_edge(self, edge: GraphEdge, graph_name: str) -> bool:
        """实现：FalkorDB 添加边（纯底层操作）"""
        try:
            graph = self._get_graph(graph_name)
            
            # 构建边属性
            props_list = []
            for key, value in edge.properties.items():
                if isinstance(value, str):
                    props_list.append(f"{key}: '{value}'")
                else:
                    props_list.append(f"{key}: {value}")
            props_str = ", ".join(props_list) if props_list else ""
            
            # 执行 Cypher
            cypher = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            CREATE (a)-[r:{edge.relation_type.value} {{{props_str}}}]->(b)
            RETURN r
            """
            
            params = {
                "source_id": edge.source_id,
                "target_id": edge.target_id
            }
            
            graph.query(cypher, params)
            return True
        except Exception as e:
            logger.error(f"FalkorDB add_edge failed: {str(e)}")
            raise GraphStoreError(f"Failed to add edge: {str(e)}")
    
    def _get_edges(self, source_id: str, target_id: Optional[str], graph_name: str) -> List[GraphEdge]:
        """实现：FalkorDB 获取边"""
        try:
            graph = self._get_graph(graph_name)
            
            if target_id:
                cypher = """
                MATCH (a {id: $source_id})-[r]->(b {id: $target_id})
                RETURN a.id as source, b.id as target, type(r) as rel_type, properties(r) as props
                """
                params = {"source_id": source_id, "target_id": target_id}
            else:
                cypher = """
                MATCH (a {id: $source_id})-[r]->(b)
                RETURN a.id as source, b.id as target, type(r) as rel_type, properties(r) as props
                """
                params = {"source_id": source_id}
            
            result = graph.query(cypher, params)
            edges = []
            
            if result.result_set:
                for row in result.result_set:
                    props = dict(row[3]) if row[3] else {}
                    
                    edge = GraphEdge(
                        source_id=row[0],
                        target_id=row[1],
                        relation_type=RelationType(row[2]),
                        properties=props
                    )
                    edges.append(edge)
            
            return edges
        except Exception as e:
            logger.error(f"FalkorDB get_edges failed: {str(e)}")
            return []
    
    def _delete_edge(self, source_id: str, target_id: str, relation_type: RelationType, graph_name: str) -> bool:
        """实现：FalkorDB 删除边"""
        try:
            graph = self._get_graph(graph_name)
            
            cypher = f"""
            MATCH (a {{id: $source_id}})-[r:{relation_type.value}]->(b {{id: $target_id}})
            DELETE r
            """
            graph.query(cypher, {"source_id": source_id, "target_id": target_id})
            return True
        except Exception as e:
            logger.error(f"FalkorDB delete_edge failed: {str(e)}")
            return False
    
    def _query(self, cypher: str, params: Dict[str, Any], graph_name: str) -> QueryResult:
        """实现：FalkorDB 执行查询（纯底层操作）"""
        try:
            graph = self._get_graph(graph_name)
            result = graph.query(cypher, params)
            
            # 解析结果
            nodes = []
            edges = []
            
            if result.result_set:
                # 简化实现：直接返回原始数据
                # 实际使用中可以根据返回的数据结构解析
                pass
            
            return QueryResult(
                nodes=nodes,
                edges=edges,
                raw_data=result
            )
        except Exception as e:
            logger.error(f"FalkorDB query failed: {str(e)}")
            raise QueryError(f"Query execution failed: {str(e)}", query=cypher)
    
    def _update_edge(self, edge: GraphEdge, graph_name: str) -> bool:
        """实现：FalkorDB 更新边属性（用于失效时间更新）"""
        try:
            graph = self._get_graph(graph_name)
            
            set_clauses = []
            params = {
                "source_id": edge.source_id,
                "target_id": edge.target_id
            }
            
            for key, value in edge.properties.items():
                param_key = f"prop_{key}"
                set_clauses.append(f"r.{key} = ${param_key}")
                params[param_key] = value
            
            set_clause = ", ".join(set_clauses)
            cypher = f"""
            MATCH (a {{id: $source_id}})-[r:{edge.relation_type.value}]->(b {{id: $target_id}})
            SET {set_clause}
            RETURN r
            """
            
            graph.query(cypher, params)
            return True
        except Exception as e:
            logger.error(f"FalkorDB update_edge failed: {str(e)}")
            return False
