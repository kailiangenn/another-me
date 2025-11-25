"""
高级图谱操作测试
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ame.foundation.graph.utils.models import GraphNode, GraphEdge, NodeLabel, RelationType, GraphType
from ame.foundation.graph.core.falkordb_store import FalkorDBStore


def test_advanced_operations():
    """测试高级图谱操作"""
    print("=== 高级图谱操作测试 ===")
    
    # 创建图谱存储实例
    store = FalkorDBStore(
        host="localhost",
        port=6379,
        base_name="test_another_me"
    )
    
    try:
        # 连接数据库（会自动初始化两张表）
        store.connect()
        print("✓ 连接成功，双表初始化完成")
        
        # ========== 生活图谱测试 ==========
        print("\n--- 生活图谱测试 ---")
        
        # 添加多个兴趣节点
        interest_nodes = [
            GraphNode(
                id="interest_001",
                label=NodeLabel.INTEREST,
                properties={
                    "name": "摄影",
                    "level": "advanced",
                    "years_of_experience": 3
                }
            ),
            GraphNode(
                id="interest_002",
                label=NodeLabel.INTEREST,
                properties={
                    "name": "编程",
                    "level": "expert",
                    "years_of_experience": 5
                }
            ),
            GraphNode(
                id="interest_003",
                label=NodeLabel.INTEREST,
                properties={
                    "name": "烹饪",
                    "level": "beginner",
                    "years_of_experience": 1
                }
            )
        ]
        
        for node in interest_nodes:
            store.add_node(node, graph_type=GraphType.LIFE)
        print("✓ 添加多个兴趣节点成功")
        
        # 通过属性查询节点
        advanced_interests = store.get_nodes_by_properties(
            {"level": "advanced"}, 
            label=NodeLabel.INTEREST,
            graph_type=GraphType.LIFE
        )
        print(f"✓ 查询到 {len(advanced_interests)} 个高级兴趣节点")
        
        # 高级搜索节点
        search_results = store.search_nodes(
            graph_type=GraphType.LIFE,
            label=NodeLabel.INTEREST,
            properties={"level": "advanced"},
            limit=10,
            order_by="name",
            order_direction="ASC"
        )
        print(f"✓ 搜索到 {len(search_results)} 个符合条件的兴趣节点")
        
        # 统计节点数量
        total_interests = store.count_nodes(
            graph_type=GraphType.LIFE,
            label=NodeLabel.INTEREST
        )
        print(f"✓ 生活图谱中共有 {total_interests} 个兴趣节点")
        
        # 添加人物节点和关系
        person_node = GraphNode(
            id="person_001",
            label=NodeLabel.PERSON,
            properties={
                "name": "张三",
                "age": 30
            }
        )
        store.add_node(person_node, graph_type=GraphType.LIFE)
        print("✓ 添加人物节点成功")
        
        # 添加关系
        interest_edges = [
            GraphEdge(
                source_id="person_001",
                target_id="interest_001",
                relation_type=RelationType.INTERESTED_IN,
                properties={"since": "2020-01-01"},
                create_time=datetime(2020, 1, 1)
            ),
            GraphEdge(
                source_id="person_001",
                target_id="interest_002",
                relation_type=RelationType.INTERESTED_IN,
                properties={"since": "2019-01-01"},
                create_time=datetime(2019, 1, 1)
            )
        ]
        
        for edge in interest_edges:
            store.add_edge(edge, graph_type=GraphType.LIFE)
        print("✓ 添加兴趣关系成功")
        
        # 查找邻居节点
        neighbors = store.find_neighbors(
            node_id="person_001",
            graph_type=GraphType.LIFE,
            relation_type=RelationType.INTERESTED_IN,
            direction="out"
        )
        print(f"✓ 查找到 {len(neighbors)} 个兴趣邻居节点")
        
        # 查找路径
        path_edges = store.find_path(
            start_node_id="person_001",
            end_node_id="interest_001",
            graph_type=GraphType.LIFE,
            max_depth=3
        )
        print(f"✓ 查找到 {len(path_edges)} 条路径边")
        
        # 使边失效
        store.invalidate_edge(
            source_id="person_001",
            target_id="interest_001",
            relation_type=RelationType.INTERESTED_IN,
            graph_type=GraphType.LIFE,
            invalid_time=datetime(2023, 1, 1)
        )
        print("✓ 使边失效成功")
        
        # 删除节点（通过属性）
        deleted_count = store.delete_nodes_by_properties(
            {"level": "beginner"}, 
            label=NodeLabel.INTEREST,
            graph_type=GraphType.LIFE
        )
        print(f"✓ 删除了 {deleted_count} 个初级兴趣节点")
        
        # ========== 工作图谱测试 ==========
        print("\n--- 工作图谱测试 ---")
        
        # 添加工作节点
        work_nodes = [
            GraphNode(
                id="role_001",
                label=NodeLabel.ROLE,
                properties={
                    "title": "软件工程师",
                    "department": "技术部"
                }
            ),
            GraphNode(
                id="project_001",
                label=NodeLabel.PROJECT,
                properties={
                    "name": "AI助手项目",
                    "status": "进行中"
                }
            )
        ]
        
        for node in work_nodes:
            store.add_node(node, graph_type=GraphType.WORK)
        print("✓ 添加工作节点成功")
        
        # 添加工作关系
        work_edge = GraphEdge(
            source_id="role_001",
            target_id="project_001",
            relation_type=RelationType.WORKS_ON,
            properties={"assigned_date": "2023-01-01"}
        )
        store.add_edge(work_edge, graph_type=GraphType.WORK)
        print("✓ 添加工作关系成功")
        
        # 统计工作节点数量
        total_roles = store.count_nodes(
            graph_type=GraphType.WORK,
            label=NodeLabel.ROLE
        )
        print(f"✓ 工作图谱中共有 {total_roles} 个角色节点")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 断开连接
        store.disconnect()


if __name__ == "__main__":
    test_advanced_operations()