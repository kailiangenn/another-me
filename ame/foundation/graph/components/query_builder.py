"""
Cypher 查询构建器（链式 API）
"""
from typing import Optional, List, Dict, Any
from datetime import datetime

from ..utils.models import NodeLabel, RelationType
from ..utils.exceptions import GraphStoreError


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
        # 强制类型检查
        if label is not None and not isinstance(label, NodeLabel):
            raise GraphStoreError("Label must be an instance of NodeLabel enum")
        
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
    
    def match_nodes_by_properties(
        self, 
        properties: Dict[str, Any], 
        label: Optional[NodeLabel] = None, 
        alias: str = "n"
    ) -> "QueryBuilder":
        """通过属性匹配节点"""
        # 强制类型检查
        if label is not None and not isinstance(label, NodeLabel):
            raise GraphStoreError("Label must be an instance of NodeLabel enum")
        
        prop_conditions = []
        for key, value in properties.items():
            param_name = self._add_param(value)
            prop_conditions.append(f"{key}: ${param_name}")
        
        props_str = "{ " + ", ".join(prop_conditions) + " }" if prop_conditions else ""
        label_str = f":{label.value}" if label else ""
        
        clause = f"MATCH ({alias}{label_str} {props_str})"
        self._match_clauses.append(clause)
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
        # 强制类型检查
        if relation_type is not None and not isinstance(relation_type, RelationType):
            raise GraphStoreError("Relation type must be an instance of RelationType enum")
        
        rel_str = f":{relation_type.value}" if relation_type else ""
        
        # 构建关系模式
        if direction == "out":
            pattern = f"-[{edge_alias}{rel_str}]->({target_alias})"
        elif direction == "in":
            pattern = f"<-[{edge_alias}{rel_str}]-({target_alias})"
        else:  # both
            pattern = f"-[{edge_alias}{rel_str}]-({target_alias})"
        
        # 更新最后一个 MATCH 子句，将关系模式正确连接到源节点上
        if self._match_clauses:
            last_clause = self._match_clauses[-1]
            # 特别处理 match_node_by_id 产生的模式，如 "MATCH (n {id: $param_0})"
            if last_clause.startswith("MATCH (") and "{id: $" in last_clause and last_clause.endswith("})"):
                # 直接在最后添加关系模式
                self._match_clauses[-1] = last_clause[:-1] + f"){pattern}"
            # 处理一般的节点匹配模式
            elif f"({source_alias})" in last_clause and not ("->" in last_clause or "<-" in last_clause):
                # 将节点匹配转换为带关系的匹配
                start_pos = last_clause.rfind(f"({source_alias}")
                if start_pos != -1:
                    end_pos = last_clause.find(")", start_pos)
                    if end_pos != -1:
                        node_part = last_clause[start_pos:end_pos+1]
                        self._match_clauses[-1] = last_clause.replace(node_part, f"{node_part}{pattern}", 1)
                    else:
                        self._match_clauses.append(f"MATCH ({source_alias}){pattern}")
                else:
                    self._match_clauses.append(f"MATCH ({source_alias}){pattern}")
            else:
                # 如果最后一个子句已经是带关系的匹配，或者不是以源别名结尾，则添加一个新的 MATCH 子句
                self._match_clauses.append(f"MATCH ({source_alias}){pattern}")
        else:
            # 如果还没有 MATCH 子句，则添加一个新的
            self._match_clauses.append(f"MATCH ({source_alias}){pattern}")
        
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
    
    def where_node_property_in(
        self, 
        field: str, 
        values: List[Any], 
        alias: str = "n"
    ) -> "QueryBuilder":
        """添加节点属性 IN 条件"""
        param_names = []
        for value in values:
            param_name = self._add_param(value)
            param_names.append(f"${param_name}")
        
        self._where_clauses.append(f"{alias}.{field} IN [{', '.join(param_names)}]")
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
    
    def return_count(self, alias: str = "n") -> "QueryBuilder":
        """返回计数"""
        self._return_clause = f"RETURN count({alias}) as count"
        return self
    
    def order_by(self, field: str, direction: str = "ASC", alias: str = "n") -> "QueryBuilder":
        """添加排序"""
        if self._return_clause:
            self._return_clause += f" ORDER BY {alias}.{field} {direction}"
        return self
    
    def limit(self, count: int) -> "QueryBuilder":
        """限制返回数量"""
        if self._return_clause:
            self._return_clause += f" LIMIT {count}"
        return self
    
    def find_path(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 3,
        relationship_types: Optional[List[RelationType]] = None
    ) -> "QueryBuilder":
        """查找两个节点之间的路径"""
        # 强制类型检查
        if relationship_types is not None:
            for rt in relationship_types:
                if not isinstance(rt, RelationType):
                    raise GraphStoreError("All relationship types must be instances of RelationType enum")
        
        start_param = self._add_param(start_node_id)
        end_param = self._add_param(end_node_id)
        
        # 构建关系类型过滤
        rel_types = ""
        if relationship_types:
            type_names = [rt.value for rt in relationship_types]
            rel_types = f":{ '|'.join(type_names) }"
        
        self._match_clauses.append(
            f"MATCH path = (start {{id: ${start_param}}})-[{rel_types}*1..{max_depth}]->(end {{id: ${end_param}}})"
        )
        self._return_clause = "RETURN path"
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