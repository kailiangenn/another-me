# Another-Me 代码实现细节

> **实现指南**: 本文档提供系统的详细代码实现、接口定义和使用示例,配合 [architecture.md](./architecture.md) 理解架构设计

> 📋 **文档说明**: 
> - 包含完整的项目目录结构
> - 遵循**模块抽象层 + 原子能力层**的四层架构设计
> - 采用**扩平化目录结构**，通过命名约定区分职责
> - 提供各层详细的接口定义和代码示例
> - 所有代码示例均可直接参考使用
> - 强调**自下而上**的能力实现方式

---

## 📚 文档目录

1. [完整项目目录结构](#完整项目目录结构)
   - [1.1 目录架构总览](#目录架构总览)
   - [1.2 基础能力层目录](#基础能力层目录)
   - [1.3 组合能力层目录](#组合能力层目录)
   - [1.4 服务层目录](#服务层目录)
2. [基础能力层代码实现](#基础能力层代码实现)
   - [2.1 LLM模块](#llm模块)
   - [2.2 Vector模块](#vector模块)
   - [2.3 Graph模块](#graph模块)
   - [2.4 NLP模块](#nlp模块)
   - [2.5 File模块](#file模块)
   - [2.6 Algorithm模块](#algorithm模块)
3. [组合能力层代码实现](#组合能力层代码实现)
   - [3.1 Life场景能力](#life场景能力)
   - [3.2 Work场景能力](#work场景能力)
   - [3.3 能力工厂实现](#能力工厂实现)
4. [服务层代码实现](#服务层代码实现)
   - [4.1 ChatService实现](#chatservice实现)
   - [4.2 WorkProjectService实现](#workprojectservice实现)
   - [4.3 WorkTodoService实现](#worktodoservice实现)
   - [4.4 WorkAdviceService实现](#workadviceservice实现)
5. [数据模型定义](#数据模型定义)
6. [使用示例与最佳实践](#使用示例与最佳实践)

---

## 1. 完整项目目录结构

> 💡 **架构理念**: 目录结构遵循**自下而上**的能力提供方式，从原子能力层向上构建模块抽象，再组合成能力，最终在服务层对外提供完整功能

> 📌 **设计原则**: 
> - **扩平化设计**: 每个模块目录内文件直接存放，无多层嵌套
> - **命名约定**: 通过文件名区分职责（`*_caller.py`, `*_store.py`, `*_manager.py`等）
> - **模块分离**: 每个模块自包含 `models.py` 统一管理数据类

### 1.1 目录架构总览

```
another-me/
├── ame/                          # 核心代码目录
│   ├── foundation/               # ⭐ 原子能力层
│   ├── capability/               # 🔧 组合能力层
│   ├── service/                  # 🚀 服务层
│   ├── models/                   # 📦 数据模型
│   ├── requirements.txt          # 依赖清单
│   └── setup.py                  # 包安装脚本
├── ame-tests/                    # 测试代码目录
├── ame-doc/                      # 文档目录
└── README.md
```

### 1.2 基础能力层目录

> 🏛️ **设计理念**: 基础能力层采用**模块抽象层 + 原子能力层**两层设计，提供最小粒度的基础能力

> 📁 **模块内部结构**: 每个模块采用 **utils + core + components** 三层结构

**模块内部职责划分**：
- **utils/**: 通用工具层
  - `models.py`: 数据模型定义
  - `exceptions.py`: 异常类定义
  
- **core/**: 核心实现层（原子能力层）
  - `base.py`: **抽象基类**（定义接口契约，保证扩展性）
  - 第三方服务调用器：`*_caller.py`（如 `openai_caller.py`）
  - 存储实现：`*_store.py`（如 `faiss_store.py`）
  - 解析器：`*_parser.py`（如 `pdf_parser.py`）
  - 分析器：`*_analyzer.py`（如 `emotion_analyzer.py`）
  
- **components/**: 组合组件层（模块抽象层）
  - 构建器：`*_builder.py`（如 `prompt_builder.py`）
  - 管理器：`*_manager.py`（如 `history_manager.py`）
  - 检索器：`*_retriever.py`（如 `hybrid_retriever.py`）

```
foundation/                     # 基础能力层
├── __init__.py
├── llm/                       # 🧠 LLM模块
│   ├── __init__.py
│   ├── utils/                 # 通用工具
│   │   ├── __init__.py
│   │   ├── models.py         # 数据模型
│   │   └── exceptions.py     # 异常定义
│   ├── core/                  # 核心实现（原子层）
│   │   ├── __init__.py
│   │   ├── base.py           # 抽象基类：LLMCaller
│   │   ├── openai_caller.py  # OpenAI API调用器
│   │   └── claude_caller.py  # Claude API调用器(可选)
│   └── components/            # 组合组件（模块层）
│       ├── __init__.py
│       ├── prompt_builder.py # 提示词构建器
│       └── history_manager.py# 历史管理器
│
├── embedding/                 # 🔢 Embedding模块
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── exceptions.py
│   └── core/
│       ├── __init__.py
│       ├── base.py           # 抽象基类：Embedding
│       └── simple_embedding.py # OpenAI Embedding API
│
├── vector/                    # 🔢 Vector模块
│   ├── __init__.py
│   ├── utils/                 # 通用工具
│   │   ├── __init__.py
│   │   ├── models.py         # 数据模型
│   │   └── exceptions.py     # 异常定义
│   └── core/                  # 核心实现（原子层）
│       ├── __init__.py
│       ├── base.py           # 抽象基类：VectorStore
│       └── faiss_store.py    # Faiss向量存储
│
├── graph/                     # 🕸️ Graph模块
│   ├── __init__.py
│   ├── utils/                 # 通用工具
│   │   ├── __init__.py
│   │   ├── models.py         # 含GraphSchema定义
│   │   ├── validators.py     # 数据验证器
│   │   └── exceptions.py
│   └── core/                  # 核心实现（原子层）
│       ├── __init__.py
│       ├── base.py           # 抽象基类：GraphStore
│       └── falkordb_store.py # FalkorDB图存储
│
├── nlp/                       # 📝 NLP模块
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── exceptions.py
│   └── core/                  # 核心实现（原子层）
│       ├── __init__.py
│       ├── base.py           # 抽象基类：EmotionAnalyzer, EntityExtractor等
│       ├── emotion_analyzer.py  # 情绪分析(spaCy/HuggingFace)
│       ├── entity_extractor.py  # 实体提取NER(spaCy)
│       ├── intent_classifier.py # 意图识别
│       └── summarizer.py        # 文本摘要
│
├── file/                      # 📄 File模块
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── exceptions.py
│   └── core/                  # 核心实现（原子层）
│       ├── __init__.py
│       ├── base.py           # 抽象基类：FileParser
│       ├── pdf_parser.py     # PDF解析(PyPDF2)
│       ├── docx_parser.py    # Word解析(python-docx)
│       ├── markdown_parser.py# Markdown解析
│       ├── text_parser.py    # 文本解析
│       └── ppt_parser.py     # PPT解析
│
└── algorithm/                 # ⚙️ Algorithm模块
    ├── __init__.py
    ├── utils/
    │   ├── __init__.py
    │   └── models.py
    └── core/                  # 核心实现（原子层）
        ├── __init__.py
        ├── base.py           # 抽象基类：SimilarityCalculator等
        ├── text_similarity.py    # 文本相似度(NumPy)
        ├── time_analyzer.py      # 时间解析
        └── todo_sorter.py        # 拓扑排序(NetworkX)
```

### 组合能力层结构

### 1.3 组合能力层目录

> 🔧 **设计理念**: 组合能力层基于原子能力的组合,完成抽象的业务步骤

```
capability/                    # 组合能力层
├── __init__.py
├── common/                    # 🔧 通用组合能力
│   ├── __init__.py
│   └── hybrid_retriever.py   # 混合检索器(Faiss 0.6 + Falkor 0.4)
│
├── life/                      # 🏡 Life场景能力
│   ├── __init__.py
│   ├── intent_recognizer.py  # 意图识别器
│   ├── context_retriever.py  # 上下文检索器
│   ├── dialogue_generator.py # 对话生成器
│   ├── memory_extractor.py   # 记忆提取器
│   └── tests/
│
├── work/                      # 💼 Work场景能力
│   ├── __init__.py
│   ├── document_parser.py    # 文档解析器
│   ├── project_analyzer.py   # 项目分析器
│   ├── todo_parser.py        # 待办解析器
│   ├── todo_manager.py       # 待办管理器
│   ├── pattern_analyzer.py   # 模式分析器
│   ├── advice_generator.py   # 建议生成器
│   └── tests/
│
└── factory.py                 # 能力工厂(依赖注入)
```

### 服务层结构

### 1.4 服务层目录

> 🚀 **设计理念**: 服务层编排组合能力,实现完整的业务流程,直接对外提供服务

```
service/                       # 服务层
├── __init__.py
├── life/                      # 🏡 生活场景服务
│   ├── __init__.py
│   ├── chat_service.py       # ChatService
│   └── tests/
│
└── work/                      # 💼 工作场景服务
    ├── __init__.py
    ├── project_service.py    # WorkProjectService
    ├── todo_service.py       # WorkTodoService
    ├── advice_service.py     # WorkAdviceService
    └── tests/
```

---

## 2. 基础能力层代码实现

> 🏛️ **能力基座**: 基础能力层是整个系统的能力基座，提供最小粒度的原子操作

> 🏛️ **两层架构**: 采用**模块抽象层 + 原子能力层**的两层设计
> - **模块抽象层**: 定义能力边界和对外接口，屏蔽底层实现细节
> - **原子能力层**: 提供具体的技术实现(如OpenAI、Faiss、spaCy等)

### 2.0 base.py 设计理念

> 🔑 **扩展性保证**: 每个模块的 `core/base.py` 定义抽象基类，确保用户可以自定义扩展

**设计原则**：

1. **开闭原则** (Open-Closed Principle)
   - 对扩展开放：用户可以继承 `base.py` 中的抽象类实现自己的版本
   - 对修改关闭：上层代码只依赖抽象接口，不感知底层实现变化

2. **里氏替换原则** (Liskov Substitution Principle)
   - 所有实现类都可以透明替换
   - 例：`OpenAICaller`、`ClaudeCaller` 都可以替换 `LLMCaller`

3. **依赖倒置原则** (Dependency Inversion Principle)
   - 上层模块依赖抽象，而非具体实现
   - 例：`HybridRetriever` 依赖 `VectorStore` 抽象，而非 `FaissStore`

**扩展示例**：

```
# 用户可以自定义 LLM 实现
from ame.foundation.llm.core.base import LLMCaller

class CustomLLMCaller(LLMCaller):
    """[用户自定义] 本地LLM调用器"""
    
    def call(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        # 调用本地 LLaMA 模型
        return self.local_llama.generate(prompt)
    
    def call_stream(self, prompt: str, model: str):
        # 流式输出
        for chunk in self.local_llama.stream(prompt):
            yield chunk

# 系统自动支持，无需修改上层代码
caller = CustomLLMCaller()
response = caller.call("Hello", "llama-7b", 0.7, 100)
```

**base.py 核心职责**：

| 模块 | base.py 定义的抽象类 | 说明 |
|------|---------------------|------|
| **LLM** | `LLMCaller` | 定义 `call()`, `call_stream()`, `batch_call()` 接口 |
| **Embedding** | `Embedding` | 定义 `embed()`, `embed_batch()` 接口 |
| **Vector** | `VectorStore` | 定义 `add()`, `search()` 接口 |
| **Graph** | `GraphStore` | 定义 `add_node()`, `add_edge()`, `query()` 接口 |
| **NLP** | `EmotionAnalyzer`, `EntityExtractor`, `IntentClassifier`, `Summarizer` | 定义各自NLP能力接口 |
| **File** | `FileParser` | 定义 `parse()` 统一接口 |
| **Algorithm** | `SimilarityCalculator`, `TimeAnalyzer`, `Sorter` | 定义算法类接口 |

---

### 2.1 LLM模块

#### 模块定位

**能力边界**: 大模型调用、提示词管理、对话历史管理

**技术选型**: OpenAI API (GPT-4/GPT-3.5-turbo)

**对外接口**: `call()`, `build_prompt()`, `manage_history()`

**目录结构** (utils + core + components):
```
llm/
├── __init__.py
├── utils/                 # 通用工具
│   ├── __init__.py
│   ├── models.py         # 数据模型
│   └── exceptions.py     # 异常定义
├── core/                  # 核心实现（原子层）
│   ├── __init__.py
│   ├── base.py           # 抽象基类：LLMCaller(保证扩展性)
│   ├── openai_caller.py  # OpenAI API调用器
│   └── claude_caller.py  # Claude API调用器(可选)
└── components/            # 组合组件（模块层）
    ├── __init__.py
    ├── prompt_builder.py # 提示词构建器
    └── history_manager.py# 历史管理器
```

#### 模块层接口定义

```python
from abc import ABC, abstractmethod
from typing import Iterator, List, Dict

class LLMCaller(ABC):
    """LLM调用抽象基类"""
    
    @abstractmethod
    def call(self, prompt: str, model: str, temperature: float, max_tokens: int) -> str:
        """
        同步调用LLM
        - 输入: 提示词、模型配置参数
        - 输出: 生成的文本响应
        - 功能: 支持重试、缓存、日志记录
        """
        pass
    
    @abstractmethod
    def call_stream(self, prompt: str, model: str) -> Iterator[str]:
        """流式调用LLM"""
        pass
    
    @abstractmethod
    def batch_call(self, prompts: List[str]) -> List[str]:
        """批量调用LLM"""
        pass

class PromptBuilder:
    """提示词构建器"""
    
    def build(self, template: str, context: Dict, variables: Dict) -> str:
        """构建提示词"""
        pass
    
    def build_with_history(self, template: str, history: List[Dict]) -> str:
        """带历史的提示词构建"""
        pass
    
    def build_few_shot(self, template: str, examples: List[Dict]) -> str:
        """Few-shot提示词构建"""
        pass

class HistoryManager:
    """对话历史管理器"""
    
    def manage(self, messages: List[Dict], max_length: int) -> List[Dict]:
        """管理对话历史"""
        pass
    
    def summarize_history(self, messages: List[Dict], llm_caller) -> str:
        """压缩历史为摘要"""
        pass
```

### 2.2 Vector模块

#### 模块定位

**能力边界**: 向量存储与相似度检索

**技术选型**: Faiss

**对外接口**: `add()`, `search()`

**关键特性**:
- 轻量高效的向量检索，适合中小规模场景
- 支持向量+文本+元数据一起存储
- 高效的余弦相似度计算

**目录结构** (utils + core):
```
vector/
├── __init__.py
├── utils/                 # 通用工具
│   ├── __init__.py
│   ├── models.py         # 数据模型
│   └── exceptions.py     # 异常定义
└── core/                  # 核心实现（原子层）
    ├── __init__.py
    ├── base.py           # 抽象基类：VectorStore(保证扩展性)
    └── faiss_store.py    # Faiss向量存储
```

#### 模块层接口定义

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class VectorStore(ABC):
    """向量存储抽象接口"""
    
    @abstractmethod
    def add(self, id: str, vector: List[float], metadata: Dict) -> bool:
        """
        添加向量
        - 输入: ID、向量、元数据
        - 输出: 添加成功与否
        - 功能: 支持向量+文本+元数据一起存储
        """
        pass
    
    @abstractmethod
    def search(self, query_vector: List[float], top_k: int, filter: Dict = None) -> List[Dict]:
        """
        相似度检索
        - 输入: 查询向量、返回数量、过滤条件
        - 输出: 相似结果列表
        - 功能: 基于余弦相似度检索
        """
        pass
    
    @abstractmethod
    def delete(self, id: str) -> bool:
        """删除向量"""
        pass
    
    @abstractmethod
    def update(self, id: str, vector: List[float], metadata: Dict) -> bool:
        """更新向量"""
        pass

---

### 2.3 Graph模块

#### 模块定位

**能力边界**: 图谱存储、图查询、关系演化分析

**技术选型**: FalkorDB

**对外接口**: `add_node()`, `add_edge()`, `query()`

**关键特性**:
- 图边支持时间属性: `create_time`(生效时间) / `invalid_time`(失效时间)
- 支持关系演化分析，跟踪关系变化
- 与Redis生态集成，高性能图计算

**目录结构** (utils + core):
```
graph/
├── __init__.py
├── utils/                 # 通用工具
│   ├── __init__.py
│   ├── models.py         # 含GraphSchema定义
│   ├── validators.py     # 数据验证器
│   └── exceptions.py
└── core/                  # 核心实现（原子层）
    ├── __init__.py
    ├── base.py           # 抽象基类：GraphStore(保证扩展性)
    └── falkordb_store.py # FalkorDB图存储
```

#### 模块层接口定义

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class GraphStore(ABC):
    """图存储抽象接口"""
    
    @abstractmethod
    def add_node(self, node_type: str, properties: Dict) -> str:
        """
        添加节点
        - 输入: 节点类型、属性字典
        - 输出: 节点ID
        """
        pass
    
    @abstractmethod
    def add_edge(self, from_id: str, to_id: str, edge_type: str, properties: Dict) -> str:
        """
        添加边(支持时间属性)
        - 输入: 起点ID、终点ID、边类型、属性字典
        - 输出: 边ID
        - properties应包含: create_time, invalid_time
        """
        pass
    
    @abstractmethod
    def query(self, cypher: str, params: Dict = None) -> List[Dict]:
        """
        Cypher查询
        - 输入: Cypher查询语句、参数
        - 输出: 查询结果列表
        """
        pass
    
    @abstractmethod
    def update_edge(self, edge_id: str, properties: Dict) -> bool:
        """
        更新边(用于设置invalid_time)
        - 输入: 边ID、更新属性
        - 输出: 更新成功与否
        """
        pass
    
    @abstractmethod
    def delete_node(self, node_id: str) -> bool:
        """删除节点"""
        pass
    
    @abstractmethod
    def delete_edge(self, edge_id: str) -> bool:
        """删除边"""
        pass
```

#### GraphSchema定义

**设计理念**: 定义标准的图谱结构,支持时间维度的关系演化分析

```python
class GraphSchema:
    """图谱Schema定义"""
    
    NODE_TYPES = {
        'User': ['user_id', 'name', 'created_at'],
        'Memory': ['content', 'emotion', 'timestamp'],
        'Entity': ['name', 'type', 'description'],  # NER提取
        'Document': ['title', 'content', 'type', 'created_at'],
        'Todo': ['title', 'priority', 'status', 'deadline'],
        'Session': ['session_id', 'start_time', 'end_time']
    }
    
    EDGE_TYPES = {
        'MENTIONS': {  # (Document/Memory)-[:MENTIONS]->(Entity)
            'properties': ['create_time', 'invalid_time']
        },
        'LIKES': {  # (User)-[:LIKES]->(Entity)
            'properties': ['create_time', 'invalid_time', 'intensity']
        },
        'DEPENDS_ON': {  # (Todo)-[:DEPENDS_ON]->(Todo)
            'properties': ['create_time', 'invalid_time']
        }
    }
```

---

## 3. 组合能力层代码实现

> 🔧 **能力组合**: 组合能力层将多个原子能力组合起来,完成抽象的业务步骤

> 🎯 **编排理念**: 服务层通过编排这些组合能力实现完整的业务流程

### 3.0 通用组合能力

#### HybridRetriever - 混合检索器

**设计理念**: 将 Vector 模块的向量检索与 Graph 模块的图查询融合，提供更全面的检索能力

**核心功能**:
- 并行调用向量检索（Faiss）和图谱检索（FalkorDB）
- 加权融合策略: Faiss 0.6 + Falkor 0.4
- 支持语义相似度 + 关系推理

```python
from typing import List, Dict
from ame.foundation.vector.core.base import VectorStore
from ame.foundation.graph.core.base import GraphStore

class HybridRetriever:
    """混合检索器 - Faiss 0.6 + Falkor 0.4"""
    
    def __init__(self, 
                 vector_store: VectorStore, 
                 graph_store: GraphStore, 
                 vector_weight: float = 0.6, 
                 graph_weight: float = 0.4):
        """
        初始化混合检索器
        
        Args:
            vector_store: 向量存储实例
            graph_store: 图存储实例
            vector_weight: 向量检索权重（默认0.6）
            graph_weight: 图查询权重（默认0.4）
        """
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.vector_weight = vector_weight
        self.graph_weight = graph_weight
    
    def retrieve(self, query: str, query_vector: List[float], top_k: int = 5) -> List[Dict]:
        """
        混合检索
        
        流程:
        1. 并行调用向量检索和图谱检索
        2. 加权融合分数
        3. 排序返回top_k结果
        
        Args:
            query: 查询文本
            query_vector: 查询向量
            top_k: 返回结果数量
        
        Returns:
            融合后的检索结果列表
        """
        # 1. 并行调用向量检索和图谱检索
        vector_results = self.vector_store.search(query_vector, top_k * 2)
        graph_results = self._graph_search(query, top_k * 2)
        
        # 2. 加权融合
        fused = self._fuse_scores(vector_results, graph_results)
        
        # 3. 排序返回
        return sorted(fused, key=lambda x: x['score'], reverse=True)[:top_k]
    
    def _graph_search(self, query: str, top_k: int) -> List[Dict]:
        """图谱检索"""
        # 根据查询构建Cypher语句
        cypher = """
        MATCH (m:Memory)-[:MENTIONS]->(e:Entity)
        WHERE e.name CONTAINS $query
        RETURN m, e, score
        ORDER BY score DESC
        LIMIT $top_k
        """
        return self.graph_store.query(cypher, {'query': query, 'top_k': top_k})
    
    def _fuse_scores(self, vector_results: List[Dict], graph_results: List[Dict]) -> List[Dict]:
        """加权融合分数"""
        # 合并结果，按ID去重
        merged = {}
        
        # 处理向量结果
        for item in vector_results:
            item_id = item['id']
            merged[item_id] = {
                'id': item_id,
                'content': item['content'],
                'score': item['score'] * self.vector_weight,
                'source': 'vector'
            }
        
        # 处理图结果
        for item in graph_results:
            item_id = item['id']
            if item_id in merged:
                # 已存在，融合分数
                merged[item_id]['score'] += item['score'] * self.graph_weight
                merged[item_id]['source'] = 'hybrid'
            else:
                # 新增
                merged[item_id] = {
                    'id': item_id,
                    'content': item['content'],
                    'score': item['score'] * self.graph_weight,
                    'source': 'graph'
                }
        
        return list(merged.values())
```

---

### 3.1 Life场景能力

```python
class IntentRecognizer:
    """意图识别器"""
    def recognize(self, message: str, context: Dict = None) -> Dict:
        # 1. 调用LLM分析意图
        # 2. 使用分类器归类
        # 3. 返回意图对象
        pass

class ContextRetriever:
    """上下文检索器"""
    def retrieve(self, query: str, query_vector: List[float], session_id: str, top_k: int = 5):
        # 使用混合检索(Faiss 0.6 + Falkor 0.4)
        results = self.retriever.retrieve(query, query_vector, top_k)
        return results

class DialogueGenerator:
    """对话生成器"""
    def generate(self, context: List[Dict], message: str) -> str:
        # 1. 分析用户风格
        # 2. 构建个性化提示词
        # 3. 调用LLM生成回复
        pass

class MemoryExtractor:
    """记忆提取器"""
    def extract(self, conversation: List[Dict]) -> List[Dict]:
        # 1. 调用LLM提取记忆点
        # 2. 情绪分析
        # 3. 实体提取(NER)
        # 4. 时间解析
        pass
```

### 3.2 Work场景能力

```python
class TodoParser:
    """待办解析器"""
    def parse(self, description: str) -> List[Dict]:
        # 1. 调用LLM解析任务
        # 2. 提取时间信息(create_time/deadline)
        # 3. 提取优先级
        pass

class TodoManager:
    """待办管理器"""
    def manage(self, new_todos: List[Dict], user_id: str) -> List[Dict]:
        # 1. 查询已有待办
        # 2. 去重合并
        # 3. 拓扑排序
        # 4. 存入图谱
        pass
```

### 3.3 能力工厂实现

**设计模式**: 依赖注入 + 工厂模式

**核心价值**:
- 🔌 统一依赖管理: 服务层无需关心能力实例创建细节
- 🔄 依赖注入: 自动处理能力之间的依赖关系
- 🧪 可测试性: 支持Mock替换,便于单元测试

```python
class CapabilityFactory:
    """能力工厂 - 统一管理组合能力的创建和依赖注入"""
    
    _instances = {}
    
    @classmethod
    def get_intent_recognizer(cls) -> 'IntentRecognizer':
        """获取意图识别器"""
        if 'intent_recognizer' not in cls._instances:
            llm_caller = cls._get_llm_caller()
            intent_classifier = cls._get_intent_classifier()
            cls._instances['intent_recognizer'] = IntentRecognizer(llm_caller, intent_classifier)
        return cls._instances['intent_recognizer']
    
    @classmethod
    def get_context_retriever(cls) -> 'ContextRetriever':
        """获取上下文检索器"""
        if 'context_retriever' not in cls._instances:
            vector_store = cls._get_vector_store()
            graph_store = cls._get_graph_store()
            hybrid_retriever = cls._get_hybrid_retriever(vector_store, graph_store)
            cls._instances['context_retriever'] = ContextRetriever(hybrid_retriever)
        return cls._instances['context_retriever']
    
    # ... 其他能力获取方法 ...
    
    @classmethod
    def _get_hybrid_retriever(cls, vector_store, graph_store):
        """获取混合检索器(权重: Faiss 0.6 + Falkor 0.4)"""
        return HybridRetriever(vector_store, graph_store, vector_weight=0.6, graph_weight=0.4)
```

---

## 4. 服务层代码实现

> 🚀 **业务编排**: 服务层编排组合能力,实现完整的业务流程,直接对外提供服务

> 👥 **用户视角**: 用户只需调用Service层接口,底层Capability和Foundation由系统自动编排执行

### 4.1 ChatService实现

**服务职责**: 提供个性化对话能力,模仿用户风格,管理对话记忆

**能力编排**: IntentRecognizer + ContextRetriever + DialogueGenerator + MemoryExtractor

```python
class ChatService:
    """生活对话服务"""
    
    def __init__(self):
        self.intent_recognizer = CapabilityFactory.get_intent_recognizer()
        self.context_retriever = CapabilityFactory.get_context_retriever()
        self.dialogue_generator = CapabilityFactory.get_dialogue_generator()
        self.memory_extractor = CapabilityFactory.get_memory_extractor()
    
    def chat(self, message: str, session_id: str) -> str:
        """对话接口"""
        # 1. 意图识别
        intent = self.intent_recognizer.recognize(message)
        
        # 2. 上下文检索(混合检索0.6+0.4)
        context = self.context_retriever.retrieve(message, session_id)
        
        # 3. 对话生成
        response = self.dialogue_generator.generate(context, message)
        
        return response
    
    def end_session(self, session_id: str):
        """结束会话,提取记忆"""
        conversation = self._get_conversation(session_id)
        memories = self.memory_extractor.extract(conversation)
        self._save_to_graph(memories)
```

### 4.2 WorkProjectService实现

**服务职责**: 分析项目文档,提取核心要素,生成结构化报告

**能力编排**: DocumentParser + ProjectAnalyzer

```python
class WorkProjectService:
    """项目分析服务"""
    
    def __init__(self):
        self.document_parser = CapabilityFactory.get_document_parser()
        self.project_analyzer = CapabilityFactory.get_project_analyzer()
    
    def analyze_project(self, files: List[str]) -> str:
        """
        分析项目文档
        
        流程:
        1. 文档解析: 支持PDF/Word/MD/PPT
        2. 实体提取: NER提取核心实体
        3. 图谱构建: (Document)-[:MENTIONS]->(Entity)
        4. 报告生成: LLM生成Markdown报告
        """
        # 1. 文档解析
        documents = self.document_parser.parse(files)
        
        # 2-4. 项目分析
        report = self.project_analyzer.analyze(documents)
        
        return report
```

### 4.3 WorkTodoService实现

**服务职责**: 智能解析任务,去重合并,拓扑排序,持久化管理

**能力编排**: TodoParser + TodoManager

```python
class WorkTodoService:
    """待办管理服务"""
    
    def add_todos(self, description: str, user_id: str) -> List[Dict]:
        # 1. 任务解析
        todos = self.todo_parser.parse(description)
        
        # 2-5. 管理待办(去重/排序/存储)
        sorted_todos = self.todo_manager.manage(todos, user_id)
        
        return sorted_todos
```

### 4.4 WorkAdviceService实现

**服务职责**: 分析工作模式,生成个性化改进建议

**能力编排**: PatternAnalyzer + AdviceGenerator

```python
class WorkAdviceService:
    """工作建议服务"""
    
    def __init__(self):
        self.pattern_analyzer = CapabilityFactory.get_pattern_analyzer()
        self.advice_generator = CapabilityFactory.get_advice_generator()
    
    def generate_advice(self, user_id: str) -> str:
        """
        生成工作建议
        
        流程:
        1. 数据收集: 从图谱查询工作数据
        2. 模式分析: 计算完成率、延期率、效率分数
        3. 建议生成: LLM生成个性化建议
        4. Markdown格式化
        """
        # 1-2. 分析工作模式
        pattern = self.pattern_analyzer.analyze(user_id)
        
        # 3-4. 生成建议
        advice = self.advice_generator.generate(pattern)
        
        return advice
```

---

## 5. 数据模型定义

### 5.1 Life场景数据模型

```python
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class Message:
    """消息对象"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    session_id: str

@dataclass
class Intent:
    """意图对象"""
    intent_type: str  # 'chat', 'query', 'command'
    sub_intent: Optional[str]
    confidence: float

@dataclass
class Memory:
    """记忆对象"""
    content: str
    emotion: str
    emotion_intensity: float
    entities: List[Dict]  # [{entity: str, type: str}]
    timestamp: datetime
    session_id: str
    create_time: str  # 生效时间
    invalid_time: Optional[str]  # 失效时间

@dataclass
class Context:
    """上下文对象"""
    messages: List[Message]
    memories: List[Memory]
    score: float  # 相关性分数
```

### 5.2 Work场景数据模型

```python
@dataclass
class Document:
    """文档对象"""
    title: str
    content: str
    file_type: str  # 'pdf', 'docx', 'md', 'ppt'
    metadata: Dict
    created_at: datetime

@dataclass
class Todo:
    """待办对象"""
    title: str
    description: str
    priority: int  # 1-5
    status: str  # 'pending', 'in_progress', 'done'
    create_time: datetime
    deadline: Optional[datetime]
    dependencies: List[str]  # 依赖的其他待办ID
    invalid_time: Optional[datetime]  # 失效时间

@dataclass
class ProjectReport:
    """项目报告对象"""
    title: str
    summary: str
    entities: List[Dict]
    structure: Dict
    markdown_content: str

@dataclass
class WorkPattern:
    """工作模式对象"""
    completion_rate: float  # 完成率
    delay_rate: float  # 延期率
    efficiency_score: float  # 效率分数
    peak_hours: List[int]  # 高效时间段
    common_patterns: List[str]  # 常见模式
```

---

## 6. 使用示例与最佳实践

### 6.1 时间属性使用示例

### 6.1 时间属性使用示例

**设计理念**: 通过`create_time`和`invalid_time`实现关系的时间维度管理,支持关系演化分析

#### 添加带时间的边

```python
# 用户开始喜欢某实体
graph_store.add_edge(
    user_id, entity_id, 'LIKES',
    {
        'create_time': '2024-01-01',
        'invalid_time': None,  # 当前有效
        'intensity': 0.8
    }
)

# 用户不再喜欢该实体
graph_store.update_edge(edge_id, {'invalid_time': '2024-12-31'})
```

#### Cypher查询示例

``cypher
# 查询当前仍有效的喜好
MATCH (u:User)-[r:LIKES]->(e:Entity)
WHERE r.invalid_time IS NULL
RETURN e

# 查询指定时间范围的关系
MATCH (u:User)-[r:LIKES]->(e:Entity)
WHERE r.create_time <= '2024-06-30' 
  AND (r.invalid_time IS NULL OR r.invalid_time > '2024-06-30')
RETURN e, r
```

---

### 6.2 混合检索使用示例

**设计理念**: 并行调用Vector模块(语义)和Graph模块(关系),加权融合(0.6+0.4)

```python
# 使用混合检索
from ame.capability.common import HybridRetriever
from ame.foundation.vector.core import FaissStore
from ame.foundation.graph.core import FalkorDBStore

# 初始化
v ector_store = FaissStore()
graph_store = FalkorDBStore()
hybrid_retriever = HybridRetriever(vector_store, graph_store)

# 检索
results = hybrid_retriever.retrieve(
    query="我上次和张三讨论的项目是什么?",
    query_vector=embedding,  # 由Embedding模块生成
    top_k=5
)

# 返回结果包含融合后的相关性分数
for result in results:
    print(f"内容: {result['content']}")
    print(f"分数: {result['score']}")
    print(f"来源: {result['source']}")  # 'vector', 'graph', or 'hybrid'
```

### 6.3 服务层调用示例

#### ChatService使用示例

```python
from service.life import ChatService

# 初始化服务
chat_service = ChatService()

# 发起对话
response = chat_service.chat(
    message="今天心情不好,想找人聊聊",
    session_id="session_123"
)

print(response)  # 个性化回复

# 结束会话,提取记忆
chat_service.end_session("session_123")
```

#### WorkTodoService使用示例

```python
from service.work import WorkTodoService

todo_service = WorkTodoService()

# 添加待办
todos = todo_service.add_todos(
    description="""
    本周需要完成:
    1. 完成项目设计文档(优先级高,周三前)
    2. 写单元测试(依赖设计文档)
    3. Code Review
    """,
    user_id="user_123"
)

# 返回排序后的待办列表
for todo in todos:
    print(f"{todo.title} - 优先级: {todo.priority}")
```

#### WorkAdviceService使用示例

```python
from service.work import WorkAdviceService

advice_service = WorkAdviceService()

# 生成工作建议
advice = advice_service.generate_advice(user_id="user_123")

print(advice)  # Markdown格式的建议
```

### 6.4 最佳实践

#### 1. 服务层调用原则

**✅ 正确做法**:
```python
# 用户只需调用Service层
from service.life import ChatService

chat_service = ChatService()
response = chat_service.chat(message, session_id)
```

**❌ 错误做法**:
```python
# 不要直接调用Capability或Foundation层
from capability.life import IntentRecognizer  # 错误!
from foundation.llm import OpenAICaller  # 错误!
```

#### 2. 能力工厂使用

**✅ 正确做法**:
```python
# 通过CapabilityFactory获取能力
from capability import CapabilityFactory

retriever = CapabilityFactory.get_context_retriever()
```

**❌ 错误做法**:
```python
# 不要直接实例化能力类
retriever = ContextRetriever(...)  # 错误!
```

#### 3. 时间属性管理

**✅ 正确做法**:
```python
# 添加关系时总是设置create_time
graph_store.add_edge(
    user_id, entity_id, 'LIKES',
    {
        'create_time': datetime.now().isoformat(),
        'invalid_time': None,  # 当前有效
        'intensity': 0.8
    }
)

# 失效时更新invalid_time
graph_store.update_edge(edge_id, {
    'invalid_time': datetime.now().isoformat()
})
```

**❌ 错误做法**:
```python
# 不要删除关系,应该设置invalid_time
graph_store.delete_edge(edge_id)  # 错误!
```

#### 4. 混合检索配置

**✅ 正确做法**:
```python
# 使用默认权重(Vector 0.6 + Graph 0.4)
from ame.capability.common import HybridRetriever

retriever = HybridRetriever(vector_store, graph_store)

# 或根据场景调整权重
retriever = HybridRetriever(
    vector_store, graph_store,
    vector_weight=0.7,  # 更侧重语义相似度
    graph_weight=0.3
)
```

#### 5. 错误处理

```python
from foundation.llm.utils.exceptions import LLMError
from foundation.vector.utils.exceptions import VectorStoreError  
from foundation.graph.utils.exceptions import GraphStoreError

try:
    response = chat_service.chat(message, session_id)
except LLMError as e:
    # 处理LLM调用错误
    logger.error(f"LLM错误: {e}")
    response = "抱歉,我现在无法回复"
except (VectorStoreError, GraphStoreError) as e:
    # 处理存储错误
    logger.error(f"存储错误: {e}")
    response = "抱歉,数据检索失败"
```

### 6.5 性能优化建议

1. **缓存策略**: 使用LLM缓存减少重复调用
2. **批量处理**: 对多个请求使用`batch_call`
3. **异步调用**: 对于耗时操作使用异步方式
4. **向量索引优化**: 定期重建 Faiss 索引提升检索效率
5. **图谱查询优化**: 使用索引加速Cypher查询

---

