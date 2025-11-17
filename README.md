### ![AME Logo](./another-me-logo.jpg)
# AME (Another Me Engine) 

<div align="center">


[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Architecture](https://img.shields.io/badge/Architecture-4_Layer-orange?style=flat-square)](docs/ARCHITECTURE.md)

**AI 数字分身的核心引擎 | 四层架构 | 模块化设计 | 高度可扩展**

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
- 🏗️ **模块化设计**: 四层架构，易于扩展和测试

---

## 🏗️ 架构设计

AME 采用清晰的**四层架构**，实现职责分离和高度可复用：

```
┌─────────────────────────────────────────────────────┐
│           Application Layer (应用层)                 │
│          FastAPI Backend / CLI / SDK                │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│            Services Layer (业务服务层)                │
│   MimicService | SearchService | ReportService ...  │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│          Capabilities Layer (能力层)                 │
│  HybridRetriever | DataAnalyzer | StyleGenerator    │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│           Foundation Layer (基础层)                  │
│     LLM | Embedding | VectorStore | GraphStore      │
└─────────────────────────────────────────────────────┘
```

### 各层职责

| 层级 | 职责 | 示例 |
|------|------|------|
| **Foundation** | 提供原子化技术能力 | LLM 调用、向量存储、情绪识别 |
| **Capabilities** | 组合基础能力，提供高级功能 | 混合检索、数据分析、风格生成 |
| **Services** | 封装业务逻辑，提供场景化服务 | 智能对话、知识搜索、工作报告 |
| **Application** | 对外接口，集成各种服务 | REST API、命令行工具、SDK |

📖 **详细架构文档**: [docs/wiki/ARCHITECTURE.md](docs/wiki/ARCHITECTURE.md)

---

## 📦 项目结构

```
ame/
├── foundation/              # 基础层 - 原子能力
│   ├── llm/                # LLM 调用器 (OpenAI, etc.)
│   ├── embedding/          # 向量化 (OpenAI Embedding)
│   ├── storage/            # 存储接口 (Vector, Graph, Document)
│   ├── nlp/                # NLP 能力 (NER, Emotion)
│   ├── inference/          # 级联推理引擎
│   └── utils/              # 工具函数
│
├── capabilities/            # 能力层 - 组合能力
│   ├── retrieval/          # 混合检索 (Vector + Graph)
│   ├── analysis/           # 数据分析、洞察提取
│   ├── generation/         # RAG 生成、风格生成
│   ├── memory/             # 记忆管理、过滤器
│   ├── intent/             # 意图识别
│   └── factory.py          # 能力工厂 (依赖注入)
│
├── services/                # 服务层 - 业务逻辑
│   ├── conversation/       # 对话服务 (MimicService)
│   ├── knowledge/          # 知识服务 (Search, Document)
│   ├── life/               # 生活服务 (Mood, Interest, Memory)
│   └── work/               # 工作服务 (Report, Todo, Meeting, Project)
│
├── models/                  # 数据模型
│   ├── domain.py           # 领域模型
│   └── report_models.py    # 报告模型
│
├── data_processor/          # 数据处理器
├── docs/                    # 文档
│   ├── wiki/               # Wiki 文档
│   └── examples/           # 示例代码
│
└── requirements.txt         # 依赖清单
```

---

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.11+
- **依赖**: OpenAI API Key (或兼容 API)
- **可选**: Docker (用于部署)

### 2. 安装

```bash
# 克隆项目
git clone https://github.com/your-repo/another-me.git
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

# 存储配置
VECTOR_STORE_PATH=./data/vector_store
GRAPH_STORE_HOST=localhost
GRAPH_STORE_PORT=6379
```

### 4. 基础使用

```python
from ame.capabilities import CapabilityFactory
from ame.services.conversation import MimicService
from ame.foundation.llm import OpenAICaller
from ame.foundation.embedding import OpenAIEmbedding
from ame.foundation.storage import VectorStore

# 初始化基础组件
llm = OpenAICaller(api_key="sk-...", model="gpt-4")
embedding = OpenAIEmbedding(api_key="sk-...")
vector_store = VectorStore(path="./data/vectors")

# 创建能力工厂
factory = CapabilityFactory(
    llm_caller=llm,
    embedding_function=embedding,
    vector_store=vector_store
)

# 初始化服务
mimic_service = MimicService(capability_factory=factory)

# 开始对话
response = await mimic_service.chat(
    user_message="你好，今天天气真好！",
    context={"user_id": "user_123"}
)

print(response["content"])
```

📖 **更多示例**: [docs/examples/](docs/examples/)

---

## 📚 核心功能

### 1️⃣ 智能对话 (MimicService)

模仿用户的语言风格，提供自然流畅的对话体验。

```python
from ame.services.conversation import MimicService

# 智能对话
response = await mimic_service.chat(
    user_message="帮我分析一下最近的工作状态",
    context={"user_id": "user_123"}
)

# 流式对话
async for chunk in mimic_service.chat_stream(
    user_message="讲个故事给我听",
    context={"user_id": "user_123"}
):
    print(chunk, end="", flush=True)
```

**功能特性**:
- ✅ 内容安全过滤
- ✅ 意图识别 (聊天/搜索/记忆/分析)
- ✅ 智能路由
- ✅ 风格模仿
- ✅ 记忆管理

📖 [对话服务文档](services/conversation/README.md)

---

### 2️⃣ 知识管理 (Knowledge Services)

强大的 RAG 知识库，支持文档上传、智能检索。

```python
from ame.services.knowledge import SearchService, DocumentService

# 文档服务
doc_service = DocumentService(capability_factory=factory)

# 上传文档
doc_id = await doc_service.upload(
    file_path="./documents/meeting_notes.pdf",
    metadata={"category": "work", "date": "2024-01-01"}
)

# 智能搜索
search_service = SearchService(capability_factory=factory)
results = await search_service.search(
    query="上季度销售数据",
    top_k=5
)
```

**功能特性**:
- ✅ 多格式支持 (PDF, DOCX, TXT, MD)
- ✅ 混合检索 (向量 + 图谱)
- ✅ 自动实体提取
- ✅ 智能分类

📖 [知识服务文档](services/knowledge/README.md)

---

### 3️⃣ 生活助手 (Life Services)

情绪追踪、兴趣发现、记忆时间线。

```python
from ame.services.life import MoodService, InterestService, MemoryService

# 情绪分析
mood_service = MoodService(capability_factory=factory)
mood_report = await mood_service.analyze_mood(
    user_id="user_123",
    time_range="last_week"
)

# 兴趣发现
interest_service = InterestService(capability_factory=factory)
interests = await interest_service.discover_interests(
    user_id="user_123"
)

# 记忆时间线
memory_service = MemoryService(capability_factory=factory)
timeline = await memory_service.get_timeline(
    user_id="user_123",
    start_date="2024-01-01"
)
```

📖 [生活服务文档](services/life/README.md)

---

### 4️⃣ 工作助手 (Work Services)

周报生成、待办管理、会议纪要、项目追踪。

```python
from ame.services.work import ReportService, TodoService, MeetingService

# 周报生成
report_service = ReportService(capability_factory=factory)
weekly_report = await report_service.generate_weekly_report(
    user_id="user_123",
    start_date="2024-01-01",
    end_date="2024-01-07"
)

# 智能待办
todo_service = TodoService(capability_factory=factory)
task = await todo_service.parse_task("明天下午3点前完成报告")

# 会议纪要
meeting_service = MeetingService(capability_factory=factory)
minutes = await meeting_service.summarize(
    meeting_content="今天讨论了...",
    meeting_date=datetime.now()
)
```

📖 [工作服务文档](services/work/README.md)

---

## 🛠️ 开发指南

### 依赖注入规范

AME 使用 **CapabilityFactory** 实现依赖注入，所有 Service 层必须遵循以下规范：

✅ **正确做法**:
```python
class MyService:
    def __init__(self, capability_factory: CapabilityFactory):
        self.factory = capability_factory
        self.llm = factory.llm
        self.retriever = factory.create_retriever(cache_key="my_retriever")
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

📖 [开发规范](docs/wiki/DEVELOPMENT.md)

---

### 测试

```bash
# 运行所有测试
pytest tests/ -v

# 测试特定模块
pytest tests/foundation/test_llm.py -v
pytest tests/capabilities/test_retrieval.py -v
pytest tests/services/test_mimic_service.py -v

# 代码覆盖率
pytest --cov=ame tests/
```

---

## 📖 文档

### 📘 Wiki 文档

- [架构设计](docs/wiki/ARCHITECTURE.md) - 四层架构详解
- [开发指南](docs/wiki/DEVELOPMENT.md) - 开发规范和最佳实践
- [API 参考](docs/wiki/API_REFERENCE.md) - 完整 API 文档
- [部署指南](docs/wiki/DEPLOYMENT.md) - Docker 部署和配置

### 📙 层级文档

- [Foundation Layer](foundation/README.md) - 基础能力层
- [Capabilities Layer](capabilities/README.md) - 能力组合层
- [Services Layer](services/README.md) - 业务服务层

### 📗 服务文档

- [Conversation Services](services/conversation/README.md) - 对话服务
- [Knowledge Services](services/knowledge/README.md) - 知识服务
- [Life Services](services/life/README.md) - 生活服务
- [Work Services](services/work/README.md) - 工作服务

---

## 🎓 示例代码

### 基础示例

- [基础使用](docs/examples/01_basic_usage.py) - 快速上手
- [能力工厂](docs/examples/02_capability_factory.py) - 工厂模式
- [检索系统](docs/examples/03_retrieval_system.py) - 混合检索

### 服务示例

- [智能对话](docs/examples/04_mimic_service.py) - 对话服务
- [知识问答](docs/examples/05_knowledge_qa.py) - RAG 问答
- [情绪追踪](docs/examples/06_mood_tracking.py) - 情绪分析
- [工作报告](docs/examples/07_work_report.py) - 报告生成

### 高级示例

- [自定义能力](docs/examples/08_custom_capability.py) - 扩展能力
- [Pipeline 定制](docs/examples/09_custom_pipeline.py) - 检索管道
- [多服务集成](docs/examples/10_service_integration.py) - 服务组合

📂 **所有示例**: [docs/examples/](docs/examples/)

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！

### 贡献流程

1. **Fork** 本项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 **Pull Request**

### 开发规范

- 遵循 PEP 8 代码规范
- 添加完整的类型提示
- 编写单元测试
- 更新相关文档

📖 [贡献指南详情](CONTRIBUTING.md)

---

## 📋 Roadmap

### ✅ 已完成

- [x] 四层架构设计
- [x] Foundation Layer 实现
- [x] Capabilities Layer 实现
- [x] Services Layer 实现
- [x] 完整文档体系

### 🚧 进行中

- [ ] 完整的测试覆盖
- [ ] 性能优化
- [ ] 多模型支持

### 📅 计划中

- [ ] WebUI 管理界面
- [ ] 插件系统
- [ ] 云端同步
- [ ] 移动端支持

---

## 📜 License

本项目采用 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

感谢以下开源项目:

- [LangChain](https://github.com/langchain-ai/langchain) - LLM 应用框架
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代 Web 框架
- [Faiss](https://github.com/facebookresearch/faiss) - 向量检索
- [FalkorDB](https://github.com/FalkorDB/FalkorDB) - 图数据库

---

## 📧 联系方式

- **项目主页**: https://github.com/your-repo/another-me
- **问题反馈**: [GitHub Issues](https://github.com/your-repo/another-me/issues)
- **邮箱**: your-email@example.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给一个 Star！**

Made with ❤️ by AME Team

</div>
