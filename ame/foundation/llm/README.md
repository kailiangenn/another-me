# LLM 模块 - 双层架构

> **新架构已上线！** 本模块已重构为双层架构，提供更清晰的职责分离和更强的可扩展性。
> 
> - **推荐使用**: `SessionPipe` (对话) / `DocumentPipe` (文档分析)
> - **传统 API**: 仍然可用，但建议迁移到新架构
> - **迁移指南**: 见 [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

## 快速开始（新架构）

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

---

# 传统 API文档（向后兼容）

## 核心理念

**文档分块分析 = 系统驱动的多轮对话**

无论是用户主动的多轮对话（SESSION 模式），还是系统自动的长文档分析（DOCUMENT 模式），本质上都是在管理**对话历史**，只是驱动方式和压缩策略不同。

## 架构设计

```
ConversationHistory (对话历史管理)
        │
        ├── CompressionStrategy (压缩策略)
        │   ├── SessionCompressionStrategy (会话模式：保守压缩)
        │   ├── DocumentCompressionStrategy (文档模式：激进压缩)
        │   └── ChunkingCompressionStrategy (分块模式：超长文本)
        │
        └── ChunkedConversationManager (分块对话管理)
            └── 基于 ConversationHistory 实现长文档渐进式处理
```

## 使用场景

### 场景 1: 普通多轮对话（SESSION 模式）

```python
from foundation.llm import OpenAICaller, ContextMode

# 创建 LLM 调用器
llm = OpenAICaller(
    api_key="your-api-key",
    max_context_tokens=4000
)

# 创建会话对话
conversation = llm.create_conversation(
    system_prompt="你是一个友好的助手",
    mode=ContextMode.SESSION  # 会话模式
)

# 多轮对话
response1 = await llm.chat_with_history(
    conversation,
    "你好，今天天气怎么样？"
)

response2 = await llm.chat_with_history(
    conversation,
    "推荐一些户外活动",
    important=True  # 标记为重要消息（压缩时优先保留）
)

# 对话结束时，导出关键信息到图谱
export_data = conversation.clear_and_export()
# ✅ 导出 important=True 的消息 + 最近5轮对话
```

### 场景 2: 长文档分析（DOCUMENT 模式 + 分块）

```python
from foundation.llm import (
    OpenAICaller,
    ContextMode,
    ChunkedConversationManager
)

# 创建 LLM 调用器
llm = OpenAICaller(api_key="your-api-key")

# 创建文档分析对话
doc_conversation = llm.create_conversation(
    system_prompt="你是一个专业的文档分析助手",
    mode=ContextMode.DOCUMENT  # 文档模式：静默压缩
)

# 创建分块管理器
chunker = ChunkedConversationManager(
    conversation=doc_conversation,
    chunk_size=2000,      # 每块 2000 tokens
    chunk_overlap=200     # 重叠 200 tokens（保持连贯性）
)

# 分块长文档
long_document = "..." # 10000+ tokens
chunks = chunker.split_into_chunks(long_document, llm.estimate_tokens)

# 逐块分析
async def generate_fn(messages):
    return await llm.generate(messages)

def on_chunk_done(result):
    print(f"✅ 完成第 {result.chunk_index + 1}/{result.total_chunks} 块分析")
    print(f"进度: {chunker.get_progress()['progress_percentage']:.1f}%")

# 处理所有块
results = await chunker.process_all_chunks(
    llm_generate_fn=generate_fn,
    on_chunk_complete=on_chunk_done
)

# 生成最终总结
summary = await chunker.generate_final_summary(generate_fn)

# 导出分析报告
report = chunker.export_analysis_report()
# ✅ 导出所有 LLM 分析结果 + 最终总结
```

### 场景 3: 流式长文档分析（用户可见进度）

```python
from foundation.llm import ChunkedConversationManager, ContextMode

async def stream_document_analysis(document: str):
    """流式展示文档分析过程"""
    
    # 创建文档对话和分块管理器
    llm = OpenAICaller(api_key="your-api-key")
    conversation = llm.create_conversation(mode=ContextMode.DOCUMENT)
    chunker = ChunkedConversationManager(conversation, chunk_size=2000)
    
    # 分块
    chunks = chunker.split_into_chunks(document, llm.estimate_tokens)
    
    # 逐块流式分析
    for i in range(len(chunks)):
        print(f"\n📄 正在分析第 {i+1}/{len(chunks)} 块...")
        
        # 流式生成
        full_response = ""
        async for chunk_text in llm.generate_stream(
            conversation.get_messages() + [
                {"role": "user", "content": chunks[i]}
            ]
        ):
            print(chunk_text, end="", flush=True)
            full_response += chunk_text
        
        # 手动添加到历史
        conversation.add_message("user", chunks[i])
        conversation.add_message("assistant", full_response)
        
        # 自动压缩（静默）
        conversation.compress_if_needed(llm.estimate_tokens)
        
        print(f"\n✅ 第 {i+1} 块分析完成")
    
    # 最终总结
    print("\n📊 正在生成最终总结...")
    conversation.add_message("user", "请总结上述所有分析", important=True)
    
    summary = ""
    async for chunk in llm.generate_stream(conversation.get_messages()):
        print(chunk, end="", flush=True)
        summary += chunk
    
    conversation.add_message("assistant", summary, important=True)
    
    # 导出
    return conversation.export_important()
```

### 场景 4: 自定义压缩策略

```python
from foundation.llm import (
    CompressionStrategy,
    ChunkingCompressionStrategy,
    ContextMode
)

# 使用分块压缩策略处理超长消息
chunking_strategy = ChunkingCompressionStrategy(chunk_size=3000)

conversation = llm.create_conversation(
    mode=ContextMode.DOCUMENT,
    compression_strategy=chunking_strategy  # 自定义策略
)

# 或者组合多个策略
class HybridCompressionStrategy(CompressionStrategy):
    """混合策略：先尝试分块，再尝试压缩"""
    
    def __init__(self):
        self.chunking = ChunkingCompressionStrategy(chunk_size=2000)
        self.document = DocumentCompressionStrategy()
    
    def should_compress(self, messages, max_tokens, token_estimator):
        # 先检查是否有超长消息
        if self.chunking.should_compress(messages, max_tokens, token_estimator):
            return True
        # 再检查总量是否超限
        return self.document.should_compress(messages, max_tokens, token_estimator)
    
    def compress(self, messages, max_tokens, token_estimator):
        # 先分块
        if self.chunking.should_compress(messages, max_tokens, token_estimator):
            kept, removed = self.chunking.compress(messages, max_tokens, token_estimator)
            messages = kept
        
        # 再压缩
        if self.document.should_compress(messages, max_tokens, token_estimator):
            return self.document.compress(messages, max_tokens, token_estimator)
        
        return messages, []
    
    def on_compression(self, removed_count, total_tokens, compressed_tokens):
        logger.info(f"混合压缩完成：移除 {removed_count} 条，{total_tokens} → {compressed_tokens} tokens")
```

## 压缩策略对比

| 策略 | 触发阈值 | 保留优先级 | 日志级别 | 适用场景 |
|------|---------|----------|---------|---------|
| **SessionCompressionStrategy** | 95% | System > Important > Recent(5轮) > Old | WARNING | 用户对话 |
| **DocumentCompressionStrategy** | 80% | System > Latest User > Latest AI > Old AI | DEBUG | 文档分析 |
| **ChunkingCompressionStrategy** | 单条>70% | 分块保留所有内容 | INFO | 超长文本 |

## 导出策略对比

### SESSION 模式导出

```python
export_data = conversation.export_important()

# 返回格式：
{
    "mode": "session",
    "total_conversations": 50,
    "important_count": 5,
    "export_content": [
        {
            "role": "user",
            "content": "...",
            "timestamp": "2024-01-01T10:00:00",
            "important": True
        },
        # ... 最近5轮对话 ...
    ]
}
```

### DOCUMENT 模式导出

```python
export_data = doc_conversation.export_important()

# 返回格式：
{
    "mode": "document",
    "total_messages": 30,
    "analysis_count": 15,
    "export_content": {
        "llm_analysis": [
            {
                "content": "分析结果1...",
                "timestamp": "2024-01-01T10:00:00"
            },
            # ... 所有 AI 分析结果 ...
        ],
        "important_inputs": [
            {
                "content": "重要文档片段...",
                "timestamp": "2024-01-01T09:00:00"
            }
        ]
    }
}
```

## API 参考

### ConversationHistory

```python
conversation = ConversationHistory(
    max_context_tokens=4000,           # 最大上下文 token 数
    mode=ContextMode.SESSION,          # 模式：SESSION | DOCUMENT
    compression_strategy=None          # 自定义压缩策略（可选）
)

# 添加消息
conversation.add_message("user", "Hello", important=True)

# 压缩（如果需要）
conversation.compress_if_needed(token_estimator_fn)

# 导出
all_data = conversation.export_all()           # 完整历史（含压缩记录）
important_data = conversation.export_important()  # 关键信息（根据模式）
graph_data = conversation.clear_and_export()   # 清空并导出

# 统计
stats = conversation.get_compression_stats()
```

### ChunkedConversationManager

```python
chunker = ChunkedConversationManager(
    conversation=doc_conversation,
    chunk_size=2000,
    chunk_overlap=200,
    chunking_mode=ChunkingMode.AUTO
)

# 分块
chunks = chunker.split_into_chunks(long_text, token_estimator)

# 处理
result = await chunker.process_chunk(0, llm_generate_fn)
all_results = await chunker.process_all_chunks(llm_generate_fn, on_complete_fn)

# 总结
summary = await chunker.generate_final_summary(llm_generate_fn)

# 导出
report = chunker.export_analysis_report()
progress = chunker.get_progress()
```

## 最佳实践

### 1. 选择合适的模式

- **SESSION 模式**：用户对话、需要保留上下文的场景
- **DOCUMENT 模式**：文档分析、知识提取、不需要保留完整历史

### 2. 标记重要消息

```python
# 会话模式中标记关键对话
await llm.chat_with_history(
    conversation,
    "这个决定很重要，请记住",
    important=True  # 压缩时优先保留
)
```

### 3. 监控压缩统计

```python
stats = conversation.get_compression_stats()
print(f"已压缩 {stats['total_compressions']} 次")
print(f"移除了 {stats['total_messages_removed']} 条消息")
```

### 4. 合理设置 chunk_size

- **小块（1000-1500）**：适合需要细粒度分析的场景
- **中块（2000-3000）**：推荐默认值，平衡准确性和效率
- **大块（4000+）**：适合概览性分析

### 5. 使用 overlap 保持连贯性

```python
chunker = ChunkedConversationManager(
    conversation=doc_conversation,
    chunk_size=2000,
    chunk_overlap=200  # 10% 重叠，避免语义断裂
)
```

## 常见问题

### Q: SESSION 和 DOCUMENT 模式可以互换吗？

A: 可以，但不推荐。两种模式的压缩策略和导出格式不同，切换可能导致行为不一致。

### Q: 如何处理极长文档（100k+ tokens）？

A: 使用 `ChunkedConversationManager`，它会自动分块并静默压缩历史分析结果。

### Q: 压缩后的消息去哪了？

A: 被移除的消息会存储在 `conversation._archived_messages` 中，可以通过 `export_all()` 导出。

### Q: 如何禁用自动压缩？

A: 设置 `max_context_tokens=None`：

```python
conversation = llm.create_conversation(
    mode=ContextMode.SESSION,
    max_context_tokens=None  # 不限制，不压缩
)
```

## 性能建议

1. **启用缓存**（仅限非创造性任务）：
   ```python
   llm = OpenAICaller(cache_enabled=True)
   ```

2. **合理设置 max_context_tokens**：
   - GPT-3.5-turbo: 4000
   - GPT-4: 8000
   - GPT-4-32k: 32000

3. **使用流式输出提升体验**：
   ```python
   async for chunk in llm.chat_stream_with_history(conversation, message):
       print(chunk, end="", flush=True)
   ```

## 更新日志

### v1.0.0 (2024-01)
- ✅ 统一会话模式和文档模式的架构
- ✅ 引入策略模式实现可扩展的压缩策略
- ✅ 实现 ChunkedConversationManager 处理长文档
- ✅ 支持自定义压缩策略
- ✅ 完善的导出机制和统计信息
