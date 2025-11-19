# Storage 模块

图数据库存储模块，基于FalkorDB实现图谱数据的管理。

## 📁 目录结构

```
storage/
├── core/                      # 核心层
│   ├── models.py             # 数据模型（GraphNode, GraphEdge等）
│   ├── schema.py             # Schema定义（NodeLabel, RelationType）
│   ├── exceptions.py         # 异常定义
│   └── validators.py         # 数据验证器
│
├── atomic/                    # 原子层
│   ├── base.py               # 抽象基类
│   └── falkordb_store.py     # FalkorDB实现
│
├── pipeline/                  # 管道层
│   ├── base.py               # 管道基类
│   ├── life_graph_pipeline.py   # 生活图谱
│   └── work_graph_pipeline.py   # 工作图谱
│
└── __init__.py
```

## 🎯 核心特性

### 1. 三层架构设计

- **Core层**: 数据模型、Schema、验证规则
- **Atomic层**: 数据库基础操作（CRUD）
- **Pipeline层**: 轻量数据操作编排

### 2. 双图谱隔离

- **life_graph**: 生活领域（人物、事件、兴趣、情绪等）
- **work_graph**: 工作领域（项目、任务、文档、会议等）

### 3. 关系时间属性

每条边包含时间属性：
- `valid_from`: 关系生效时间
- `valid_until`: 关系失效时间（None表示仍有效）

**生活场景示例**:
- INTERESTED_IN: 开始喜欢→不再喜欢
- KNOWS: 认识→失联

**工作场景示例**:
- WORKS_ON: 开始工作→完成
- DEPENDS_ON: 依赖建立→依赖解除

### 4. 封闭的Schema定义

**节点标签（NodeLabel）**:
- 生活: Person, Event, Emotion, Interest, Location, Memory, Topic
- 工作: Project, Task, Document, Meeting, Concept, Milestone, Issue

**关系类型（RelationType）**:
- 生活: KNOWS, FAMILY, FRIEND, ATTENDS, FEELS, INTERESTED_IN等
- 工作: WORKS_ON, DEPENDS_ON, BELONGS_TO, ASSIGNED_TO等

## 🚀 使用示例

### 基础使用

```python
from foundation.storage import (
    LifeGraphPipeline,
    WorkGraphPipeline,
    GraphNode,
    GraphEdge,
    NodeLabel,
    RelationType
)
from datetime import datetime

# 1. 初始化生活图谱
life_pipeline = LifeGraphPipeline(
    host="localhost",
    port=6379
)
await life_pipeline.initialize()

# 2. 创建节点
person_node = GraphNode(
    label=NodeLabel.PERSON,
    properties={"name": "张三", "user_id": "user123"}
)
person_id = await life_pipeline.validate_and_create_node(person_node)

interest_node = GraphNode(
    label=NodeLabel.INTEREST,
    properties={"name": "编程"}
)
interest_id = await life_pipeline.validate_and_create_node(interest_node)

# 3. 创建关系（包含时间属性）
edge = GraphEdge(
    source_id=person_id,
    target_id=interest_id,
    relation=RelationType.INTERESTED_IN,
    valid_from=datetime.now(),  # 开始喜欢的时间
    valid_until=None  # 仍然喜欢
)
edge_id = await life_pipeline.validate_and_create_edge(edge)
```

### 时间相关操作

```python
# 标记兴趣失效（不再喜欢）
await life_pipeline.mark_edge_as_invalid(
    edge_id,
    end_time=datetime.now()
)

# 查询当前活跃的兴趣
active_interests = await life_pipeline.get_active_relationships(
    node_id=person_id,
    relation=RelationType.INTERESTED_IN
)

# 查询历史某个时间点的兴趣
past_interests = await life_pipeline.get_active_relationships(
    node_id=person_id,
    relation=RelationType.INTERESTED_IN,
    at_time=datetime(2024, 1, 1)
)
```

### 批量操作

```python
# 批量创建节点
nodes = [
    GraphNode(label=NodeLabel.PERSON, properties={"name": "李四"}),
    GraphNode(label=NodeLabel.PERSON, properties={"name": "王五"}),
]
node_ids = await life_pipeline.batch_create_nodes(nodes)

# Merge节点（存在则更新，不存在则创建）
node_id = await life_pipeline.merge_or_create_node(
    node=GraphNode(label=NodeLabel.PERSON, properties={"name": "张三"}),
    merge_keys=["name"]  # 基于name去重
)
```

## 📋 数据模型

### GraphNode
```python
@dataclass
class GraphNode:
    label: NodeLabel                    # 节点类型
    properties: Dict[str, Any]          # 属性字典
    id: Optional[str] = None            # 数据库生成的ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

### GraphEdge
```python
@dataclass
class GraphEdge:
    source_id: str                      # 源节点ID
    target_id: str                      # 目标节点ID
    relation: RelationType              # 关系类型
    properties: Dict[str, Any]          # 属性字典
    weight: float = 1.0                 # 权重
    valid_from: datetime                # 生效时间
    valid_until: Optional[datetime]     # 失效时间
    id: Optional[str] = None
    created_at: Optional[datetime] = None
```

## ⚠️ 重要约束

1. **Schema封闭**: 只能使用预定义的NodeLabel和RelationType
2. **领域隔离**: LifeGraphPipeline只允许创建生活领域节点，WorkGraphPipeline只允许工作领域节点
3. **必需属性**: 每种节点类型有必需属性（见GraphSchema.NODE_REQUIRED_PROPS）
4. **时间一致性**: edge的valid_until不能早于valid_from

## 🔧 配置

### 环境变量
```bash
GRAPH_STORE_HOST=localhost
GRAPH_STORE_PORT=6379
GRAPH_STORE_PASSWORD=  # 可选
```

### FalkorDB部署
```yaml
# docker-compose.yml
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
    volumes:
      - falkordb_data:/data
```

## 📝 开发注意事项

1. **Foundation层保持轻量**: Pipeline只做数据操作编排，不包含业务逻辑
2. **业务逻辑在Capability层**: 实体提取、关系识别等应在上层实现
3. **时间索引优化**: valid_from和valid_until已自动创建索引
4. **异步操作**: 所有数据库操作都是异步的，需使用await

## 🧪 测试

```bash
# 运行基础测试
python ame-tests/foundation/storage/test_storage_basic.py
```

## 📚 扩展阅读

- [FalkorDB官方文档](https://docs.falkordb.com/)
- [Cypher查询语言](https://neo4j.com/docs/cypher-manual/)
- [图数据库设计模式](https://graphacademy.neo4j.com/)
