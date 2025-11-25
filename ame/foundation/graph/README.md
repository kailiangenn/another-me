# Graph 图谱模块

## 概述

Graph 模块是 AnotherMe 系统的核心组件之一，用于存储和管理用户的个人知识图谱数据。模块采用**双图谱架构**，支持生活（Life）和工作（Work）两个独立的图谱表。

## 核心设计原则

1. **原始事实存储**：图谱只存储原始事实数据，所有推理分析在外部进行
2. **双表隔离**：life_graph 和 work_graph 两张表独立存储，互不干扰
3. **时间属性支持**：所有 Edge 都带有 `create_time`（生效时间）和 `invalid_time`（失效时间）
4. **可扩展性**：支持动态添加新的节点和关系类型
5. **Cypher 语法内化**：提供高级接口，用户无需直接编写复杂的 Cypher 语法

## 架构组成

```
graph/
├── components/          # 组件层
│   ├── schema.py        # Schema 管理
│   ├── query_builder.py # 查询构建器
│   └── time_handler.py  # 时间处理器
├── core/                # 核心层
│   ├── base.py          # 抽象基类
│   └── falkordb_store.py# FalkorDB 实现
├── utils/               # 工具层
│   ├── models.py        # 数据模型
│   ├── exceptions.py    # 异常定义
│   └── logger.py        # 日志工具
└── README.md            # 本文件
```

## 核心组件

### 1. 数据模型 (utils/models.py)

定义了图谱的核心数据结构：

- `NodeLabel`: 节点标签枚举（包含生活和工作场景）
- `RelationType`: 关系类型枚举（包含生活和工作场景）
- `GraphType`: 图谱类型枚举（LIFE/WORK）
- `GraphNode`: 图节点数据类
- `GraphEdge`: 图边数据类（支持时间属性）
- `QueryResult`: 查询结果数据类

### 2. Schema 管理 (components/schema.py)

负责验证节点和边是否符合图谱规范：

- `LifeGraphSchema`: 生活图谱 Schema
- `WorkGraphSchema`: 工作图谱 Schema

### 3. 抽象基类 (core/base.py)

采用模板方法模式，内化通用组件能力：

- 连接管理
- 节点操作（增删改查）
- 边操作（增删改查）
- 查询操作
- 时间处理

### 4. 查询构建器 (components/query_builder.py)

提供链式 API 构建 Cypher 查询：

- 节点匹配
- 关系匹配
- 条件过滤
- 结果排序和限制
- 路径查找

### 5. 存储实现 (core/falkordb_store.py)

FalkorDB 的具体实现，只关注底层操作。

## Cypher 语法内化

Graph 模块通过内化 Cypher 语法，让用户无需直接编写复杂的查询语句就能完成各种操作。主要特性包括：

### 1. 高级节点操作接口

- `add_node()`: 添加节点（自动进行 Schema 验证）
- `get_node()`: 通过 ID 获取节点
- `get_nodes_by_properties()`: 通过属性获取节点列表
- `update_node()`: 更新节点属性
- `delete_node()`: 删除节点
- `delete_nodes_by_properties()`: 通过属性删除节点
- `search_nodes()`: 高级搜索节点
- `count_nodes()`: 统计节点数量

### 2. 高级边操作接口

- `add_edge()`: 添加边（自动进行 Schema 验证）
- `get_edges()`: 获取边
- `delete_edge()`: 删除边
- `invalidate_edge()`: 使边失效（关系演化）

### 3. 高级查询接口

- `find_neighbors()`: 查找邻居节点
- `find_neighbors_at_time()`: 时间点查询邻居
- `find_path()`: 查找两个节点之间的路径
- `search_nodes()`: 搜索节点
- `count_nodes()`: 统计节点数量

### 4. 自动参数化和安全防护

所有内化接口都使用参数化查询，防止 Cypher 注入攻击。

## 节点和关系类型

### 生活场景节点

- `MEMORY`: 记忆节点（日记、聊天记录等）
- `PERSON`: 人物（家人、朋友等）
- `EVENT`: 事件（发生的事情）
- `EMOTION`: 情绪标签（开心、难过等）
- `LOCATION`: 地点（家、公司等）
- `TOPIC`: 话题（兴趣、关注点）
- `INTEREST`: 兴趣爱好
- `SKILL`: 技能
- `GOAL`: 目标
- `HABIT`: 习惯
- `ACHIEVEMENT`: 成就
- `TIMESTAMP`: 时间点（用于时间序列分析）
- `DOCUMENT`: 文档
- `ENTITY`: 实体（通用命名实体）

### 生活场景关系

- `MENTIONS`: 提到（记忆提到人物/地点/话题）
- `FEELS`: 感受（记忆关联情绪）
- `PARTICIPATES`: 参与（人物参与事件）
- `OCCURS_AT`: 发生于（事件发生的时间）
- `LOCATED_AT`: 位于（事件发生的地点）
- `RELATES_TO`: 关联（通用关联关系）
- `TALKS_ABOUT`: 讨论（记忆讨论的话题）
- `INTERESTED_IN`: 感兴趣
- `HAS_SKILL`: 拥有技能
- `WORKS_ON`: 从事于（目标/项目）
- `DEVELOPS`: 培养（习惯）
- `ACHIEVED`: 达成（成就）
- `REFERENCES`: 引用（文档引用关系）
- `FOLLOWS`: 跟随（时间序列关系）

### 工作场景节点

- `TODO`: 待办任务
- `PROJECT`: 项目
- `MILESTONE`: 里程碑
- `TAG`: 标签（分类用）
- `ROLE`: 角色/职位
- `ORGANIZATION`: 组织/公司
- `MEETING`: 会议
- `DECISION`: 决策
- `ISSUE`: 问题/议题
- `TIMESTAMP`: 时间点
- `DOCUMENT`: 文档
- `ENTITY`: 实体（通用命名实体）

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
- `ASSIGNED_TO`: 分配给（角色）
- `REPORTS_TO`: 汇报给（组织结构）
- `ATTENDS`: 参加（会议）
- `MAKES`: 做出（决策）
- `RESOLVES`: 解决（问题）
- `REFERENCES`: 引用（文档引用关系）
- `FOLLOWS`: 跟随（时间序列关系）
- `RELATES_TO`: 关联（通用关联关系）

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
interest_node = GraphNode(
    id="interest_001",
    label=NodeLabel.INTEREST,
    properties={
        "name": "摄影",
        "level": "advanced"
    }
)
store.add_node(interest_node, graph_type=GraphType.LIFE)

# 添加到工作图谱
role_node = GraphNode(
    id="role_001",
    label=NodeLabel.ROLE,
    properties={
        "title": "软件工程师",
        "department": "技术部"
    }
)
store.add_node(role_node, graph_type=GraphType.WORK)
```

### 3. 添加边（带时间属性）

```python
from ame.foundation.graph.utils.models import GraphEdge, RelationType
from datetime import datetime

# 创建带时间属性的边
edge = GraphEdge(
    source_id="person_001",
    target_id="interest_001",
    relation_type=RelationType.INTERESTED_IN,
    properties={"since": "2020-01-01"},
    create_time=datetime(2020, 1, 1),  # 生效时间
    invalid_time=None  # 失效时间（None 表示一直有效）
)

# 添加到生活图谱
store.add_edge(edge, graph_type=GraphType.LIFE)
```

### 4. 查询操作（指定表）

```python
# 从生活图谱查询节点
interest = store.get_node("interest_001", graph_type=GraphType.LIFE)

# 查找邻居节点
neighbors = store.find_neighbors(
    node_id="person_001",
    graph_type=GraphType.LIFE,
    relation_type=RelationType.INTERESTED_IN,
    direction="out"
)

# 高级搜索节点
results = store.search_nodes(
    graph_type=GraphType.LIFE,
    label=NodeLabel.INTEREST,
    properties={"level": "advanced"},
    limit=10,
    order_by="name",
    order_direction="ASC"
)

# 统计节点数量
count = store.count_nodes(
    graph_type=GraphType.LIFE,
    label=NodeLabel.INTEREST
)
```

### 5. 关系演化

```python
from datetime import datetime

# 使边失效（不删除，只标记失效时间）
store.invalidate_edge(
    source_id="person_001",
    target_id="interest_001",
    relation_type=RelationType.INTERESTED_IN,
    graph_type=GraphType.LIFE,
    invalid_time=datetime(2023, 1, 1)  # 失效时间
)
```

## 外部推理分析

图谱只存储原始事实，所有推理结果应在外部动态生成。例如：

```python
# ✅ 正确：基于原始数据进行外部推理
def analyze_skill_patterns(store, user_id):
    """基于原始事实分析技能模式"""
    # 1. 从图谱查询原始数据
    skills = store.find_neighbors(
        node_id=user_id,
        graph_type=GraphType.LIFE,
        relation_type=RelationType.HAS_SKILL
    )
    
    # 2. 外部分析推理
    skill_names = [s.properties.get("name") for s in skills]
    
    # 3. 生成洞察（不存入图谱）
    if "Python编程" in skill_names and "机器学习" in skill_names:
        return "您具备Python和机器学习技能，可以考虑向数据科学方向发展"
    else:
        return "建议继续扩展技能组合"
```

## 架构优势

1. **职责清晰**：图谱专注于存储，推理专注于分析
2. **灵活性高**：推理逻辑可以随时调整，无需修改图谱结构
3. **数据纯净**：图谱数据只包含客观事实，便于长期维护
4. **时间追溯**：通过 create_time 和 invalid_time 可以追溯关系演化历史
5. **场景隔离**：生活和工作两个图谱独立，互不干扰
6. **易于扩展**：支持动态添加新的节点和关系类型
7. **使用简单**：内化 Cypher 语法，用户无需关注底层实现细节