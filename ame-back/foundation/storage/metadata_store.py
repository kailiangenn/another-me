"""
MetadataStore - 元数据存储（基于 SQLite）
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from .base import StorageBase


logger = logging.getLogger(__name__)


class MetadataStore(StorageBase):
    """
    元数据存储实现（SQLite）
    
    特性：
    - 文档元数据管理
    - 索引信息追踪
    - 状态管理
    - 快速查询
    """
    
    def __init__(self, db_path: str = "./data/metadata.db"):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    doc_type TEXT NOT NULL,
                    source TEXT,
                    timestamp DATETIME,
                    
                    -- Vector Store 字段
                    vector_index INTEGER,
                    layer TEXT DEFAULT 'hot',
                    stored_in_vector BOOLEAN DEFAULT 0,
                    
                    -- Graph Store 字段
                    graph_node_id TEXT,
                    entities TEXT,
                    stored_in_graph BOOLEAN DEFAULT 0,
                    
                    -- 状态字段
                    status TEXT DEFAULT 'active',
                    importance REAL DEFAULT 0.5,
                    
                    -- 元数据
                    metadata TEXT,
                    
                    -- 时间戳
                    created_at DATETIME,
                    updated_at DATETIME
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(doc_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON documents(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON documents(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_layer ON documents(layer)")
            
            conn.commit()
    
    async def insert(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """插入文档元数据"""
        now = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT INTO documents 
                    (id, content, doc_type, source, timestamp,
                     vector_index, layer, stored_in_vector,
                     graph_node_id, entities, stored_in_graph,
                     status, importance, metadata, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    data.get("content", ""),
                    data.get("doc_type", "unknown"),
                    data.get("source"),
                    data.get("timestamp", now),
                    data.get("vector_index"),
                    data.get("layer", "hot"),
                    data.get("stored_in_vector", False),
                    data.get("graph_node_id"),
                    json.dumps(data.get("entities", [])),
                    data.get("stored_in_graph", False),
                    data.get("status", "active"),
                    data.get("importance", 0.5),
                    json.dumps(data.get("metadata", {})),
                    now,
                    now,
                ))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Insert metadata failed: {e}")
                return False
    
    async def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """获取文档元数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return self._row_to_dict(row)
    
    async def update(self, doc_id: str, updates: Dict[str, Any]) -> bool:
        """更新文档元数据"""
        updates["updated_at"] = datetime.now().isoformat()
        
        # 处理 JSON 字段
        if "entities" in updates:
            updates["entities"] = json.dumps(updates["entities"])
        if "metadata" in updates:
            updates["metadata"] = json.dumps(updates["metadata"])
        
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        query = f"UPDATE documents SET {set_clause} WHERE id = ?"
        params = list(updates.values()) + [doc_id]
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(query, params)
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Update metadata failed: {e}")
                return False
    
    async def delete(self, doc_id: str) -> bool:
        """删除文档元数据"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                return True
            except Exception as e:
                logger.error(f"Delete metadata failed: {e}")
                return False
    
    async def search(
        self,
        query: List[float],
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """搜索（元数据不支持向量检索）"""
        logger.warning("MetadataStore does not support vector search")
        return []
    
    async def list(
        self,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        layer: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列表查询"""
        query = "SELECT * FROM documents WHERE 1=1"
        params = []
        
        if doc_type:
            query += " AND doc_type = ?"
            params.append(doc_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if layer:
            query += " AND layer = ?"
            params.append(layer)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    async def count(
        self,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        layer: Optional[str] = None
    ) -> int:
        """统计文档数量"""
        query = "SELECT COUNT(*) FROM documents WHERE 1=1"
        params = []
        
        if doc_type:
            query += " AND doc_type = ?"
            params.append(doc_type)
        if status:
            query += " AND status = ?"
            params.append(status)
        if layer:
            query += " AND layer = ?"
            params.append(layer)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchone()[0]
    
    async def get_by_ids(self, doc_ids: List[str]) -> List[Dict[str, Any]]:
        """批量获取文档"""
        if not doc_ids:
            return []
        
        placeholders = ",".join(["?" for _ in doc_ids])
        query = f"SELECT * FROM documents WHERE id IN ({placeholders})"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, doc_ids)
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """转换数据库行为字典"""
        data = dict(row)
        
        # 解析 JSON 字段
        if data.get("entities"):
            try:
                data["entities"] = json.loads(data["entities"])
            except:
                data["entities"] = []
        
        if data.get("metadata"):
            try:
                data["metadata"] = json.loads(data["metadata"])
            except:
                data["metadata"] = {}
        
        return data
    
    def close(self):
        """关闭连接（SQLite 自动管理）"""
        pass
