"""
Storage Pipeline 测试

测试：
- LifeGraphPipeline 基础功能
- WorkGraphPipeline 基础功能
- 节点创建和查询
- 边创建和时间属性
- 批量操作
- Merge操作
- 时间相关查询

使用前请确保：
1. FalkorDB已启动
2. 传入正确的连接参数
"""

import sys
import asyncio
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent / "ame"
sys.path.insert(0, str(project_root))

from foundation.storage import (
    LifeGraphPipeline,
    WorkGraphPipeline,
    GraphNode,
    GraphEdge,
    NodeLabel,
    RelationType,
)


# ===== 配置区域 =====
# 用户需要根据实际情况修改这些参数
FALKORDB_HOST = "localhost"  # FalkorDB地址
FALKORDB_PORT = 6379         # FalkorDB端口
FALKORDB_PASSWORD = None     # FalkorDB密码（如果有）


async def test_life_pipeline_init():
    """测试生活图谱初始化"""
    print("\n测试生活图谱初始化...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    
    await pipeline.initialize()
    
    # 验证连接
    is_healthy = await pipeline.store.health_check()
    assert is_healthy, "FalkorDB连接失败"
    
    await pipeline.store.disconnect()
    
    print("✓ 生活图谱初始化成功")


async def test_work_pipeline_init():
    """测试工作图谱初始化"""
    print("\n测试工作图谱初始化...")
    
    pipeline = WorkGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    
    await pipeline.initialize()
    
    # 验证连接
    is_healthy = await pipeline.store.health_check()
    assert is_healthy, "FalkorDB连接失败"
    
    await pipeline.store.disconnect()
    
    print("✓ 工作图谱初始化成功")


async def test_create_person_node():
    """测试创建Person节点"""
    print("\n测试创建Person节点...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 创建节点
        node = GraphNode(
            label=NodeLabel.PERSON,
            properties={
                "name": "测试用户",
                "user_id": "test_user_001",
                "age": 25
            }
        )
        
        node_id = await pipeline.validate_and_create_node(node)
        assert node_id is not None, "节点创建失败"
        
        # 查询验证
        retrieved_node = await pipeline.store.get_node(node_id)
        assert retrieved_node is not None, "节点查询失败"
        assert retrieved_node.label == NodeLabel.PERSON
        assert retrieved_node.properties["name"] == "测试用户"
        
        print(f"✓ Person节点创建成功，ID={node_id}")
        
    finally:
        await pipeline.store.disconnect()


async def test_create_interest_with_relationship():
    """测试创建兴趣节点和关系"""
    print("\n测试创建兴趣节点和INTERESTED_IN关系...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 1. 创建Person节点
        person_node = GraphNode(
            label=NodeLabel.PERSON,
            properties={"name": "张三", "user_id": "user_zhang"}
        )
        person_id = await pipeline.validate_and_create_node(person_node)
        
        # 2. 创建Interest节点
        interest_node = GraphNode(
            label=NodeLabel.INTEREST,
            properties={"name": "Python编程"}
        )
        interest_id = await pipeline.validate_and_create_node(interest_node)
        
        # 3. 创建关系（包含时间属性）
        now = datetime.now()
        edge = GraphEdge(
            source_id=person_id,
            target_id=interest_id,
            relation=RelationType.INTERESTED_IN,
            properties={"confidence": 0.95},
            valid_from=now,
            valid_until=None  # 仍然感兴趣
        )
        
        edge_id = await pipeline.validate_and_create_edge(edge)
        assert edge_id is not None, "边创建失败"
        
        # 4. 验证关系
        edges = await pipeline.store.find_edges(
            source_id=person_id,
            relation=RelationType.INTERESTED_IN
        )
        assert len(edges) > 0, "关系查询失败"
        assert edges[0].relation == RelationType.INTERESTED_IN
        assert edges[0].is_currently_valid(), "关系应该有效"
        
        print(f"✓ 兴趣关系创建成功，边ID={edge_id}")
        
    finally:
        await pipeline.store.disconnect()


async def test_edge_time_marking():
    """测试边的时间标记（失效）"""
    print("\n测试边的时间标记功能...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 1. 创建节点和关系
        person_node = GraphNode(
            label=NodeLabel.PERSON,
            properties={"name": "李四", "user_id": "user_li"}
        )
        person_id = await pipeline.validate_and_create_node(person_node)
        
        interest_node = GraphNode(
            label=NodeLabel.INTEREST,
            properties={"name": "摄影"}
        )
        interest_id = await pipeline.validate_and_create_node(interest_node)
        
        edge = GraphEdge(
            source_id=person_id,
            target_id=interest_id,
            relation=RelationType.INTERESTED_IN,
            valid_from=datetime.now(),
            valid_until=None
        )
        edge_id = await pipeline.validate_and_create_edge(edge)
        
        # 2. 标记为失效（不再喜欢）
        success = await pipeline.mark_edge_as_invalid(edge_id)
        assert success, "标记失效失败"
        
        # 3. 验证失效
        updated_edge = await pipeline.store.get_edge(edge_id)
        assert updated_edge is not None, "边查询失败"
        assert not updated_edge.is_currently_valid(), "边应该已失效"
        assert updated_edge.valid_until is not None, "valid_until应该已设置"
        
        print("✓ 边时间标记功能正常")
        
    finally:
        await pipeline.store.disconnect()


async def test_active_relationships():
    """测试查询活跃关系"""
    print("\n测试查询活跃关系...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 1. 创建节点
        person_node = GraphNode(
            label=NodeLabel.PERSON,
            properties={"name": "王五", "user_id": "user_wang"}
        )
        person_id = await pipeline.validate_and_create_node(person_node)
        
        # 2. 创建多个兴趣关系
        interests = ["阅读", "跑步", "音乐"]
        now = datetime.now()
        
        for i, interest_name in enumerate(interests):
            interest_node = GraphNode(
                label=NodeLabel.INTEREST,
                properties={"name": interest_name}
            )
            interest_id = await pipeline.validate_and_create_node(interest_node)
            
            # 第一个兴趣设为已失效
            if i == 0:
                edge = GraphEdge(
                    source_id=person_id,
                    target_id=interest_id,
                    relation=RelationType.INTERESTED_IN,
                    valid_from=now - timedelta(days=30),
                    valid_until=now - timedelta(days=5)  # 5天前失效
                )
            else:
                edge = GraphEdge(
                    source_id=person_id,
                    target_id=interest_id,
                    relation=RelationType.INTERESTED_IN,
                    valid_from=now,
                    valid_until=None
                )
            
            await pipeline.validate_and_create_edge(edge)
        
        # 3. 查询当前活跃的兴趣
        active_edges = await pipeline.get_active_relationships(
            node_id=person_id,
            relation=RelationType.INTERESTED_IN
        )
        
        # 应该只有2个活跃兴趣（跑步、音乐）
        assert len(active_edges) == 2, f"应该有2个活跃兴趣，实际有{len(active_edges)}个"
        
        print(f"✓ 活跃关系查询正常，找到{len(active_edges)}个活跃兴趣")
        
    finally:
        await pipeline.store.disconnect()


async def test_batch_operations():
    """测试批量操作"""
    print("\n测试批量操作...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 批量创建节点
        nodes = [
            GraphNode(label=NodeLabel.PERSON, properties={"name": f"用户{i}"})
            for i in range(5)
        ]
        
        node_ids = await pipeline.batch_create_nodes(nodes)
        assert len(node_ids) == 5, "批量创建节点数量不对"
        
        print(f"✓ 批量创建{len(node_ids)}个节点成功")
        
    finally:
        await pipeline.store.disconnect()


async def test_merge_operation():
    """测试Merge操作（去重）"""
    print("\n测试Merge操作...")
    
    pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 1. 第一次创建
        node1 = GraphNode(
            label=NodeLabel.PERSON,
            properties={"name": "赵六", "user_id": "user_zhao"}
        )
        id1 = await pipeline.merge_or_create_node(node1, merge_keys=["name"])
        
        # 2. 第二次创建（相同name）
        node2 = GraphNode(
            label=NodeLabel.PERSON,
            properties={"name": "赵六", "user_id": "user_zhao", "age": 30}
        )
        id2 = await pipeline.merge_or_create_node(node2, merge_keys=["name"])
        
        # 应该返回同一个ID
        assert id1 == id2, "Merge应该返回相同的节点ID"
        
        # 验证属性已更新
        node = await pipeline.store.get_node(id2)
        assert node.properties.get("age") == 30, "属性应该已更新"
        
        print("✓ Merge操作正常")
        
    finally:
        await pipeline.store.disconnect()


async def test_work_pipeline_task_creation():
    """测试工作图谱-任务创建"""
    print("\n测试工作图谱-任务创建...")
    
    pipeline = WorkGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await pipeline.initialize()
    
    try:
        # 1. 创建项目节点
        project_node = GraphNode(
            label=NodeLabel.PROJECT,
            properties={"name": "测试项目", "status": "active"}
        )
        project_id = await pipeline.validate_and_create_node(project_node)
        
        # 2. 创建任务节点
        task_node = GraphNode(
            label=NodeLabel.TASK,
            properties={
                "title": "完成单元测试",
                "status": "pending",
                "priority": "high"
            }
        )
        task_id = await pipeline.validate_and_create_node(task_node)
        
        # 3. 创建BELONGS_TO关系
        edge = GraphEdge(
            source_id=task_id,
            target_id=project_id,
            relation=RelationType.BELONGS_TO,
            valid_from=datetime.now()
        )
        edge_id = await pipeline.validate_and_create_edge(edge)
        
        # 4. 验证
        edges = await pipeline.store.find_edges(
            source_id=task_id,
            relation=RelationType.BELONGS_TO
        )
        assert len(edges) > 0, "关系查询失败"
        
        print(f"✓ 工作图谱任务创建成功，任务ID={task_id}")
        
    finally:
        await pipeline.store.disconnect()


async def test_domain_isolation():
    """测试领域隔离（生活/工作）"""
    print("\n测试领域隔离...")
    
    life_pipeline = LifeGraphPipeline(
        host=FALKORDB_HOST,
        port=FALKORDB_PORT,
        password=FALKORDB_PASSWORD
    )
    await life_pipeline.initialize()
    
    try:
        # 尝试在生活图谱中创建工作节点（应该失败）
        task_node = GraphNode(
            label=NodeLabel.TASK,
            properties={"title": "测试任务", "status": "pending"}
        )
        
        try:
            await life_pipeline.validate_and_create_node(task_node)
            assert False, "应该抛出ValidationError"
        except Exception as e:
            assert "不属于生活领域" in str(e), "错误信息不正确"
            print("✓ 领域隔离验证通过（正确拒绝了工作节点）")
        
    finally:
        await life_pipeline.store.disconnect()


async def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("Storage Pipeline 测试")
    print("=" * 60)
    print(f"\nFalkorDB配置:")
    print(f"  Host: {FALKORDB_HOST}")
    print(f"  Port: {FALKORDB_PORT}")
    print(f"  Password: {'***' if FALKORDB_PASSWORD else 'None'}")
    print("=" * 60)
    
    try:
        # 连接测试
        await test_life_pipeline_init()
        await test_work_pipeline_init()
        
        # 基础CRUD测试
        await test_create_person_node()
        await test_create_interest_with_relationship()
        
        # 时间相关测试
        await test_edge_time_marking()
        await test_active_relationships()
        
        # 批量操作测试
        await test_batch_operations()
        await test_merge_operation()
        
        # 工作图谱测试
        await test_work_pipeline_task_creation()
        
        # 领域隔离测试
        await test_domain_isolation()
        
        print("\n" + "=" * 60)
        print("✅ 所有Pipeline测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("请确保FalkorDB已启动！")
    print("=" * 60)
    print("\n如需修改连接参数，请编辑文件顶部的配置区域：")
    print(f"  FALKORDB_HOST = '{FALKORDB_HOST}'")
    print(f"  FALKORDB_PORT = {FALKORDB_PORT}")
    print(f"  FALKORDB_PASSWORD = {FALKORDB_PASSWORD}")
    print("\n按Enter键继续...")
    input()
    
    # 运行异步测试
    asyncio.run(run_all_tests())


if __name__ == "__main__":
    main()
