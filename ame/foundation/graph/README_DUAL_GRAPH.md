# 双图谱架构使用说明

## 概述

Graph 模块采用**双图谱架构**，支持生活（Life）和工作（Work）两个独立的图谱表。

## 核心设计原则

1. **原始事实存储**：图谱只存储原始事实数据，所有推理分析在外部进行
2. **双表隔离**：life_graph 和 work_graph 两张表独立存储，互不干扰
3. **时间属性支持**：所有 Edge 都带有 `create_time`（生效时间）和 `invalid_time`（失效时间）

## 使用示例

### 1. 初始化图谱存储

```python
from ame.foundation.graph.core.falkordb_store import FalkorDBStore
from ame.foundation.graph.utils.models import GraphType

# 创建图谱存储实例（自动初始化两张表）
store = FalkorDBStore(
    host="localhost",
    port=6379,
    base_name="another_me"  # 将创建 another_me_life 和 another_me_work 两张表
)

# 连接并初始化两张表
store.connect()
```

### 2. 添加节点（指定表）

```python
from ame.foundation.graph.utils.models import GraphNode, NodeLabel, GraphType

# 添加到生活图谱
memory_node = GraphNode(
    id="mem_001",
    label=NodeLabel.MEMORY,
    properties={
        "content": "今天和朋友去咖啡厅聊天",
        "timestamp": "2024-01-20T15:30:00"
    }
)
store.add_node(memory_node, graph_type=GraphType.LIFE)

# 添加到工作图谱
todo_node = GraphNode(
    id="todo_001",
    label=NodeLabel.TODO,
    properties={
        "title": "完成图谱模块设计",
        "status": "in_progress",
        "priority": "high"
    }
)
store.add_node(todo_node, graph_type=GraphType.WORK)
```

### 3. 添加边（带时间属性）

```python
from ame.foundation.graph.utils.models import GraphEdge, RelationType
from datetime import datetime

# 创建带时间属性的边
edge = GraphEdge(
    source_id="mem_001",
    target_id="person_001",
    relation_type=RelationType.MENTIONS,
    properties={"context": "在咖啡厅提到了朋友"},
    create_time=datetime(2024, 1, 20, 15, 30),  # 生效时间
    invalid_time=None  # 失效时间（None 表示一直有效）
)

# 添加到生活图谱
store.add_edge(edge, graph_type=GraphType.LIFE)
```

### 4. 查询操作（指定表）

```python
# 从生活图谱查询节点
memory = store.get_node("mem_001", graph_type=GraphType.LIFE)

# 从工作图谱查询节点
todo = store.get_node("todo_001", graph_type=GraphType.WORK)

# 查找邻居节点
neighbors = store.find_neighbors(
    node_id="mem_001",
    graph_type=GraphType.LIFE,
    relation_type=RelationType.MENTIONS,
    direction="out"
)
```

### 5. 时间查询（关系演化）

```python
from datetime import datetime

# 查询特定时间点的有效邻居
neighbors_at_time = store.find_neighbors_at_time(
    node_id="mem_001",
    graph_type=GraphType.LIFE,
    at_time=datetime(2024, 1, 20, 16, 0),  # 查询这个时间点的状态
    relation_type=RelationType.MENTIONS
)
```

### 6. 边的失效（关系演化）

```python
# 使边失效（不删除，只标记失效时间）
store.invalidate_edge(
    source_id="mem_001",
    target_id="person_001",
    relation_type=RelationType.MENTIONS,
    graph_type=GraphType.LIFE,
    invalid_time=datetime(2024, 1, 21, 10, 0)  # 失效时间
)
```

## 节点和关系类型

### 生活场景节点

- `MEMORY`: 记忆节点（日记、聊天记录等）
- `PERSON`: 人物（家人、朋友等）
- `EVENT`: 事件（发生的事情）
- `EMOTION`: 情绪标签（开心、难过等）
- `LOCATION`: 地点（家、公司等）
- `TOPIC`: 话题（兴趣、关注点）
- `TIMESTAMP`: 时间点（用于时间序列分析）

### 生活场景关系

- `MENTIONS`: 提到（记忆提到人物/地点/话题）
- `FEELS`: 感受（记忆关联情绪）
- `PARTICIPATES`: 参与（人物参与事件）
- `OCCURS_AT`: 发生于（事件发生的时间）
- `LOCATED_AT`: 位于（事件发生的地点）
- `RELATES_TO`: 关联（通用关联关系）
- `TALKS_ABOUT`: 讨论（记忆讨论的话题）

### 工作场景节点

- `TODO`: 待办任务
- `PROJECT`: 项目
- `MILESTONE`: 里程碑
- `TAG`: 标签（分类用）
- `TIMESTAMP`: 时间点

### 工作场景关系

- `DEPENDS_ON`: 依赖（任务依赖关系）
- `BELONGS_TO`: 属于（任务属于项目）
- `CONTAINS`: 包含（项目包含任务）
- `BLOCKS`: 阻塞（任务阻塞关系）
- `DUE_AT`: 截止于（任务的截止时间）
- `CONTRIBUTES_TO`: 贡献到（任务贡献到里程碑）
- `CREATED_AT`: 创建于（创建时间）
- `COMPLETED_AT`: 完成于（完成时间）
- `TAGGED_AS`: 标记为（分类标签）

## 外部推理分析

图谱只存储原始事实，所有推理结果应在外部动态生成。例如：

```python
# ❌ 错误：不应该存储推理结果
# suggestion_node = GraphNode(
#     id="sug_001",
#     label=NodeLabel.SUGGESTION,  # 这是推理结果，不应该存在图谱中
#     properties={"content": "建议加强沟通能力"}
# )

# ✅ 正确：基于原始数据进行外部推理
def analyze_communication_pattern(store, user_id):
    """基于原始事实分析沟通模式"""
    # 1. 从图谱查询原始数据
    memories = store.find_neighbors(
        node_id=user_id,
        graph_type=GraphType.LIFE,
        relation_type=RelationType.MENTIONS
    )
    
    # 2. 外部分析推理
    communication_events = [m for m in memories if "沟通" in m.properties.get("content", "")]
    avg_duration = sum(e.properties.get("duration", 0) for e in communication_events) / len(communication_events)
    
    # 3. 生成建议（不存入图谱）
    if avg_duration > 60:
        return "建议：沟通时间较长，可以尝试提高沟通效率"
    else:
        return "沟通效率良好"
```

## 架构优势

1. **职责清晰**：图谱专注于存储，推理专注于分析
2. **灵活性高**：推理逻辑可以随时调整，无需修改图谱结构
3. **数据纯净**：图谱数据只包含客观事实，便于长期维护
4. **时间追溯**：通过 create_time 和 invalid_time 可以追溯关系演化历史
5. **场景隔离**：生活和工作两个图谱独立，互不干扰
