# AME模块 API参考文档

> **版本**: 1.0  
> **更新时间**: 2024年11月

---

## 目录

1. [Foundation Layer API](#foundation-layer-api)
2. [Capability Layer API](#capability-layer-api)
3. [Service Layer API](#service-layer-api)
4. [工具函数API](#工具函数api)

---

## Foundation Layer API

### LLM模块

#### OpenAICaller

LLM调用器,支持同步和流式生成。

```python
class OpenAICaller(LLMCallerBase):
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    )
```

**参数**:
- `api_key`: OpenAI API密钥
- `model`: 模型名称
- `base_url`: API基础URL(可选)
- `temperature`: 温度参数(0-2)

**方法**:

##### generate()
```python
async def generate(
    self,
    messages: List[Dict[str, str]],
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> LLMResponse
```

生成回复。

**参数**:
- `messages`: 消息列表
- `max_tokens`: 最大token数
- `temperature`: 温度参数

**返回**: `LLMResponse`对象

##### generate_stream()
```python
async def generate_stream(
    self,
    messages: List[Dict[str, str]],
    **kwargs
) -> AsyncIterator[str]
```

流式生成回复。

**返回**: 异步迭代器

#### PromptBuilder

提示词构建器。

```python
class PromptBuilder:
    def build(
        self,
        template: str,
        variables: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str
```

**方法**:

##### build()
构建基础提示词。

##### build_with_history()
```python
def build_with_history(
    self,
    template: str,
    history: List[Dict],
    max_history_messages: int = 10
) -> str
```

构建带历史的提示词。

##### build_few_shot()
```python
def build_few_shot(
    self,
    task_description: str,
    examples: List[Dict],
    query: str
) -> str
```

构建Few-shot提示词。

##### build_messages_with_history()
```python
def build_messages_with_history(
    self,
    user_message: str,
    history: List[Dict],
    system_prompt: Optional[str] = None
) -> List[Dict]
```

构建完整消息列表。

#### HistoryManager

对话历史管理器。

```python
class HistoryManager:
    def __init__(
        self,
        llm_caller: Optional[LLMCallerBase] = None,
        max_length: int = 4000
    )
```

**方法**:

##### manage()
```python
def manage(
    self,
    messages: List[Dict],
    strategy: CompressionStrategy,
    max_messages: Optional[int] = None,
    keep_system: bool = True,
    **kwargs
) -> List[Dict]
```

管理对话历史。

**参数**:
- `messages`: 消息列表
- `strategy`: 压缩策略(TRUNCATE/SUMMARIZE/SLIDING_WINDOW/IMPORTANCE)
- `max_messages`: 最大消息数
- `keep_system`: 是否保留系统消息

**策略说明**:
- `TRUNCATE`: 截断保留最新N条
- `SUMMARIZE`: LLM压缩为摘要
- `SLIDING_WINDOW`: 滑动窗口(保留开头+结尾)
- `IMPORTANCE`: 基于重要性评分

### Embedding模块

#### SimpleEmbedding

简单的Embedding实现,无外部依赖。

```python
class SimpleEmbedding(EmbeddingBase):
    def __init__(self, dimension: int = 128)
```

**方法**:

##### embed_text()
```python
def embed_text(self, text: str) -> EmbeddingResult
```

文本向量化(单条)。

**返回**: `EmbeddingResult(embedding, metadata)`

##### embed_batch()
```python
def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]
```

批量文本向量化。

##### cosine_similarity()
```python
def cosine_similarity(
    self,
    vec1: List[float],
    vec2: List[float]
) -> float
```

计算余弦相似度。

**返回**: 相似度值(0-1)

### File模块

#### DocumentParsePipeline

文档解析管道,自动识别格式。

```python
class DocumentParsePipeline:
    def __init__(self, use_pdfplumber: bool = False)
```

**方法**:

##### parse()
```python
async def parse(
    self,
    file_path: str,
    parser_name: Optional[str] = None
) -> ParsedDocument
```

解析文档。

**参数**:
- `file_path`: 文件路径
- `parser_name`: 指定解析器(可选)

**返回**: `ParsedDocument`对象

##### batch_parse()
```python
async def batch_parse(
    self,
    file_paths: List[str],
    ignore_errors: bool = True
) -> List[ParsedDocument]
```

批量解析文档。

##### get_supported_formats()
```python
def get_supported_formats(self) -> Dict[str, List[str]]
```

获取支持的文件格式。

**返回**: `{解析器名称: [扩展名列表]}`

---

## Capability Layer API

### Life场景

#### LifeIntentRecognizer

Life场景意图识别器。

```python
class LifeIntentRecognizer:
    def __init__(self, llm_caller: Optional[LLMCallerBase] = None)
```

**方法**:

##### recognize()
```python
async def recognize(
    self,
    text: str,
    use_llm: bool = True,
    context: Optional[List[str]] = None
) -> IntentResult
```

识别意图(规则+LLM)。

**返回**: `IntentResult(intent, confidence, keywords, metadata)`

##### recognize_sync()
```python
def recognize_sync(self, text: str) -> IntentResult
```

同步识别(仅规则)。

##### register_custom_intent()
```python
def register_custom_intent(
    self,
    intent_name: str,
    patterns: List[str],
    replace: bool = False
)
```

注册自定义意图。

**支持的意图类型**:
- `query_self`: 查询自我信息
- `comfort`: 安慰倾诉
- `analyze`: 分析请求
- `chat`: 普通聊天
- `share_emotion`: 情绪分享(自定义)
- `recall_memory`: 回忆记忆(自定义)

#### DialogueGenerator

对话生成器。

```python
class DialogueGenerator:
    def __init__(self, llm_caller: LLMCallerBase)
```

**方法**:

##### generate()
```python
async def generate(
    self,
    user_input: str,
    intent: IntentType = IntentType.CHAT,
    contexts: Optional[List[Dict]] = None,
    conversation_history: Optional[List[Dict]] = None,
    **kwargs
) -> str
```

生成对话回复。

##### generate_stream()
```python
async def generate_stream(...) -> AsyncIterator[str]
```

流式生成回复。

### Work场景

#### DocumentParser

文档解析器(Capability层封装)。

```python
class DocumentParser:
    def __init__(
        self,
        use_pdfplumber: bool = False,
        entity_extractor: Optional[EntityExtractor] = None
    )
```

**方法**:

##### parse()
```python
async def parse(
    self,
    file_path: str,
    extract_entities: bool = True,
    extract_outline: bool = True
) -> DocumentParseResult
```

解析文档并提取结构化信息。

**返回**: `DocumentParseResult`对象

#### TodoParser

待办解析器。

```python
class TodoParser:
    def __init__(self, llm_caller: Optional[LLMCallerBase] = None)
```

**方法**:

##### parse()
```python
async def parse(
    self,
    text: str,
    use_llm: bool = True,
    existing_task_ids: Optional[List[str]] = None
) -> List[TodoItem]
```

从文本解析待办事项。

**支持格式**:
- `- [ ] 任务`: Checkbox格式
- `TODO: 任务`: TODO格式
- `1. 任务`: 数字列表
- `- 任务`: Dash格式

**自动识别**:
- 优先级: 紧急/重要/普通
- 截止日期: 今天/明天/本周/YYYY-MM-DD

#### PatternAnalyzer

工作模式分析器。

```python
class PatternAnalyzer:
    def __init__(self, graph_store: GraphStoreBase)
```

**方法**:

##### analyze()
```python
async def analyze(
    self,
    user_id: str,
    days: int = 30,
    min_tasks: int = 5
) -> PatternAnalysisReport
```

分析用户工作模式。

**分析维度**:
- 时间模式: 工作时段偏好
- 优先级模式: 优先级分布
- 完成模式: 完成率和平均时长
- 拖延模式: 逾期任务识别

**返回**: `PatternAnalysisReport`对象

### CapabilityFactory

能力工厂,统一管理所有能力。

```python
class CapabilityFactory:
    def __init__(self)
```

**核心方法**:

##### create_llm_caller()
```python
def create_llm_caller(
    self,
    api_key: str,
    model: str = "gpt-3.5-turbo",
    cache_key: Optional[str] = None
) -> LLMCallerBase
```

##### create_work_capability_package()
```python
def create_work_capability_package(
    self,
    llm_api_key: str,
    graph_host: str = "localhost",
    cache_prefix: str = "work"
) -> Dict[str, Any]
```

创建Work能力包(包含6个能力)。

**返回能力**:
- `document_parser`: 文档解析器
- `todo_parser`: 待办解析器
- `project_analyzer`: 项目分析器
- `todo_manager`: 待办管理器
- `pattern_analyzer`: 模式分析器
- `advice_generator`: 建议生成器

---

## Service Layer API

### WorkProjectService

项目认知服务。

```python
class WorkProjectService:
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        llm_api_key: str
    )
```

**方法**:

##### analyze_project()
```python
async def analyze_project(
    self,
    user_id: str,
    doc_paths: List[str],
    project_name: str,
    user_prompt: Optional[str] = None
) -> ProjectAnalysisResult
```

分析项目文档,生成Markdown报告。

### WorkTodoService

待办管理服务。

```python
class WorkTodoService:
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        llm_api_key: str,
        graph_host: str = "localhost"
    )
```

**方法**:

##### generate_todos()
```python
async def generate_todos(
    self,
    user_id: str,
    new_info: str,
    project_name: Optional[str] = None
) -> SortedTodoList
```

生成并排序待办。

##### update_todo_status()
```python
async def update_todo_status(
    self,
    user_id: str,
    task_id: str,
    new_status: str
) -> bool
```

更新待办状态。

**状态值**: `pending`, `in_progress`, `completed`

### WorkAdviceService

工作建议服务。

```python
class WorkAdviceService:
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        llm_api_key: str,
        graph_host: str = "localhost"
    )
```

**方法**:

##### generate_advice()
```python
async def generate_advice(
    self,
    user_id: str,
    time_range: Optional[TimeRange] = None
) -> AdviceReport
```

生成工作建议报告。

##### generate_weekly_advice()
```python
async def generate_weekly_advice(self, user_id: str) -> AdviceReport
```

生成周报建议(最近7天)。

##### generate_monthly_advice()
```python
async def generate_monthly_advice(self, user_id: str) -> AdviceReport
```

生成月报建议(最近30天)。

---

## 工具函数API

### 辅助函数

#### create_system_message()
```python
def create_system_message(content: str) -> Dict[str, str]
```

创建系统消息。

#### create_user_message()
```python
def create_user_message(content: str) -> Dict[str, str]
```

创建用户消息。

#### create_assistant_message()
```python
def create_assistant_message(content: str) -> Dict[str, str]
```

创建助手消息。

---

## 数据模型

### IntentResult
```python
@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    keywords: List[str]
    metadata: Dict[str, Any]
```

### TodoItem
```python
@dataclass
class TodoItem:
    id: str
    title: str
    description: str
    priority: Priority
    status: TaskStatus
    due_date: Optional[datetime]
    dependencies: List[str]
    created_at: datetime
```

### ParsedDocument
```python
@dataclass
class ParsedDocument:
    format: DocumentFormat
    file_path: str
    raw_content: str
    sections: List[DocumentSection]
    total_chars: int
    total_pages: Optional[int]
    metadata: Dict[str, Any]
```

---

## 枚举类型

### IntentType
```python
class IntentType(Enum):
    QUERY_SELF = "query_self"
    COMFORT = "comfort"
    ANALYZE = "analyze"
    CHAT = "chat"
    CUSTOM = "custom"
    UNKNOWN = "unknown"
```

### Priority
```python
class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
```

### TaskStatus
```python
class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

### CompressionStrategy
```python
class CompressionStrategy(Enum):
    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"
    SLIDING_WINDOW = "sliding"
    IMPORTANCE = "importance"
```

---

**文档版本**: 1.0  
**最后更新**: 2024年11月21日  
**维护者**: AME开发团队
