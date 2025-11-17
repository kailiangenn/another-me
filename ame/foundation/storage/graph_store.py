"""
GraphStore - 图谱存储（基于 FalkorDB）
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

try:
    from falkordb import FalkorDB
    FALKORDB_AVAILABLE = True
except ImportError:
    FALKORDB_AVAILABLE = False
    logging.warning("FalkorDB not installed. Install with: pip install falkordb")

from .base import StorageBase


logger = logging.getLogger(__name__)


class GraphStore(StorageBase):
    """
    图谱存储实现（FalkorDB）
    
    特性：
    - 实体关系建模
    - 多跳知识推理
    - 时间序列演化分析
    - Cypher 查询支持
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "another_me",
        password: Optional[str] = None,
        **kwargs
    ):
        """
        Args:
            host: FalkorDB 主机
            port: 端口
            graph_name: 图谱名称
            password: 密码（可选）
        """
        if not FALKORDB_AVAILABLE:
            raise ImportError(
                "FalkorDB is required. Install with: pip install falkordb redis"
            )
        
        self.host = host
        self.port = port
        self.graph_name = graph_name
        
        # 初始化客户端
        self.client = FalkorDB(host=host, port=port, password=password)
        self.graph = self.client.select_graph(graph_name)
        
        # 初始化索引
        self._init_schema()
    
    def _init_schema(self):
        """初始化图谱结构"""
        try:
            self.graph.query("CREATE INDEX FOR (d:Document) ON (d.id)")
            self.graph.query("CREATE INDEX FOR (e:Entity) ON (e.name)")
        except Exception as e:
            logger.debug(f"Schema init: {e}")
    
    async def insert(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """插入文档节点"""
        props = {
            "id": doc_id,
            "content": data.get("content", ""),
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            **data.get("metadata", {})
        }
        
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()])
        cypher = f"CREATE (d:Document {{{props_str}}})"
        
        try:
            self.graph.query(cypher, props)
            return True
        except Exception as e:
            logger.error(f"Insert document failed: {e}")
            return False
    
    async def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档节点"""
        cypher = "MATCH (d:Document {id: $doc_id}) RETURN d"
        
        try:
            result = self.graph.query(cypher, {"doc_id": doc_id})
            if result.result_set:
                # 解析节点属性
                node = result.result_set[0][0]
                return {"doc_id": doc_id, "data": node}
            return None
        except Exception as e:
            logger.error(f"Get document failed: {e}")
            return None
    
    async def delete(self, doc_id: str) -> bool:
        """删除文档节点及关系"""
        cypher = "MATCH (d:Document {id: $doc_id}) DETACH DELETE d"
        
        try:
            self.graph.query(cypher, {"doc_id": doc_id})
            return True
        except Exception as e:
            logger.error(f"Delete document failed: {e}")
            return False
    
    async def search(
        self,
        query: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """图谱检索（基于实体）"""
        # GraphStore 主要用于关系检索，不支持向量检索
        logger.warning("GraphStore does not support vector search")
        return []
    
    async def create_entity(
        self,
        entity_name: str,
        entity_type: str = "Entity",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        创建实体节点
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            metadata: 元数据
        
        Returns:
            entity_id: 实体ID
        """
        props = {"name": entity_name, "type": entity_type.upper()}
        if metadata:
            props.update(metadata)
        
        props_items = [f"e.{k} = ${k}" for k in props.keys()]
        props_set = ", ".join(props_items)
        
        cypher = f"""
        MERGE (e:Entity {{name: $name}})
        ON CREATE SET e.id = $name, {props_set}
        ON MATCH SET {props_set}
        RETURN e.id
        """
        
        try:
            result = self.graph.query(cypher, props)
            if result.result_set:
                return result.result_set[0][0]
            return entity_name
        except Exception as e:
            logger.error(f"Create entity failed: {e}")
            return entity_name
    
    async def create_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        创建关系
        
        Args:
            source_id: 源节点ID
            target_id: 目标节点ID
            relation_type: 关系类型
            properties: 关系属性
        """
        rel_props = properties or {}
        rel_props["created_at"] = datetime.now().isoformat()
        
        props_str = "{" + ", ".join([f"{k}: ${k}" for k in rel_props.keys()]) + "}"
        
        cypher = f"""
        MATCH (s {{id: $source}}), (t {{id: $target}})
        MERGE (s)-[r:{relation_type}]->(t)
        ON CREATE SET r = {props_str}
        """
        
        params = {"source": source_id, "target": target_id, **rel_props}
        
        try:
            self.graph.query(cypher, params)
            return True
        except Exception as e:
            logger.error(f"Create relation failed: {e}")
            return False
    
    async def search_by_entities(
        self,
        entities: List[str],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """基于实体检索文档"""
        if not entities:
            return []
        
        cypher = """
        UNWIND $entities AS entity_name
        MATCH (d:Document)-[:MENTIONS]->(e:Entity)
        WHERE e.name = entity_name
        WITH d, COLLECT(DISTINCT e.name) AS matched_entities, COUNT(e) as match_count
        RETURN 
            d.id AS doc_id,
            d.timestamp AS timestamp,
            match_count AS relevance,
            matched_entities
        ORDER BY relevance DESC, timestamp DESC
        LIMIT $top_k
        """
        
        try:
            result = self.graph.query(cypher, {"entities": entities, "top_k": top_k})
            
            if not result.result_set:
                return []
            
            max_relevance = max([row[2] for row in result.result_set])
            
            return [
                {
                    "doc_id": row[0],
                    "score": float(row[2]) / max_relevance,
                    "source": "graph",
                    "matched_entities": row[3],
                    "timestamp": row[1]
                }
                for row in result.result_set
            ]
        except Exception as e:
            logger.error(f"Search by entities failed: {e}")
            return []
    
    async def find_related_docs(
        self,
        doc_id: str,
        max_hops: int = 2,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """查找相关文档（多跳推理）"""
        cypher = """
        MATCH (d1:Document {id: $doc_id})-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(d2:Document)
        WHERE d1 <> d2
        WITH d2, COLLECT(DISTINCT e.name) AS shared_entities, COUNT(e) AS entity_count
        RETURN 
            d2.id AS doc_id,
            1 AS distance,
            entity_count,
            shared_entities
        ORDER BY entity_count DESC
        LIMIT $limit
        """
        
        try:
            result = self.graph.query(cypher, {"doc_id": doc_id, "limit": limit})
            
            if not result.result_set:
                return []
            
            max_count = max([row[2] for row in result.result_set])
            
            return [
                {
                    "doc_id": row[0],
                    "distance": row[1],
                    "score": float(row[2]) / max_count,
                    "shared_entities": row[3]
                }
                for row in result.result_set
            ]
        except Exception as e:
            logger.error(f"Find related docs failed: {e}")
            return []
    
    async def execute_cypher(
        self,
        query: str,
        parameters: Optional[Dict] = None
    ) -> List[Dict]:
        """执行自定义 Cypher 查询"""
        try:
            result = self.graph.query(query, parameters or {})
            
            if not result.result_set:
                return []
            
            headers = result.header if hasattr(result, 'header') else []
            
            return [
                {headers[i]: row[i] for i in range(len(row))}
                for row in result.result_set
            ]
        except Exception as e:
            logger.error(f"Execute cypher failed: {e}")
            return []
    
    def close(self):
        """关闭连接"""
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                logger.error(f"Close connection failed: {e}")
