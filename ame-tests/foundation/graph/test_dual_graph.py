"""
双图谱架构测试
"""
import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ame.foundation.graph.utils.models import GraphNode, GraphEdge, NodeLabel, RelationType, GraphType
from ame.foundation.graph.core.falkordb_store import FalkorDBStore


def test_dual_graph():
    """测试双图谱架构"""
    print("=== 双图谱架构测试 ===")
    
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
        
        # 添加生活节点
        memory_node = GraphNode(
            id="mem_001",
            label=NodeLabel.MEMORY,
            properties={
                "content": "今天和朋友去咖啡厅聊天",
                "timestamp": "2024-01-20T15:30:00"
            }
        )
        person_node = GraphNode(
            id="person_001",
            label=NodeLabel.PERSON,
            properties={
                "name": "张三",
                "relationship": "friend"
            }
        )
        
        store.add_node(memory_node, graph_type=GraphType.LIFE)
        store.add_node(person_node, graph_type=GraphType.LIFE)
        print("✓ 添加生活节点成功")
        
        # 添加生活边（带时间属性）
        edge = GraphEdge(
            source_id="mem_001",
            target_id="person_001",
            relation_type=RelationType.MENTIONS,
            properties={"context": "在咖啡厅提到了朋友"},
            create_time=datetime(2024, 1, 20, 15, 30),
            invalid_time=None
        )
        store.add_edge(edge, graph_type=GraphType.LIFE)
        print("✓ 添加生活边成功")
        
        # 查询生活节点
        retrieved_memory = store.get_node("mem_001", graph_type=GraphType.LIFE)
        print(f"✓ 查询生活节点: {retrieved_memory.properties['content']}")
        
        # ========== 工作图谱测试 ==========
        print("\n--- 工作图谱测试 ---")
        
        # 添加工作节点
        todo_node = GraphNode(
            id="todo_001",
            label=NodeLabel.TODO,
            properties={
                "title": "完成图谱模块设计",
                "status": "in_progress",
                "priority": "high"
            }
        )
        project_node = GraphNode(
            id="proj_001",
            label=NodeLabel.PROJECT,
            properties={
                "name": "AnotherMe 项目",
                "description": "个人AI助手项目"
            }
        )
        
        store.add_node(todo_node, graph_type=GraphType.WORK)
        store.add_node(project_node, graph_type=GraphType.WORK)
        print("✓ 添加工作节点成功")
        
        # 添加工作边
        work_edge = GraphEdge(
            source_id="todo_001",
            target_id="proj_001",
            relation_type=RelationType.BELONGS_TO,
            properties={"assigned_date": "2024-01-20"}
        )
        store.add_edge(work_edge, graph_type=GraphType.WORK)
        print("✓ 添加工作边成功")
        
        # 查询工作节点
        retrieved_todo = store.get_node("todo_001", graph_type=GraphType.WORK)
        print(f"✓ 查询工作节点: {retrieved_todo.properties['title']}")
        
        # ========== 跨图谱隔离测试 ==========
        print("\n--- 跨图谱隔离测试 ---")
        
        # 尝试在生活图谱中查找工作节点（应该找不到）
        work_node_in_life = store.get_node("todo_001", graph_type=GraphType.LIFE)
        if work_node_in_life is None:
            print("✓ 图谱隔离正常：在生活图谱中找不到工作节点")
        else:
            print("✗ 图谱隔离异常：在生活图谱中找到了工作节点")
            
        # 尝试在工作图谱中查找生活节点（应该找不到）
        life_node_in_work = store.get_node("mem_001", graph_type=GraphType.WORK)
        if life_node_in_work is None:
            print("✓ 图谱隔离正常：在工作图谱中找不到生活节点")
        else:
            print("✗ 图谱隔离异常：在工作图谱中找到了生活节点")
            
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 断开连接
        store.disconnect()


if __name__ == "__main__":
    test_dual_graph()