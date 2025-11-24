"""
增强图谱 Schema 测试
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from ame.foundation.graph.utils.models import GraphNode, GraphEdge, NodeLabel, RelationType, GraphType
from ame.foundation.graph.components.schema import LifeGraphSchema, WorkGraphSchema


def test_enhanced_schema():
    """测试增强的图谱 Schema"""
    print("=== 增强图谱 Schema 测试 ===")
    
    # 测试生活图谱 Schema
    print("\n--- 生活图谱 Schema 测试 ---")
    life_schema = LifeGraphSchema()
    
    # 测试新增的生活节点类型
    interest_node = GraphNode(
        id="interest_001",
        label=NodeLabel.INTEREST,
        properties={"name": "摄影", "level": "advanced"}
    )
    
    skill_node = GraphNode(
        id="skill_001",
        label=NodeLabel.SKILL,
        properties={"name": "Python编程", "proficiency": "expert"}
    )
    
    goal_node = GraphNode(
        id="goal_001",
        label=NodeLabel.GOAL,
        properties={"title": "学习机器学习", "deadline": "2024-12-31"}
    )
    
    try:
        life_schema.validate_node(interest_node)
        life_schema.validate_node(skill_node)
        life_schema.validate_node(goal_node)
        print("✓ 新增生活节点类型验证通过")
    except Exception as e:
        print(f"✗ 新增生活节点类型验证失败: {e}")
    
    # 测试新增的生活关系类型
    interest_edge = GraphEdge(
        source_id="person_001",
        target_id="interest_001",
        relation_type=RelationType.INTERESTED_IN
    )
    
    skill_edge = GraphEdge(
        source_id="person_001",
        target_id="skill_001",
        relation_type=RelationType.HAS_SKILL
    )
    
    try:
        life_schema.validate_edge(interest_edge)
        life_schema.validate_edge(skill_edge)
        print("✓ 新增生活关系类型验证通过")
    except Exception as e:
        print(f"✗ 新增生活关系类型验证失败: {e}")
    
    # 测试工作图谱 Schema
    print("\n--- 工作图谱 Schema 测试 ---")
    work_schema = WorkGraphSchema()
    
    # 测试新增的工作节点类型
    role_node = GraphNode(
        id="role_001",
        label=NodeLabel.ROLE,
        properties={"title": "软件工程师", "department": "技术部"}
    )
    
    org_node = GraphNode(
        id="org_001",
        label=NodeLabel.ORGANIZATION,
        properties={"name": "某某科技公司", "industry": "互联网"}
    )
    
    meeting_node = GraphNode(
        id="meeting_001",
        label=NodeLabel.MEETING,
        properties={"subject": "项目进度评审", "date": "2024-01-20"}
    )
    
    try:
        work_schema.validate_node(role_node)
        work_schema.validate_node(org_node)
        work_schema.validate_node(meeting_node)
        print("✓ 新增工作节点类型验证通过")
    except Exception as e:
        print(f"✗ 新增工作节点类型验证失败: {e}")
    
    # 测试新增的工作关系类型
    assigned_edge = GraphEdge(
        source_id="person_001",
        target_id="role_001",
        relation_type=RelationType.ASSIGNED_TO
    )
    
    attends_edge = GraphEdge(
        source_id="person_001",
        target_id="meeting_001",
        relation_type=RelationType.ATTENDS
    )
    
    try:
        work_schema.validate_edge(assigned_edge)
        work_schema.validate_edge(attends_edge)
        print("✓ 新增工作关系类型验证通过")
    except Exception as e:
        print(f"✗ 新增工作关系类型验证失败: {e}")
    
    # 打印所有允许的节点和关系类型
    print("\n--- 生活图谱允许的节点类型 ---")
    for node_label in life_schema.allowed_nodes:
        print(f"  • {node_label.value}")
    
    print("\n--- 生活图谱允许的关系类型 ---")
    for relation_type in life_schema.allowed_relations:
        print(f"  • {relation_type.value}")
    
    print("\n--- 工作图谱允许的节点类型 ---")
    for node_label in work_schema.allowed_nodes:
        print(f"  • {node_label.value}")
    
    print("\n--- 工作图谱允许的关系类型 ---")
    for relation_type in work_schema.allowed_relations:
        print(f"  • {relation_type.value}")
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_enhanced_schema()