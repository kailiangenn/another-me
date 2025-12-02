"""
结构化图分析组件
基于图结构和节点属性计算相似性，不依赖embedding
"""
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import math

from ..utils.models import GraphNode, GraphEdge, GraphType, NodeLabel, RelationType
# 注意：避免循环导入，不在这里直接导入GraphStoreBase


class StructuralAnalyzer:
    """结构化图分析器"""
    
    def __init__(self, graph_store):
        # 延迟类型检查，避免循环导入
        self.graph_store = graph_store
    
    def calculate_structural_similarity(self, node_id1: str, node_id2: str, 
                                     graph_type: GraphType) -> float:
        """
        基于图结构计算节点相似性（不依赖embedding）
        
        相似性计算基于：
        1. 共同邻居数量
        2. 直接连接关系
        3. 节点标签相似性
        4. 属性相似性
        """
        # 获取节点信息
        node1 = self.graph_store.get_node(node_id1, graph_type)
        node2 = self.graph_store.get_node(node_id2, graph_type)
        
        if not node1 or not node2:
            return 0.0
        
        # 1. 计算标签相似性（相同标签得1分，不同得0分）
        label_similarity = 1.0 if node1.label == node2.label else 0.0
        
        # 2. 计算属性相似性（基于共同属性数量）
        attr_similarity = self._calculate_attribute_similarity(node1.properties, node2.properties)
        
        # 3. 计算邻居相似性
        neighbors1 = set(n.id for n in self.graph_store.find_neighbors(node_id1, graph_type))
        neighbors2 = set(n.id for n in self.graph_store.find_neighbors(node_id2, graph_type))
        
        # Jaccard相似性计算
        if len(neighbors1) == 0 and len(neighbors2) == 0:
            neighbor_similarity = 1.0 if node_id2 in neighbors1 or node_id1 in neighbors2 else 0.0
        else:
            intersection = len(neighbors1.intersection(neighbors2))
            union = len(neighbors1.union(neighbors2))
            neighbor_similarity = intersection / union if union > 0 else 0.0
        
        # 4. 直接连接检查
        direct_connection = 1.0 if node_id2 in neighbors1 or node_id1 in neighbors2 else 0.0
        
        # 综合计算相似性（可调整权重）
        total_similarity = (
            0.3 * label_similarity + 
            0.3 * attr_similarity + 
            0.3 * neighbor_similarity + 
            0.1 * direct_connection
        )
        
        return total_similarity
    
    def _calculate_attribute_similarity(self, props1: Dict, props2: Dict) -> float:
        """计算属性相似性"""
        if not props1 and not props2:
            return 1.0
        if not props1 or not props2:
            return 0.0
            
        # 找出共同属性
        common_keys = set(props1.keys()).intersection(set(props2.keys()))
        if not common_keys:
            return 0.0
            
        # 计算共同属性值的匹配度
        matches = 0
        for key in common_keys:
            if props1[key] == props2[key]:
                matches += 1
                
        return matches / len(common_keys)
    
    def find_similar_nodes(self, node_id: str, graph_type: GraphType, 
                          threshold: float = 0.5, limit: int = 10) -> List[Tuple[str, float]]:
        """
        查找相似节点
        
        Args:
            node_id: 目标节点ID
            graph_type: 图类型
            threshold: 相似性阈值
            limit: 返回结果数量限制
            
        Returns:
            相似节点列表 [(node_id, similarity_score), ...]
        """
        # 获取所有节点进行比较
        all_nodes = self.graph_store.search_nodes(graph_type=graph_type)
        
        similarities = []
        for node in all_nodes:
            if node.id == node_id:
                continue
                
            similarity = self.calculate_structural_similarity(node_id, node.id, graph_type)
            if similarity >= threshold:
                similarities.append((node.id, similarity))
        
        # 按相似性排序并限制数量
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]
    
    def calculate_centrality(self, graph_type: GraphType, 
                           centrality_type: str = "degree") -> Dict[str, float]:
        """
        计算中心性指标（基于图结构）
        
        Args:
            graph_type: 图类型
            centrality_type: 中心性类型 ("degree", "betweenness", "closeness")
        """
        if centrality_type == "degree":
            return self._calculate_degree_centrality(graph_type)
        elif centrality_type == "betweenness":
            return self._calculate_betweenness_centrality(graph_type)
        elif centrality_type == "closeness":
            return self._calculate_closeness_centrality(graph_type)
        else:
            raise ValueError(f"Unsupported centrality type: {centrality_type}")
    
    def _calculate_degree_centrality(self, graph_type: GraphType) -> Dict[str, float]:
        """计算度中心性"""
        nodes = self.graph_store.search_nodes(graph_type=graph_type)
        total_nodes = len(nodes)
        
        if total_nodes <= 1:
            return {node.id: 0.0 for node in nodes}
        
        centrality = {}
        for node in nodes:
            neighbors = self.graph_store.find_neighbors(node.id, graph_type)
            # 归一化度中心性
            centrality[node.id] = len(neighbors) / (total_nodes - 1)
            
        return centrality
    
    def _calculate_betweenness_centrality(self, graph_type: GraphType) -> Dict[str, float]:
        """计算介数中心性（简化版）"""
        nodes = self.graph_store.search_nodes(graph_type=graph_type)
        
        # 简化的介数中心性计算
        # 实际应用中可以使用更复杂的算法，这里为了性能考虑使用近似方法
        centrality = {node.id: 0.0 for node in nodes}
        
        # 对于每个节点，计算它在其他节点对之间的最短路径上的出现次数
        for source_node in nodes:
            # 使用广度优先搜索计算最短路径
            distances, predecessors = self._bfs_shortest_path(source_node.id, graph_type)
            
            # 更新介数中心性
            for target_id in distances:
                if target_id != source_node.id:
                    # 简化处理：只考虑直接邻居的贡献
                    neighbors = self.graph_store.find_neighbors(source_node.id, graph_type)
                    for neighbor in neighbors:
                        if neighbor.id == target_id:
                            centrality[neighbor.id] += 1.0
        
        # 归一化
        max_centrality = max(centrality.values()) if centrality.values() else 1
        if max_centrality > 0:
            for node_id in centrality:
                centrality[node_id] /= max_centrality
                
        return centrality
    
    def _bfs_shortest_path(self, start_node_id: str, graph_type: GraphType) -> Tuple[Dict, Dict]:
        """广度优先搜索计算最短路径"""
        distances = {start_node_id: 0}
        predecessors = {start_node_id: None}
        queue = [start_node_id]
        
        while queue:
            current_node_id = queue.pop(0)
            current_distance = distances[current_node_id]
            
            # 获取邻居节点
            neighbors = self.graph_store.find_neighbors(current_node_id, graph_type)
            for neighbor in neighbors:
                if neighbor.id not in distances:
                    distances[neighbor.id] = current_distance + 1
                    predecessors[neighbor.id] = current_node_id
                    queue.append(neighbor.id)
        
        return distances, predecessors
    
    def _calculate_closeness_centrality(self, graph_type: GraphType) -> Dict[str, float]:
        """计算接近中心性"""
        nodes = self.graph_store.search_nodes(graph_type=graph_type)
        total_nodes = len(nodes)
        
        if total_nodes <= 1:
            return {node.id: 0.0 for node in nodes}
        
        centrality = {}
        for source_node in nodes:
            # 计算从该节点到所有其他节点的最短路径总和
            distances, _ = self._bfs_shortest_path(source_node.id, graph_type)
            
            # 计算总距离
            total_distance = sum(distances.values())
            
            # 接近中心性是总距离的倒数（归一化）
            if total_distance > 0:
                centrality[source_node.id] = (total_nodes - 1) / total_distance
            else:
                centrality[source_node.id] = 0.0
                
        return centrality
    
    def detect_communities(self, graph_type: GraphType) -> Dict[int, List[str]]:
        """
        基于标签和连接关系的社区发现
        
        Args:
            graph_type: 图类型
            
        Returns:
            社区分组 {community_id: [node_ids]}
        """
        nodes = self.graph_store.search_nodes(graph_type=graph_type)
        
        # 基于标签进行初步分组
        label_groups = defaultdict(list)
        for node in nodes:
            label_groups[node.label].append(node.id)
        
        # 基于连接关系进一步细分社区
        communities = {}
        community_id = 0
        
        for label, node_ids in label_groups.items():
            # 对于同一标签的节点，根据连接关系进一步分组
            sub_communities = self._split_by_connectivity(node_ids, graph_type)
            for sub_community in sub_communities:
                communities[community_id] = sub_community
                community_id += 1
                
        return communities
    
    def _split_by_connectivity(self, node_ids: List[str], graph_type: GraphType) -> List[List[str]]:
        """根据连接关系分割节点"""
        if len(node_ids) <= 1:
            return [node_ids]
        
        # 构建子图连接关系
        subgraph_edges = defaultdict(set)
        for node_id in node_ids:
            neighbors = self.graph_store.find_neighbors(node_id, graph_type)
            for neighbor in neighbors:
                if neighbor.id in node_ids:
                    subgraph_edges[node_id].add(neighbor.id)
        
        # 使用简单的连通分量算法分割
        visited = set()
        communities = []
        
        for node_id in node_ids:
            if node_id not in visited:
                # 发现新的连通分量
                community = []
                stack = [node_id]
                
                while stack:
                    current = stack.pop()
                    if current not in visited:
                        visited.add(current)
                        community.append(current)
                        # 添加所有未访问的邻居
                        for neighbor in subgraph_edges[current]:
                            if neighbor not in visited:
                                stack.append(neighbor)
                
                if community:
                    communities.append(community)
        
        return communities if communities else [node_ids]
    
    def get_graph_statistics(self, graph_type: GraphType) -> Dict[str, float]:
        """获取图统计信息"""
        nodes = self.graph_store.search_nodes(graph_type=graph_type)
        node_count = len(nodes)
        
        if node_count == 0:
            return {
                "nodes_count": 0,
                "edges_count": 0,
                "density": 0.0,
                "avg_degree": 0.0
            }
        
        # 计算边数量
        edge_count = 0
        total_degree = 0
        for node in nodes:
            neighbors = self.graph_store.find_neighbors(node.id, graph_type)
            edge_count += len(neighbors)
            total_degree += len(neighbors)
        
        # 无向图中每条边被计算两次
        edge_count = edge_count // 2
        total_degree = total_degree // 2
        
        # 计算密度
        max_possible_edges = node_count * (node_count - 1) // 2
        density = edge_count / max_possible_edges if max_possible_edges > 0 else 0.0
        
        return {
            "nodes_count": node_count,
            "edges_count": edge_count,
            "density": density,
            "avg_degree": total_degree / node_count if node_count > 0 else 0.0
        }