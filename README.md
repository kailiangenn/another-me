<div align="center">
    <img src="./another-me-logo.jpg" alt="AME Logo" width="200" />
</div>

<div align="center">

# AME (Another Me Engine)

</div>

<div align="center">


[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Architecture](https://img.shields.io/badge/Architecture-3_Layer-orange?style=flat-square)](ame-doc/architecture.md)

**AI 数字分身的核心引擎 | 三层架构 | 模块化设计 | 高度可扩展**

[快速开始](#快速开始) • [架构设计](#架构设计) • [文档](#文档) • [示例](#示例) • [贡献指南](#贡献指南)

</div>

---

## 🎯 项目简介

**AME (Another Me Engine)** 是一个强大的 AI 数字分身引擎，旨在通过用户的个人数据（聊天记录、日记、知识库）训练出一个"像你"的 AI 助手。

### 核心特性

- 🧠 **智能对话**: 模仿用户的语言风格和思维模式
- 📚 **知识管理**: 强大的 RAG 知识库，支持智能检索
- 💡 **记忆系统**: 自动分类和管理对话记忆
- 📊 **数据分析**: 情绪追踪、兴趣发现、工作报告
- 🔒 **隐私优先**: 数据完全本地存储，可离线运行
- 🏗️ **模块化设计**: 三层架构,易于扩展和测试

---

## 🏗️ 架构设计

AME 采用清晰的**三层架构**,实现职责分离和高度可复用:

```
┌─────────────────────────────────────────────────────┐
│            Service Layer (业务服务层)                │
│     LifeChatService | Work Components              │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│          Capability Layer (能力层)                   │
│    🔧 CapabilityFactory (依赖注入中心)               │
│  Life Capabilities | Work Capabilities             │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│           Foundation Layer (基础层)                  │
│  LLM | File | NLP | Storage | Algorithm             │
└─────────────────────────────────────────────────────┘
```

### 各层职责

| 层级 | 职责 | 实际实现 |
|------|------|----------|
| **Foundation** | 提供原子化技术能力 | LLM调用器、文档解析、NLP能力、图存储、算法 |
| **Capability** | 组合基础能力,提供高级功能 | 生活能力(上下文/对话/记忆)、工作能力(项目/待办/建议) |
| **Service** | 封装业务逻辑,提供场景化服务 | LifeChatService、工作能力组件、连接测试 |

### 🔧 CapabilityFactory - 依赖注入中心

**CapabilityFactory** 是架构的核心枢纽,负责:

- ✅ 统一创建和管理所有能力实例
- ✅ 实现依赖注入,Service层只依赖Factory
- ✅ 支持实例缓存和复用
- ✅ 提供预设能力包(Life/Work)

📖 **详细架构文档**: [ame-doc/architecture.md](ame-doc/architecture.md)

---

## 📦 项目结构

```
ame/
├── foundation/              # 基础层 - 原子能力
│   ├── llm/                # LLM 调用器 (OpenAI)
│   │   ├── atomic/         # 原子能力: OpenAICaller, 策略模式
│   │   ├── core/           # 核心模型和异常
│   │   └── pipeline/       # 管道: SessionPipe, DocumentPipe
│   │
│   ├── file/               # 文档解析器
│   │   ├── atomic/         # PDF/DOCX/Markdown/PPT/Text 解析器
│   │   ├── core/           # 文档模型
│   │   └── pipeline/       # 文档处理管道
│   │
│   ├── nlp/                # NLP 能力
│   │   ├── atomic/         # 意图识别、实体提取、情感分析、摘要
│   │   └── core/           # NLP模型
│   │
│   ├── storage/            # 存储接口
│   │   ├── atomic/         # FalkorDB 图存储
│   │   ├── core/           # 存储模型和Schema
│   │   └── pipeline/       # 图处理管道 (Life/Work)
│   │
│   └── algorithm/          # 算法能力
│       └── todo_sorter.py  # 待办优先级排序
│
├── capability/              # 能力层 - 组合能力
│   ├── life/               # 生活场景能力
│   │   ├── context_retriever.py    # 上下文检索
│   │   ├── dialogue_generator.py   # 对话生成
│   │   └── memory_extractor.py     # 记忆提取
│   │
│   ├── work/               # 工作场景能力
│   │   ├── project_analyzer.py     # 项目分析器
│   │   ├── todo_manager.py         # 待办管理器
│   │   └── advice_generator.py     # 建议生成器
│   │
│   └── factory.py          # ⭐ 能力工厂 (依赖注入中心)
│
├── service/                 # 服务层 - 业务逻辑
│   ├── connect/            # 连接测试服务
│   │   ├── test_llm.py         # LLM 连接测试
│   │   └── test_storage.py     # 存储连接测试
│   │
│   ├── life/               # 生活服务
│   │   └── life_chat_service.py    # 生活对话服务
│   │
│   └── work/               # 工作服务组件
│       ├── project.py          # 项目服务
│       ├── todo.py             # 待办服务
│       └── suggest.py          # 建议服务
│
└── requirements.txt         # 依赖清单
```

---

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.11+
- **依赖**: OpenAI API Key (或兼容 API)
- **可选**: FalkorDB (用于知识图谱)

### 2. 安装

```bash
# 克隆项目
git clone https://github.com/kailiangenn/another-me.git
cd another-me/ame

# 创建虚拟环境
conda create -n ame python=3.11
conda activate ame

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置

创建 `.env` 文件：

```bash
# OpenAI 配置
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 图存储配置
GRAPH_STORE_HOST=localhost
GRAPH_STORE_PORT=6379
```

### 4. 快速上手示例

#### 示例 1: LLM 连接测试

```python
from ame.capability.factory import CapabilityFactory

# 创建能力工厂
factory = CapabilityFactory()

# 创建 LLM 测试能力
llm_tester = factory.create_llm_test_capability(
    api_key="sk-...",
    model="gpt-3.5-turbo"
)

# 测试基础调用
result = await llm_tester.test_basic_call()
print(f"测试结果: {result}")
```

#### 示例 2: 生活对话服务

```python
from ame.service.life import LifeChatService
from ame.capability.factory import CapabilityFactory

# 创建工厂和服务
factory = CapabilityFactory()

chat_service = LifeChatService(
    capability_factory=factory,
    llm_api_key="sk-...",
    graph_host="localhost"
)

# 开始对话
session_id = await chat_service.start_session(user_id="user_123")
response = await chat_service.chat(session_id, "你好,最近天气怎么样?")
print(response)
```

#### 示例 3: 待办管理

```python
from ame.capability.factory import CapabilityFactory

factory = CapabilityFactory()

# 创建待办管理器
todo_manager = factory.create_todo_manager(
    api_key="sk-...",
    graph_host="localhost"
)

# 解析并添加待办
task = await todo_manager.parse_and_add_task(
    "明天下午3点前完成项目报告"
)
print(f"待办任务: {task}")
```

---

## 📚 功能清单

### ✅ 已实现功能

#### Foundation Layer (基础层)

| 模块 | 功能 | 关键类 |
|------|------|----------|
| **llm** | LLM调用、策略模式、管道模式 | `OpenAICaller`, `SessionPipe`, `DocumentPipe` |
| **file** | 多格式文档解析 | PDF/DOCX/Markdown/PPT/Text 解析器 |
| **nlp** | NLP能力 | `IntentRecognizer`, `EntityExtractor`, `EmotionAnalyzer`, `Summarizer` |
| **storage** | 图存储 | `FalkorDBStore`, `GraphStoreBase`, `Pipeline` |
| **algorithm** | 算法能力 | `TodoSorter` (优先级排序算法) |

#### Capability Layer (能力层)

| 模块 | 功能 | 关键类 |
|------|------|----------|
| **factory** | 统一创建入口 | `CapabilityFactory` (核心枢纽) |
| **life** | 生活场景能力 | `ContextRetriever`, `DialogueGenerator`, `MemoryExtractor` |
| **work** | 工作场景能力 | `ProjectAnalyzer`, `TodoManager`, `AdviceGenerator` |

#### Service Layer (服务层)

| 服务 | 状态 | 说明 |
|------|------|------|
| **LifeChatService** | ✅ 已实现 | 对话服务(意图识别+上下文检索+生成+记忆提取) |
| **工作能力组件** | ✅ 已实现 | 项目分析、待办管理、建议生成(独立组件形态) |
| **连接测试服务** | ✅ 已实现 | LLM测试、存储测试 |

---

### 🖍️ 规划中功能

#### 近期规划

- [ ] **知识管理服务**: 文档上传、智能搜索、RAG问答
- [ ] **混合检索系统**: 向量+图谱混合检索
- [ ] **风格模仿服务**: 基于用户历史对话模仿风格
- [ ] **工作报告服务**: 周报/月报自动生成

#### 中远期规划

- [ ] **多模态支持**: 图片、音频处理能力
- [ ] **插件系统**: 支持自定义能力扩展
- [ ] **WebUI管理界面**: 可视化配置和管理
- [ ] **云端同步**: 多设备数据同步

---

---

## 🛠️ 开发指南

### CapabilityFactory 使用规范

AME 使用 **CapabilityFactory** 实现依赖注入,所有 Service 层必须遵循以下规范:

✅ **正确做法**:
```python
class MyService:
    def __init__(self, capability_factory: CapabilityFactory):
        self.factory = capability_factory
        # 通过Factory获取能力
        self.llm = factory.create_llm_caller(
            api_key="sk-...",
            cache_key="my_llm"
        )
        self.intent_recognizer = factory.create_intent_recognizer()
```

❌ **错误做法**:
```python
# 禁止在 Service 内部创建 Factory
class MyService:
    def __init__(self, llm, embedding, vector_store, ...):
        self.factory = CapabilityFactory(...)  # ❌

# 禁止直接传递大量 Foundation 层组件
service = MyService(llm, embedding, vector_store, graph_store, ner, ...)  # ❌
```

### CapabilityFactory 提供的能力

```python
from ame.capability.factory import CapabilityFactory

factory = CapabilityFactory()

# Foundation-LLM
llm_caller = factory.create_llm_caller(api_key="sk-...", cache_key="main")

# Foundation-Storage
graph_store = factory.create_graph_store(host="localhost", port=6379)

# Foundation-NLP
intent_recognizer = factory.create_intent_recognizer()
entity_extractor = factory.create_entity_extractor()
emotion_analyzer = factory.create_emotion_analyzer()
summarizer = factory.create_summarizer()

# Foundation-Algorithm
todo_sorter = factory.create_todo_sorter()

# Capability-Life Package
life_capabilities = factory.create_life_capability_package(
    llm_api_key="sk-...",
    graph_host="localhost"
)

# Capability-Work Package
work_capabilities = factory.create_work_capability_package(
    llm_api_key="sk-...",
    graph_host="localhost"
)

# Test Capabilities
llm_tester = factory.create_llm_test_capability(api_key="sk-...")
storage_tester = factory.create_storage_test_capability(host="localhost")
```

---

### 测试

```bash
# 运行所有测试
pytest ame-tests/ -v

# 测试特定模块
pytest ame-tests/foundation/llm/test_openai_caller.py -v
pytest ame-tests/foundation/storage/test_storage_basic.py -v

# 代码覆盖率
pytest --cov=ame ame-tests/
```

---

## 📖 文档

### 📘 项目文档

- [架构设计](ame-doc/architecture.md) - 精简版三层架构文档

> 💡 **代码即文档**: 本项目采用代码即文档理念,详细实现请直接查阅带有完整类型注解和docstring的源码。

### 📗 测试文档

- [测试说明](ame-tests/README.md) - 测试指南
- [Storage测试](ame-tests/foundation/storage/README.md) - 图存储测试指南

---

## 📝 Roadmap

### ✅ 已完成

- [x] 三层架构设计
- [x] Foundation Layer 实现 (LLM/File/NLP/Storage/Algorithm)
- [x] Capability Layer 实现 (Life/Work + Factory)
- [x] Service Layer 基础实现 (LifeChatService + Work Components)
- [x] CapabilityFactory 依赖注入中心

### 🚧 进行中

- [ ] 向量存储增强 (Faiss)
- [ ] 混合检索系统 (向量+图谱)
- [ ] NLP能力增强 (可配置意图/自定义词典/多策略摘要)
- [ ] Algorithm能力增强 (文本相似度/时间模式分析)
- [ ] 测试覆盖率提升 (NLP/Storage/Algorithm单元测试)

### 📅 计划中

- [ ] 知识管理服务 (SearchService, DocumentService)
- [ ] 混合检索系统 (Vector + Graph)
- [ ] 风格模仿服务 (MimicService)
- [ ] 工作报告服务 (ReportService)
- [ ] WebUI 管理界面
- [ ] 插件系统
- [ ] 多模型支持

---

## 🙏 致谢

感谢以下开源项目:

- [FastAPI](https://github.com/tiangolo/fastapi) - 现代 Web 框架
- [FalkorDB](https://github.com/FalkorDB/FalkorDB) - 图数据库
- [OpenAI](https://openai.com/) - LLM API

---

## 📝 License

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 📧 联系方式

- **项目主页**: https://github.com/kailiangenn/another-me
- **问题反馈**: [GitHub Issues](https://github.com/kailiangenn/another-me/issues)
- **邮箱**: shangkl@enn.cn

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

Made with ❤️ by EnnIoT Team

</div>
