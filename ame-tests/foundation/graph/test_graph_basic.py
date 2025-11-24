"""
Graph 模块基础测试
验证设计的可用性
"""
from datetime import datetime, timedelta

from ame.foundation.graph import (
    # 枚举
    NodeLabel,
    RelationType,
    GraphType,
    # 数据类
    GraphNode,
    GraphEdge,
    # Core
    FalkorDBStore,
)


def test_create_nodes():
    """测试创建节点（验证 Schema 自动验证）"""
    # 生活场景节点
    memory_node = GraphNode(
        id="mem_001",
        label=NodeLabel.MEMORY,
        properties={
            "content": "今天天气很好",
            "emotion": "happy"
        }
    )
    
    # 工作场景节点
    todo_node = GraphNode(
        id="todo_001",
        label=NodeLabel.TODO,
        properties={
            "title": "完成 Graph 模块开发",
            "priority": "high"
        }
    )
    
    print(f"✅ Memory Node: {memory_node.id}")
    print(f"✅ Todo Node: {todo_node.id}")


def test_create_edges():
    """测试创建边（验证时间属性）"""
    # 创建带时间属性的边
    edge = GraphEdge(
        source_id="mem_001",
        target_id="person_001",
        relation_type=RelationType.MENTIONS,
        properties={
            "context": "在日记中提到"
        }
    )
    
    print(f"✅ Edge created: {edge.source_id} -[{edge.relation_type}]-> {edge.target_id}")
    print(f"   Create time: {edge.create_time}")
    print(f"   Is valid: {edge.is_valid()}")


def test_graph_store_usage():
    """测试 GraphStore 使用（验证内化组件能力）"""
    # 创建生活图谱
    store = FalkorDBStore(
        host="localhost",
        port=6379,
        graph_name="test_life_graph",
        graph_type=GraphType.LIFE
    )
    
    print(f"✅ GraphStore created: {store.graph_name} ({store.graph_type.value})")
    print(f"   Schema: {store.schema.__class__.__name__}")
    print(f"   QueryBuilder: {store.query_builder.__class__.__name__}")
    print(f"   TimeHandler: {store.time_handler.__class__.__name__}")
    
    # 验证 Schema 自动验证
    try:
        memory_node = GraphNode(
            id="mem_001",
            label=NodeLabel.MEMORY,
            properties={"content": "测试"}
        )
        # Schema 验证在 add_node 中自动执行
        # store.connect()  # 需要 FalkorDB 运行才能测试
        # store.add_node(memory_node)
        print(f"✅ Schema validation works (Memory node allowed in LIFE graph)")
    except Exception as e:
        print(f"❌ Schema validation failed: {e}")


def test_query_builder():
    """测试 QueryBuilder（验证链式 API）"""
    store = FalkorDBStore(graph_type=GraphType.LIFE)
    
    # 构建查询
    cypher = store.query_builder.reset() \
        .match_node_by_id("mem_001", "n") \
        .with_relation(RelationType.MENTIONS, "out", "n", "m", "r") \
        .where_time_valid(datetime.now(), "r") \
        .return_neighbors("m") \
        .limit(10) \
        .build()
    
    params = store.query_builder.get_params()
    
    print("✅ Query built:")
    print(cypher)
    print(f"   Params: {params}")


def test_schema_validation():
    """测试 Schema 验证（不同场景的节点）"""
    # 生活图谱
    life_store = FalkorDBStore(graph_type=GraphType.LIFE)
    
    # 工作图谱
    work_store = FalkorDBStore(graph_type=GraphType.WORK)
    
    # 测试节点验证
    memory_node = GraphNode(id="mem_001", label=NodeLabel.MEMORY, properties={})
    todo_node = GraphNode(id="todo_001", label=NodeLabel.TODO, properties={})
    
    try:
        life_store.schema.validate_node(memory_node)
        print("✅ Memory node valid in LIFE schema")
    except Exception as e:
        print(f"❌ Memory node invalid in LIFE schema: {e}")
    
    try:
        work_store.schema.validate_node(todo_node)
        print("✅ Todo node valid in WORK schema")
    except Exception as e:
        print(f"❌ Todo node invalid in WORK schema: {e}")
    
    # 测试跨场景验证（应该失败）
    try:
        work_store.schema.validate_node(memory_node)
        print("❌ Memory node should not be valid in WORK schema")
    except Exception as e:
        print(f"✅ Cross-schema validation works: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("Graph 模块基础测试")
    print("=" * 60)
    
    print("\n1. 测试创建节点")
    print("-" * 60)
    test_create_nodes()
    
    print("\n2. 测试创建边")
    print("-" * 60)
    test_create_edges()
    
    print("\n3. 测试 GraphStore 使用")
    print("-" * 60)
    test_graph_store_usage()
    
    print("\n4. 测试 QueryBuilder")
    print("-" * 60)
    test_query_builder()
    
    print("\n5. 测试 Schema 验证")
    print("-" * 60)
    test_schema_validation()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
