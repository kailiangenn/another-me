# LLM 模块 - 双层架构

> **新架构已上线！** 本模块已重构为双层架构，提供更清晰的职责分离和更强的可扩展性。
> 
> - **推荐使用**: `SessionPipe` (对话) / `DocumentPipe` (文档分析)

## 快速开始

### 1. 对话场景

```python
from ame.foundation.llm import AtomicOpenAICaller, SessionPipe, PipelineContext
from ame.foundation.llm.utils import ConversationMessage

# 创建调用器
caller = AtomicOpenAICaller(api_key="your-key", model="gpt-3.5-turbo")

# 创建会话管道
pipe = SessionPipe(
    caller=caller,
    cache_enabled=True,  # 启用缓存
    keep_recent=5  # 保留最近5轮对话
)

# 准备消息
messages = [
    ConversationMessage(role="system", content="You are a helpful assistant."),
    ConversationMessage(role="user", content="Hello!"),
]

# 调用管道
context = PipelineContext(messages=messages)
result = await pipe.process(context)

print(result.response.content)
print(f"缓存命中: {result.cached}")
```

### 2. 文档分析场景

```python
from ame.foundation.llm import AtomicOpenAICaller, DocumentPipe

caller = AtomicOpenAICaller(api_key="your-key")
pipe = DocumentPipe(caller=caller)

messages = [
    ConversationMessage(role="system", content="You are a document analyzer."),
    ConversationMessage(role="user", content=f"Analyze: {document_text}"),
]

context = PipelineContext(messages=messages)
result = await pipe.process(context)

print(result.response.content)
```

### 3. 流式输出

```python
context = PipelineContext(messages=messages, stream=True)
result = await pipe.process(context)

async for chunk in result.stream_iterator:
    print(chunk, end="", flush=True)
```

## 架构设计

### 双层架构

```
应用层 (Service/Controller)
    │
    ↓
管道层 (Pipeline Layer) - 场景化组合
    ├─ SessionPipe (对话管道)
    │   ├─ CacheStrategy (缓存)
    │   ├─ SessionCompressStrategy (保守压缩)
    │   └─ RetryStrategy (重试)
    │
    └─ DocumentPipe (文档管道)
        ├─ DocumentCompressStrategy (激进压缩)
        └─ RetryStrategy (重试)
    │
    ↓
原子层 (Atomic Layer) - 基础能力
    ├─ Caller (调用器)
    │   ├─ LLMCallerBase (抽象基类)
    │   ├─ OpenAICaller (优化版，tiktoken)
    │   └─ StreamCaller (流式封装)
    │
    └─ Strategy (策略)
        ├─ CacheStrategy (TTLCache)
        ├─ CompressStrategy (压缩)
        └─ RetryStrategy (重试)
```

### 核心优势

| 维度 | 新架构 | 传统架构 |
|------|--------|----------|
| **职责分离** | 原子能力独立、管道组合 | 能力耦合在一起 |
| **Token估算** | tiktoken精确估算 | 简单公式估算 |
| **缓存机制** | TTLCache、自动过期 | 无缓存 |
| **策略插件** | 可插拔 | 耦合在类中 |
| **扩展性** | 高 | 中 |
