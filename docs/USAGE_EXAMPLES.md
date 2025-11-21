# AME模块使用示例

> 本文档提供AME模块的实际使用示例和快速入门指南

---

## 目录

1. [环境配置](#环境配置)
2. [Foundation层使用](#foundation层使用)
3. [Capability层使用](#capability层使用)
4. [Service层使用](#service层使用)
5. [完整示例](#完整示例)

---

## 环境配置

### 安装依赖

```bash
# 激活conda环境
conda activate anotherme

# 安装核心依赖
pip install openai falkordb loguru

# 可选依赖(文档解析)
pip install PyPDF2 python-docx python-pptx

# 可选依赖(NLP)
pip install jieba
```

### 环境变量

```python
import os
os.environ["OPENAI_API_KEY"] = "your-api-key"
os.environ["OPENAI_BASE_URL"] = "https://api.openai.com/v1"
```

---

## Foundation层使用

### 1. LLM基础调用

```python
from ame.foundation.llm import OpenAICaller

# 创建LLM调用器
llm = OpenAICaller(
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)

# 生成回复
async def example():
    messages = [
        {"role": "user", "content": "你好"}
    ]
    response = await llm.generate(messages)
    print(response.content)
```

### 2. PromptBuilder使用

```python
from ame.foundation.llm import PromptBuilder

builder = PromptBuilder()

# 构建提示词
prompt = builder.build(
    template="你是{role},擅长{skill}",
    variables={"role": "助手", "skill": "编程"},
    context={}
)
```

### 3. HistoryManager使用

```python
from ame.foundation.llm import HistoryManager, CompressionStrategy

manager = HistoryManager(llm_caller=llm, max_length=4000)

# 管理历史消息
managed = manager.manage(
    messages=history,
    strategy=CompressionStrategy.TRUNCATE,
    max_messages=10
)
```

### 4. Embedding使用

```python
from ame.foundation.embedding import SimpleEmbedding

embedder = SimpleEmbedding(dimension=128)

# 文本向量化
result = embedder.embed_text("测试文本")
vector = result.embedding

# 计算相似度
similarity = embedder.cosine_similarity(vec1, vec2)
```

### 5. 文档解析

```python
from ame.foundation.file import DocumentParsePipeline

pipeline = DocumentParsePipeline()

# 解析文档
async def parse():
    doc = await pipeline.parse("example.pdf")
    print(f"总字符: {doc.total_chars}")
    print(f"章节数: {len(doc.sections)}")
```

---

## Capability层使用

### 1. Life场景意图识别

```python
from ame.capability.life import LifeIntentRecognizer

recognizer = LifeIntentRecognizer()

# 识别意图
result = recognizer.recognize_sync("我喜欢什么?")
print(f"意图: {result.intent.value}")
print(f"置信度: {result.confidence}")
```

### 2. Work场景待办解析

```python
from ame.capability.work import TodoParser

parser = TodoParser()

text = """
- [ ] 修复bug
- [ ] 实现新功能
TODO: 更新文档
"""

# 解析待办
todos = parser._parse_by_rules(text)
for todo in todos:
    print(f"{todo.title} (优先级: {todo.priority.value})")
```

### 3. 文档解析

```python
from ame.capability.work import DocumentParser

parser = DocumentParser()

# 解析文档
result = await parser.parse(
    "design.pdf",
    extract_entities=True,
    extract_outline=True
)

print(f"提取到 {len(result.entities)} 个实体")
print(f"大纲层级: {len(result.outline)}")
```

### 4. 使用CapabilityFactory

```python
from ame.capability.factory import CapabilityFactory

factory = CapabilityFactory()

# 创建LLM能力
llm = factory.create_llm_caller(
    api_key="your-api-key",
    model="gpt-3.5-turbo"
)

# 创建Work能力包
work_capabilities = factory.create_work_capability_package(
    llm_api_key="your-api-key",
    graph_host="localhost",
    graph_port=6379
)

# 使用能力
document_parser = work_capabilities["document_parser"]
todo_parser = work_capabilities["todo_parser"]
```

---

## Service层使用

### 1. Work项目服务

```python
from ame.service.work import WorkProjectService
from ame.capability.factory import CapabilityFactory

factory = CapabilityFactory()

service = WorkProjectService(
    capability_factory=factory,
    llm_api_key="your-api-key"
)

# 分析项目
result = await service.analyze_project(
    user_id="user123",
    doc_paths=["design.pdf", "api.md"],
    project_name="MyProject"
)

print(result.markdown_content)
```

### 2. Work待办服务

```python
from ame.service.work import WorkTodoService

service = WorkTodoService(
    capability_factory=factory,
    llm_api_key="your-api-key"
)

# 生成待办
todos = await service.generate_todos(
    user_id="user123",
    new_info="需要修复登录bug和实现新功能"
)

# 更新状态
await service.update_todo_status(
    user_id="user123",
    task_id="task_001",
    new_status="completed"
)
```

---

## 完整示例

### 示例1: 生活场景对话

```python
import asyncio
from ame.capability.factory import CapabilityFactory
from ame.capability.life import LifeIntentRecognizer, DialogueGenerator

async def life_chat_example():
    factory = CapabilityFactory()
    
    # 创建能力
    llm = factory.create_llm_caller(api_key="your-api-key")
    recognizer = LifeIntentRecognizer(llm_caller=llm)
    generator = DialogueGenerator(llm_caller=llm)
    
    # 识别意图
    user_input = "我最近心情不太好"
    result = await recognizer.recognize(user_input)
    print(f"识别意图: {result.intent.value}")
    
    # 生成回复
    reply = await generator.generate(
        user_input=user_input,
        intent=result.intent,
        contexts=[]
    )
    print(f"回复: {reply}")

asyncio.run(life_chat_example())
```

### 示例2: 工作场景待办管理

```python
import asyncio
from ame.capability.factory import CapabilityFactory
from ame.capability.work import TodoParser

async def todo_management_example():
    factory = CapabilityFactory()
    
    # 创建能力
    llm = factory.create_llm_caller(api_key="your-api-key")
    parser = TodoParser(llm_caller=llm)
    
    # 解析待办
    text = """
    本周任务:
    - [ ] 紧急: 修复登录bug (今天)
    - [ ] 实现用户认证功能
    - [ ] 更新API文档
    """
    
    todos = await parser.parse(text, use_llm=True)
    
    for todo in todos:
        print(f"[{todo.priority.value}] {todo.title}")
        if todo.due_date:
            print(f"  截止: {todo.due_date.date()}")

asyncio.run(todo_management_example())
```

### 示例3: 项目文档分析

```python
import asyncio
from ame.service.work import WorkProjectService
from ame.capability.factory import CapabilityFactory

async def project_analysis_example():
    factory = CapabilityFactory()
    
    service = WorkProjectService(
        capability_factory=factory,
        llm_api_key="your-api-key"
    )
    
    # 分析项目
    result = await service.analyze_project(
        user_id="developer",
        doc_paths=["architecture.md", "design.pdf"],
        project_name="AME模块",
        user_prompt="重点分析架构设计"
    )
    
    # 输出Markdown报告
    print(result.markdown_content)
    
    # 输出实体
    print(f"\n提取到 {len(result.entities)} 个实体:")
    for entity in result.entities[:10]:
        print(f"  - {entity.text} ({entity.type.value})")

asyncio.run(project_analysis_example())
```

---

## 常见问题

### Q1: 如何处理长对话历史?

使用HistoryManager:
```python
from ame.foundation.llm import HistoryManager, CompressionStrategy

manager = HistoryManager(llm_caller=llm)
managed = manager.manage(
    messages=long_history,
    strategy=CompressionStrategy.SLIDING_WINDOW,
    window_size=5
)
```

### Q2: 如何自定义意图识别?

```python
recognizer = LifeIntentRecognizer()
recognizer.register_custom_intent(
    intent_name="book_query",
    patterns=[r"推荐.*?书", r"什么.*?书"]
)
```

### Q3: 如何解析不同格式的文档?

DocumentPipeline会自动识别格式:
```python
pipeline = DocumentParsePipeline()
doc = await pipeline.parse("document.pdf")  # 自动识别为PDF
```

### Q4: 如何提高待办解析准确率?

1. 使用标准格式(checkbox/TODO/数字列表)
2. 明确标注优先级关键词
3. 启用LLM增强: `use_llm=True`

---

**更新时间**: 2024年11月  
**版本**: 1.0
