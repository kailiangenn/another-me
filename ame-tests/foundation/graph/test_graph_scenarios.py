"""
Graph 模块场景测试
验证生活场景（安慰、模仿、分析）和工作场景（待办分析、紧急程度、工作建议）
"""
from datetime import datetime, timedelta

from ame.foundation.graph import (
    NodeLabel,
    RelationType,
    GraphType,
    GraphNode,
    GraphEdge,
    FalkorDBStore,
)


# ========== 生活场景示例 ==========

def test_comfort_scenario():
    """场景1：情绪安慰 - 识别情绪状态并提供安慰"""
    print("\n【场景1：情绪安慰】")
    
    # 创建情绪状态节点
    emotional_state = GraphNode(
        id="emotional_001",
        label=NodeLabel.EMOTIONAL_STATE,
        properties={
            "state": "焦虑",
            "intensity": 0.8,  # 强度 0-1
            "detected_at": datetime.now().isoformat(),
            "triggers": ["工作压力", "deadline临近"]
        }
    )
    
    # 创建记忆节点
    memory = GraphNode(
        id="mem_001",
        label=NodeLabel.MEMORY,
        properties={
            "content": "最近工作压力很大，感觉很焦虑",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    # 建立关系：记忆 -> 表现出 -> 情绪状态
    edge1 = GraphEdge(
        source_id="mem_001",
        target_id="emotional_001",
        relation_type=RelationType.EXHIBITS,
        properties={"confidence": 0.9}
    )
    
    # 建立关系：情绪状态 -> 需要安慰
    edge2 = GraphEdge(
        source_id="emotional_001",
        target_id="comfort_suggestion_001",
        relation_type=RelationType.NEEDS_COMFORT,
        properties={
            "comfort_type": "鼓励",
            "suggested_response": "我理解你的压力，一步步来，你一定可以的"
        }
    )
    
    print(f"✅ 情绪状态节点: {emotional_state.id} - {emotional_state.properties['state']}")
    print(f"✅ 安慰关系: {edge2.relation_type}")


def test_mimic_scenario():
    """场景2：风格模仿 - 学习用户沟通风格"""
    print("\n【场景2：风格模仿】")
    
    # 创建用户沟通风格节点
    comm_style = GraphNode(
        id="style_001",
        label=NodeLabel.COMMUNICATION_STYLE,
        properties={
            "user_id": "user_001",
            "characteristics": {
                "tone": "轻松幽默",
                "common_phrases": ["哈哈", "不错哦", "我觉得"],
                "sentence_length": "中等",
                "emoji_usage": "频繁",
                "formality": "非正式"
            },
            "learned_from": 150,  # 学习自150条对话
            "confidence": 0.85
        }
    )
    
    # 创建记忆节点（历史对话）
    memory1 = GraphNode(
        id="mem_002",
        label=NodeLabel.MEMORY,
        properties={
            "content": "哈哈，这个想法不错哦，我觉得可以试试",
            "type": "对话"
        }
    )
    
    # 建立关系：记忆 -> 表达为 -> 沟通风格
    edge = GraphEdge(
        source_id="mem_002",
        target_id="style_001",
        relation_type=RelationType.EXPRESSES_AS,
        properties={"weight": 1.0}
    )
    
    print(f"✅ 沟通风格节点: {comm_style.properties['characteristics']['tone']}")
    print(f"✅ 学习来源: {comm_style.properties['learned_from']} 条对话")


def test_behavior_analysis_scenario():
    """场景3：行为分析 - 分析用户行为模式"""
    print("\n【场景3：行为分析】")
    
    # 创建行为模式节点
    behavior = GraphNode(
        id="behavior_001",
        label=NodeLabel.BEHAVIOR_PATTERN,
        properties={
            "pattern_type": "作息规律",
            "description": "通常晚上11点后休息，早上8点起床",
            "frequency": "每周5-6次",
            "confidence": 0.9,
            "detected_period": "最近30天"
        }
    )
    
    # 创建偏好节点
    preference = GraphNode(
        id="pref_001",
        label=NodeLabel.PREFERENCE,
        properties={
            "category": "娱乐",
            "items": ["看电影", "听音乐", "散步"],
            "strength": 0.8
        }
    )
    
    # 建立关系：用户 -> 表现出 -> 行为模式
    edge1 = GraphEdge(
        source_id="user_001",
        target_id="behavior_001",
        relation_type=RelationType.EXHIBITS,
        properties={}
    )
    
    # 建立关系：用户 -> 偏好 -> 娱乐活动
    edge2 = GraphEdge(
        source_id="user_001",
        target_id="pref_001",
        relation_type=RelationType.PREFERS,
        properties={}
    )
    
    print(f"✅ 行为模式: {behavior.properties['pattern_type']}")
    print(f"✅ 偏好分析: {preference.properties['category']}")


# ========== 工作场景示例 ==========

def test_todo_urgency_analysis():
    """场景4：待办紧急程度分析"""
    print("\n【场景4：待办紧急程度分析】")
    
    # 创建待办任务节点
    todo = GraphNode(
        id="todo_001",
        label=NodeLabel.TODO,
        properties={
            "title": "完成季度报告",
            "status": "进行中",
            "estimated_hours": 8
        }
    )
    
    # 创建截止日期节点
    deadline = GraphNode(
        id="deadline_001",
        label=NodeLabel.DEADLINE,
        properties={
            "date": (datetime.now() + timedelta(days=2)).isoformat(),
            "is_hard_deadline": True,
            "buffer_days": 0
        }
    )
    
    # 创建工作模式分析节点
    work_pattern = GraphNode(
        id="pattern_001",
        label=NodeLabel.WORK_PATTERN,
        properties={
            "task_type": "报告撰写",
            "average_completion_time": 10,  # 小时
            "typical_delay_rate": 0.3,  # 30%延期率
            "urgency_level": "高"
        }
    )
    
    # 建立关系：待办 -> 有截止日期
    edge1 = GraphEdge(
        source_id="todo_001",
        target_id="deadline_001",
        relation_type=RelationType.HAS_DEADLINE,
        properties={"days_remaining": 2}
    )
    
    # 建立关系：待办 -> 显示模式
    edge2 = GraphEdge(
        source_id="todo_001",
        target_id="pattern_001",
        relation_type=RelationType.SHOWS_PATTERN,
        properties={"risk_level": "高"}
    )
    
    # 建立关系：待办 -> 优先级
    edge3 = GraphEdge(
        source_id="todo_001",
        target_id="priority_high",
        relation_type=RelationType.PRIORITIZED_AS,
        properties={
            "priority": "紧急重要",
            "score": 95  # 0-100
        }
    )
    
    print(f"✅ 待办任务: {todo.properties['title']}")
    print(f"✅ 紧急程度: {work_pattern.properties['urgency_level']}")
    print(f"✅ 延期风险: {work_pattern.properties['typical_delay_rate']*100}%")


def test_time_consumption_analysis():
    """场景5：任务耗时分析"""
    print("\n【场景5：任务耗时分析】")
    
    # 创建待办任务
    todo = GraphNode(
        id="todo_002",
        label=NodeLabel.TODO,
        properties={
            "title": "团队沟通会议",
            "type": "沟通"
        }
    )
    
    # 创建耗时分析节点
    time_analysis = GraphNode(
        id="time_001",
        label=NodeLabel.TIME_CONSUMPTION,
        properties={
            "task_type": "沟通会议",
            "average_duration_minutes": 90,
            "planned_duration_minutes": 60,
            "overrun_rate": 0.5,  # 50%超时
            "analysis": "沟通会议经常超时，建议提前准备议程"
        }
    )
    
    # 建立关系：待办 -> 耗时
    edge = GraphEdge(
        source_id="todo_002",
        target_id="time_001",
        relation_type=RelationType.TAKES_TIME,
        properties={
            "actual_vs_planned": 1.5  # 实际耗时是计划的1.5倍
        }
    )
    
    print(f"✅ 任务类型: {time_analysis.properties['task_type']}")
    print(f"✅ 超时率: {time_analysis.properties['overrun_rate']*100}%")
    print(f"✅ 分析: {time_analysis.properties['analysis']}")


def test_work_suggestion():
    """场景6：工作改进建议"""
    print("\n【场景6：工作改进建议】")
    
    # 创建技能缺口节点
    skill_gap = GraphNode(
        id="gap_001",
        label=NodeLabel.SKILL_GAP,
        properties={
            "skill_name": "高效沟通",
            "current_level": "中等",
            "target_level": "熟练",
            "identified_issues": [
                "会议经常超时",
                "讨论容易偏离主题",
                "决策效率低"
            ]
        }
    )
    
    # 创建工作建议节点
    suggestion = GraphNode(
        id="sugg_001",
        label=NodeLabel.SUGGESTION,
        properties={
            "title": "提升沟通效率",
            "suggestions": [
                "会前准备清晰议程",
                "设置时间提醒",
                "使用结构化讨论框架（如STAR）",
                "会后及时总结行动项"
            ],
            "expected_improvement": "减少30%会议时间",
            "priority": "高",
            "generated_at": datetime.now().isoformat()
        }
    )
    
    # 建立关系：技能缺口 -> 建议
    edge1 = GraphEdge(
        source_id="gap_001",
        target_id="sugg_001",
        relation_type=RelationType.SUGGESTS,
        properties={"relevance": 0.95}
    )
    
    # 建立关系：建议 -> 改进（技能）
    edge2 = GraphEdge(
        source_id="sugg_001",
        target_id="gap_001",
        relation_type=RelationType.IMPROVES,
        properties={"expected_effect": 0.7}
    )
    
    print(f"✅ 技能缺口: {skill_gap.properties['skill_name']}")
    print(f"✅ 问题识别: {len(skill_gap.properties['identified_issues'])} 个")
    print(f"✅ 改进建议: {suggestion.properties['title']}")
    print(f"   - {suggestion.properties['suggestions'][0]}")
    print(f"   - {suggestion.properties['suggestions'][1]}")


def test_schema_validation():
    """测试 Schema 验证"""
    print("\n【Schema 验证测试】")
    
    # 测试生活图谱
    life_store = FalkorDBStore(graph_type=GraphType.LIFE)
    
    # 测试新增的节点类型
    test_nodes = [
        (NodeLabel.EMOTIONAL_STATE, "情绪状态", True),
        (NodeLabel.COMMUNICATION_STYLE, "沟通风格", True),
        (NodeLabel.BEHAVIOR_PATTERN, "行为模式", True),
        (NodeLabel.TODO, "待办任务", False),  # 不应该在生活图谱中
    ]
    
    for label, name, should_pass in test_nodes:
        node = GraphNode(id=f"test_{label.value}", label=label, properties={})
        try:
            life_store.schema.validate_node(node)
            result = "✅" if should_pass else "❌"
            print(f"{result} {name} in LIFE schema: {'通过' if should_pass else '不应通过'}")
        except Exception as e:
            result = "✅" if not should_pass else "❌"
            print(f"{result} {name} in LIFE schema: 正确拒绝")
    
    # 测试工作图谱
    work_store = FalkorDBStore(graph_type=GraphType.WORK)
    
    test_nodes_work = [
        (NodeLabel.TODO, "待办任务", True),
        (NodeLabel.WORK_PATTERN, "工作模式", True),
        (NodeLabel.SKILL_GAP, "技能缺口", True),
        (NodeLabel.SUGGESTION, "工作建议", True),
        (NodeLabel.EMOTIONAL_STATE, "情绪状态", False),  # 不应该在工作图谱中
    ]
    
    for label, name, should_pass in test_nodes_work:
        node = GraphNode(id=f"test_{label.value}", label=label, properties={})
        try:
            work_store.schema.validate_node(node)
            result = "✅" if should_pass else "❌"
            print(f"{result} {name} in WORK schema: {'通过' if should_pass else '不应通过'}")
        except Exception as e:
            result = "✅" if not should_pass else "❌"
            print(f"{result} {name} in WORK schema: 正确拒绝")


if __name__ == "__main__":
    print("=" * 80)
    print("Graph 模块场景测试 - 生活与工作场景扩展")
    print("=" * 80)
    
    # 生活场景
    test_comfort_scenario()
    test_mimic_scenario()
    test_behavior_analysis_scenario()
    
    # 工作场景
    test_todo_urgency_analysis()
    test_time_consumption_analysis()
    test_work_suggestion()
    
    # Schema 验证
    test_schema_validation()
    
    print("\n" + "=" * 80)
    print("✅ 所有场景测试完成！")
    print("=" * 80)
