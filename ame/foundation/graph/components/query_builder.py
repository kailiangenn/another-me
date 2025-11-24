"""
Cypher 查询构建器（链式 API）
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..utils.models import NodeLabel, RelationType


class QueryBuilder:
    """
    Cypher 查询构建器
    提供链式 API，自动参数化，防止注入攻击
    """
    
    def __init__(self):
        self._match_clauses: List[str] = []
        self._where_clauses: List[str] = []
        self._return_clause: str = ""
        self._params: Dict[str, Any] = {}
        self._param_counter = 0
    
    def reset(self) -> "QueryBuilder":
        """重置构建器"""
        self._match_clauses = []
        self._where_clauses = []
        self._return_clause = ""
        self._params = {}
        self._param_counter = 0
        return self
    
    def match_node(
        self, 
        label: Optional[NodeLabel] = None, 
        alias: str = "n"
    ) -> "QueryBuilder":
        """匹配节点"""
        if label:
            clause = f"MATCH ({alias}:{label.value})"
        else:
            clause = f"MATCH ({alias})"
        self._match_clauses.append(clause)
        return self
    
    def match_node_by_id(self, node_id: str, alias: str = "n") -> "QueryBuilder":
        """通过 ID 匹配节点"""
        param_name = self._add_param(node_id)
        self._match_clauses.append(f"MATCH ({alias} {{id: ${param_name}}})")
        return self
    
    def with_relation(
        self,
        relation_type: Optional[RelationType] = None,
        direction: str = "out",  # "out", "in", "both"
        source_alias: str = "n",
        target_alias: str = "m",
        edge_alias: str = "r"
    ) -> "QueryBuilder":
        """添加关系匹配"""
        rel_str = f":{relation_type.value}" if relation_type else ""
        
        if direction == "out":
            pattern = f"({source_alias})-[{edge_alias}{rel_str}]->({target_alias})"
        elif direction == "in":
            pattern = f"({source_alias})<-[{edge_alias}{rel_str}]-({target_alias})"
        else:  # both
            pattern = f"({source_alias})-[{edge_alias}{rel_str}]-({target_alias})"
        
        # 更新最后一个 MATCH 子句
        if self._match_clauses:
            self._match_clauses[-1] += f" {pattern}"
        else:
            self._match_clauses.append(f"MATCH {pattern}")
        
        return self
    
    def where(self, field: str, operator: str, value: Any, alias: str = "n") -> "QueryBuilder":
        """添加 WHERE 条件"""
        param_name = self._add_param(value)
        self._where_clauses.append(f"{alias}.{field} {operator} ${param_name}")
        return self
    
    def where_time_valid(
        self, 
        at_time: Optional[datetime] = None, 
        edge_alias: str = "r"
    ) -> "QueryBuilder":
        """添加时间有效性过滤"""
        check_time = at_time or datetime.now()
        time_param = self._add_param(check_time.isoformat())
        
        self._where_clauses.append(
            f"{edge_alias}.create_time <= ${time_param} AND "
            f"(NOT exists({edge_alias}.invalid_time) OR {edge_alias}.invalid_time > ${time_param})"
        )
        return self
    
    def return_nodes(self, alias: str = "n") -> "QueryBuilder":
        """返回节点"""
        self._return_clause = f"RETURN {alias}"
        return self
    
    def return_neighbors(self, alias: str = "m") -> "QueryBuilder":
        """返回邻居节点"""
        self._return_clause = f"RETURN {alias}"
        return self
    
    def return_all(self) -> "QueryBuilder":
        """返回所有"""
        self._return_clause = "RETURN *"
        return self
    
    def limit(self, count: int) -> "QueryBuilder":
        """限制返回数量"""
        if self._return_clause:
            self._return_clause += f" LIMIT {count}"
        return self
    
    def build(self) -> str:
        """构建最终的 Cypher 查询"""
        parts = []
        
        # MATCH 子句
        parts.extend(self._match_clauses)
        
        # WHERE 子句
        if self._where_clauses:
            parts.append(f"WHERE {' AND '.join(self._where_clauses)}")
        
        # RETURN 子句
        if self._return_clause:
            parts.append(self._return_clause)
        
        return "\n".join(parts)
    
    def get_params(self) -> Dict[str, Any]:
        """获取参数"""
        return self._params
    
    def _add_param(self, value: Any) -> str:
        """添加参数（自动命名）"""
        param_name = f"param_{self._param_counter}"
        self._params[param_name] = value
        self._param_counter += 1
        return param_name
