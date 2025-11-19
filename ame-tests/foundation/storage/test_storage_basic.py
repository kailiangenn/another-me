"""
Storage模块基础测试

测试：
- 数据模型创建
- Schema验证
- 验证器功能
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ame.foundation.storage.core.models import GraphNode, GraphEdge
from ame.foundation.storage.core.schema import NodeLabel, RelationType, GraphSchema
from ame.foundation.storage.core.validators import GraphDataValidator


def test_node_creation():
    """测试节点创建"""
    print("测试节点创建...")
    
    # 创建Person节点
    node = GraphNode(
        label=NodeLabel.PERSON,
        properties={"name": "张三", "age": 25}
    )
    
    assert node.label == NodeLabel.PERSON
    assert node.properties["name"] == "张三"
    assert node.created_at is not None
    
    print("✓ 节点创建成功")


def test_edge_creation():
    """测试边创建（包含时间属性）"""
    print("测试边创建...")
    
    # 创建INTERESTED_IN边
    edge = GraphEdge(
        source_id="1",
        target_id="2",
        relation=RelationType.INTERESTED_IN,
        properties={"confidence": 0.9},
        valid_from=datetime.now(),
        valid_until=None  # 仍然有效
    )
    
    assert edge.relation == RelationType.INTERESTED_IN
    assert edge.is_currently_valid()
    assert edge.duration() is None  # 仍在进行
    
    print("✓ 边创建成功")


def test_edge_time_validity():
    """测试边的时间有效性判断"""
    print("测试边的时间有效性...")
    
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    
    # 创建已失效的边
    edge = GraphEdge(
        source_id="1",
        target_id="2",
        relation=RelationType.WORKS_ON,
        valid_from=yesterday - timedelta(days=5),
        valid_until=yesterday  # 昨天失效
    )
    
    # 验证
    assert edge.is_valid_at(yesterday - timedelta(days=2))  # 5天前有效
    assert not edge.is_currently_valid()  # 现在无效
    print(edge.duration())
    assert edge.duration() == timedelta(days=5)  # 持续4天
    
    print("✓ 时间有效性判断正确")


def test_schema_validation():
    """测试Schema验证"""
    print("测试Schema验证...")
    
    # 正确的Person节点
    valid, error = GraphSchema.validate_node(
        NodeLabel.PERSON,
        {"name": "李四"}
    )
    assert valid, f"验证失败: {error}"
    
    # 缺少必需属性的Person节点
    valid, error = GraphSchema.validate_node(
        NodeLabel.PERSON,
        {"age": 30}  # 缺少name
    )
    assert not valid
    assert "name" in error
    
    print("✓ Schema验证正确")


def test_validator():
    """测试验证器"""
    print("测试验证器...")
    
    validator = GraphDataValidator()
    
    # 正确的节点
    node = GraphNode(
        label=NodeLabel.TASK,
        properties={"title": "完成测试", "status": "pending"}
    )
    assert validator.validate_node(node)
    
    # 错误的节点（缺少必需属性）
    node = GraphNode(
        label=NodeLabel.TASK,
        properties={"title": "完成测试"}  # 缺少status
    )
    assert not validator.validate_node(node)
    
    # 正确的边
    edge = GraphEdge(
        source_id="1",
        target_id="2",
        relation=RelationType.DEPENDS_ON
    )
    assert validator.validate_edge(edge)
    
    # 错误的边（valid_until早于valid_from）
    edge = GraphEdge(
        source_id="1",
        target_id="2",
        relation=RelationType.DEPENDS_ON,
        valid_from=datetime.now(),
        valid_until=datetime.now() - timedelta(days=1)
    )
    assert not validator.validate_edge(edge)
    
    print("✓ 验证器工作正常")


def test_schema_life_work_labels():
    """测试生活/工作领域标签分类"""
    print("测试领域标签分类...")
    
    life_labels = GraphSchema.get_life_labels()
    work_labels = GraphSchema.get_work_labels()
    
    # 验证分类
    assert NodeLabel.PERSON in life_labels
    assert NodeLabel.INTEREST in life_labels
    assert NodeLabel.TASK in work_labels
    assert NodeLabel.PROJECT in work_labels
    
    # 确保没有重叠
    assert not set(life_labels).intersection(set(work_labels))
    
    print("✓ 领域标签分类正确")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("Storage 模块基础测试")
    print("=" * 50)
    
    try:
        test_node_creation()
        test_edge_creation()
        test_edge_time_validity()
        test_schema_validation()
        test_validator()
        test_schema_life_work_labels()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
