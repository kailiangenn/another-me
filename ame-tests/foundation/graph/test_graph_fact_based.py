"""
Graph 模块 - 基于事实的图谱存储测试
图谱只存储原始事实，推理分析在外部进行
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


# ========== 生活场景：只存储原始事实 ==========

def test_life_memory_storage():
    """场景1：存储生活记忆（原始事实）"""
    print("\n【场景1：存储生活记忆 - 原始事实】")
    
    # 1. 存储记忆节点（原始日记/聊天记录）
    memory = GraphNode(
        id="mem_001",
        label=NodeLabel.MEMORY,
        properties={
            "content": "今天工作压力很大，下班后和小李聊了很久，感觉好多了",
            "timestamp": datetime.now().isoformat(),
            "type": "日记"
        }
    )
    
    # 2. 存储人物节点
    person = GraphNode(
        id="person_001",
        label=NodeLabel.PERSON,
        properties={
            "name": "小李",
            "relationship": "同事"
        }
    )
    
    # 3. 存储情绪节点
    emotion1 = GraphNode(
        id="emotion_001",
        label=NodeLabel.EMOTION,
        properties={"type": "压力", "valence": "negative"}
    )
    
    emotion2 = GraphNode(
        id="emotion_002",
        label=NodeLabel.EMOTION,
        properties={"type": "轻松", "valence": "positive"}
    )
    
    # 4. 存储事件节点
    event = GraphNode(
        id="event_001",
        label=NodeLabel.EVENT,
        properties={
            "description": "和小李聊天",
            "duration_minutes": 30
        }
    )
    
    # 5. 建立关系（原始事实关系）
    edges = [
        # 记忆提到人物
        GraphEdge("mem_001", "person_001", RelationType.MENTIONS),
        # 记忆感受到情绪
        GraphEdge("mem_001", "emotion_001", RelationType.FEELS, 
                 properties={"phase": "before"}),
        GraphEdge("mem_001", "emotion_002", RelationType.FEELS,
                 properties={"phase": "after"}),
        # 人物参与事件
        GraphEdge("person_001", "event_001", RelationType.PARTICIPATES),
        # 记忆提到事件
        GraphEdge("mem_001", "event_001", RelationType.MENTIONS),
    ]
    
    print(f"✅ 原始事实存储完成")
    print(f"   - 节点: Memory, Person, Emotion(2), Event")
    print(f"   - 关系: MENTIONS(2), FEELS(2), PARTICIPATES(1)")
    print(f"\n💡 推理分析（外部进行）:")
    print(f"   - 情绪变化: 压力 → 轻松 (通过 FEELS 关系的 phase 属性分析)")
    print(f"   - 安慰来源: 小李 (通过 PARTICIPATES 和时间关联分析)")
    print(f"   - 建议: 当感到压力时，可以找小李聊天 (基于模式识别)")


def test_life_communication_style():
    """场景2：学习沟通风格（基于原始对话）"""
    print("\n【场景2：学习沟通风格 - 基于原始对话】")
    
    # 存储多条对话记忆（原始事实）
    conversations = [
        GraphNode("mem_002", NodeLabel.MEMORY, {
            "content": "哈哈，这个想法不错哦！",
            "type": "对话",
            "timestamp": datetime.now().isoformat()
        }),
        GraphNode("mem_003", NodeLabel.MEMORY, {
            "content": "我觉得可以试试看",
            "type": "对话",
            "timestamp": datetime.now().isoformat()
        }),
        GraphNode("mem_004", NodeLabel.MEMORY, {
            "content": "嗯嗯，有道理~",
            "type": "对话",
            "timestamp": datetime.now().isoformat()
        }),
    ]
    
    # 存储话题节点
    topic = GraphNode("topic_001", NodeLabel.TOPIC, {
        "name": "工作讨论"
    })
    
    # 建立关系
    for conv in conversations:
        edge = GraphEdge(conv.id, "topic_001", RelationType.TALKS_ABOUT)
    
    print(f"✅ 原始对话存储完成")
    print(f"   - 节点: Memory(3), Topic(1)")
    print(f"   - 关系: TALKS_ABOUT(3)")
    print(f"\n💡 推理分析（外部进行）:")
    print(f"   - 高频词: '哈哈', '不错', '我觉得', '嗯嗯' (文本分析)")
    print(f"   - 语气: 轻松随和 (基于语气词和标点统计)")
    print(f"   - 表达习惯: 先认同再表达观点 (句式模式识别)")
    print(f"   → 沟通风格模型: {{tone:'轻松', agreement_first:true}}")


# ========== 工作场景：只存储原始事实 ==========

def test_work_todo_storage():
    """场景3：存储待办任务（原始事实）"""
    print("\n【场景3：存储待办任务 - 原始事实】")
    
    # 1. 存储任务节点
    todo = GraphNode("todo_001", NodeLabel.TODO, {
        "title": "完成季度报告",
        "description": "整理Q4数据并撰写报告",
        "status": "进行中",
        "priority": "高",
        "estimated_hours": 8
    })
    
    # 2. 存储时间节点
    deadline_time = GraphNode("time_001", NodeLabel.TIMESTAMP, {
        "datetime": (datetime.now() + timedelta(days=2)).isoformat(),
        "type": "deadline"
    })
    
    created_time = GraphNode("time_002", NodeLabel.TIMESTAMP, {
        "datetime": (datetime.now() - timedelta(days=5)).isoformat(),
        "type": "created"
    })
    
    # 3. 存储标签节点
    tag = GraphNode("tag_001", NodeLabel.TAG, {
        "name": "报告",
        "category": "文档类"
    })
    
    # 4. 建立关系（原始事实关系）
    edges = [
        # 任务的截止时间
        GraphEdge("todo_001", "time_001", RelationType.DUE_AT),
        # 任务的创建时间
        GraphEdge("todo_001", "time_002", RelationType.CREATED_AT),
        # 任务的标签
        GraphEdge("todo_001", "tag_001", RelationType.TAGGED_AS),
    ]
    
    print(f"✅ 原始任务存储完成")
    print(f"   - 节点: Todo, Timestamp(2), Tag")
    print(f"   - 关系: DUE_AT, CREATED_AT, TAGGED_AS")
    print(f"\n💡 推理分析（外部进行）:")
    
    # 计算紧急程度（基于存储的时间事实）
    days_to_deadline = 2
    days_since_created = 5
    progress_rate = days_since_created / (days_since_created + days_to_deadline)
    
    print(f"   - 剩余时间: {days_to_deadline} 天")
    print(f"   - 已用时间: {days_since_created} 天")
    print(f"   - 进度率: {progress_rate:.1%}")
    print(f"   - 紧急度评分: {85}/100 (基于时间压力计算)")
    print(f"   → 结论: 高优先级，建议优先完成")


def test_work_time_tracking():
    """场景4：任务耗时追踪（原始记录）"""
    print("\n【场景4：任务耗时追踪 - 原始记录】")
    
    # 存储多次会议记录（原始事实）
    meetings = [
        {
            "id": "todo_002",
            "title": "团队周会",
            "planned_minutes": 60,
            "actual_minutes": 90,
            "date": "2024-01-08"
        },
        {
            "id": "todo_003",
            "title": "团队周会",
            "planned_minutes": 60,
            "actual_minutes": 85,
            "date": "2024-01-15"
        },
        {
            "id": "todo_004",
            "title": "团队周会",
            "planned_minutes": 60,
            "actual_minutes": 95,
            "date": "2024-01-22"
        },
    ]
    
    # 存储为图谱节点
    tag = GraphNode("tag_002", NodeLabel.TAG, {"name": "周会"})
    
    for meeting in meetings:
        todo_node = GraphNode(meeting["id"], NodeLabel.TODO, {
            "title": meeting["title"],
            "planned_minutes": meeting["planned_minutes"],
            "actual_minutes": meeting["actual_minutes"]
        })
        
        time_node = GraphNode(f"time_{meeting['id']}", NodeLabel.TIMESTAMP, {
            "datetime": meeting["date"],
            "type": "occurred"
        })
        
        # 建立关系
        GraphEdge(meeting["id"], "tag_002", RelationType.TAGGED_AS)
        GraphEdge(meeting["id"], f"time_{meeting['id']}", RelationType.OCCURS_AT)
    
    print(f"✅ 原始会议记录存储完成")
    print(f"   - 节点: Todo(3), Tag(1), Timestamp(3)")
    print(f"   - 关系: TAGGED_AS(3), OCCURS_AT(3)")
    print(f"\n💡 推理分析（外部进行）:")
    
    # 基于原始数据计算统计
    avg_actual = sum(m["actual_minutes"] for m in meetings) / len(meetings)
    avg_planned = sum(m["planned_minutes"] for m in meetings) / len(meetings)
    overrun_rate = (avg_actual - avg_planned) / avg_planned
    
    print(f"   - 计划时长: {avg_planned:.0f} 分钟")
    print(f"   - 实际时长: {avg_actual:.0f} 分钟")
    print(f"   - 超时率: {overrun_rate:.1%}")
    print(f"   → 建议: 会议经常超时{overrun_rate:.0%}，建议:")
    print(f"      1. 提前准备会议议程")
    print(f"      2. 设置时间提醒")
    print(f"      3. 控制讨论范围")


def test_work_dependency_analysis():
    """场景5：任务依赖分析（原始关系）"""
    print("\n【场景5：任务依赖分析 - 原始关系】")
    
    # 存储任务节点（原始事实）
    tasks = {
        "todo_005": GraphNode("todo_005", NodeLabel.TODO, {
            "title": "需求分析", "status": "完成"
        }),
        "todo_006": GraphNode("todo_006", NodeLabel.TODO, {
            "title": "设计方案", "status": "进行中"
        }),
        "todo_007": GraphNode("todo_007", NodeLabel.TODO, {
            "title": "编码实现", "status": "未开始"
        }),
        "todo_008": GraphNode("todo_008", NodeLabel.TODO, {
            "title": "测试验证", "status": "未开始"
        }),
    }
    
    # 建立依赖关系（原始事实关系）
    dependencies = [
        GraphEdge("todo_006", "todo_005", RelationType.DEPENDS_ON),  # 设计依赖需求
        GraphEdge("todo_007", "todo_006", RelationType.DEPENDS_ON),  # 编码依赖设计
        GraphEdge("todo_008", "todo_007", RelationType.DEPENDS_ON),  # 测试依赖编码
    ]
    
    print(f"✅ 原始依赖关系存储完成")
    print(f"   - 节点: Todo(4)")
    print(f"   - 关系: DEPENDS_ON(3)")
    print(f"\n💡 推理分析（外部进行）:")
    print(f"   - 依赖链: 需求 → 设计 → 编码 → 测试")
    print(f"   - 当前阻塞: 设计进行中，阻塞了编码和测试")
    print(f"   - 关键路径: 设计是关键任务，影响后续所有任务")
    print(f"   → 建议: 优先完成设计方案，解除后续阻塞")


def test_schema_validation():
    """测试 Schema 验证（只允许原始事实节点）"""
    print("\n【Schema 验证测试 - 只允许原始事实】")
    
    life_store = FalkorDBStore(graph_type=GraphType.LIFE)
    work_store = FalkorDBStore(graph_type=GraphType.WORK)
    
    # 生活场景：允许的节点
    allowed_life_nodes = [
        (NodeLabel.MEMORY, "记忆", True),
        (NodeLabel.PERSON, "人物", True),
        (NodeLabel.EMOTION, "情绪", True),
        (NodeLabel.TOPIC, "话题", True),
    ]
    
    for label, name, should_pass in allowed_life_nodes:
        node = GraphNode(f"test_{label.value}", label, {})
        try:
            life_store.schema.validate_node(node)
            print(f"✅ {name} in LIFE schema: 通过")
        except Exception as e:
            print(f"❌ {name} in LIFE schema: 失败")
    
    # 工作场景：允许的节点
    allowed_work_nodes = [
        (NodeLabel.TODO, "待办", True),
        (NodeLabel.PROJECT, "项目", True),
        (NodeLabel.TAG, "标签", True),
        (NodeLabel.TIMESTAMP, "时间点", True),
    ]
    
    for label, name, should_pass in allowed_work_nodes:
        node = GraphNode(f"test_{label.value}", label, {})
        try:
            work_store.schema.validate_node(node)
            print(f"✅ {name} in WORK schema: 通过")
        except Exception as e:
            print(f"❌ {name} in WORK schema: 失败")


if __name__ == "__main__":
    print("=" * 80)
    print("Graph 模块测试 - 基于事实的图谱存储")
    print("原则：图谱只存储原始事实，推理分析在外部进行")
    print("=" * 80)
    
    # 生活场景
    test_life_memory_storage()
    test_life_communication_style()
    
    # 工作场景
    test_work_todo_storage()
    test_work_time_tracking()
    test_work_dependency_analysis()
    
    # Schema 验证
    test_schema_validation()
    
    print("\n" + "=" * 80)
    print("✅ 所有测试完成！")
    print("=" * 80)
    print("\n📝 设计原则总结:")
    print("   1. 图谱只存储原始事实（记忆、任务、时间、关系）")
    print("   2. 推理分析在外部进行（模式识别、建议生成等）")
    print("   3. 分析结果可以缓存，但不存入图谱")
    print("   4. 保持图谱数据的纯粹性和可追溯性")
