# 文档解析模块 (file)

Foundation 层的文档解析模块，采用三层架构设计，提供统一的文档解析接口。

## 📐 架构设计

遵循 LLM 模块的架构规范，分为三层：

```
foundation/file/
├── core/              # 核心层
│   ├── models.py      # 数据模型定义
│   ├── exceptions.py  # 异常定义
│   └── __init__.py
├── atomic/            # 原子层
│   ├── base.py        # 解析器基类
│   ├── text_parser.py       # TXT 解析器
│   ├── markdown_parser.py   # Markdown 解析器
│   ├── pdf_parser.py        # PDF 解析器
│   ├── docx_parser.py       # DOCX 解析器
│   └── __init__.py
├── pipeline/          # 管道层
│   ├── document_pipeline.py # 文档解析管道
│   └── __init__.py
├── __init__.py        # 模块导出
└── README.md          # 本文档
```

### 分层职责

#### 1. Core 层（核心层）
- **数据模型** (`models.py`)
  - `DocumentFormat`: 文档格式枚举
  - `SectionType`: 章节类型枚举
  - `DocumentSection`: 文档章节数据类
  - `ParsedDocument`: 解析结果数据类

- **异常定义** (`exceptions.py`)
  - `FileParserError`: 基础异常
  - `UnsupportedFormatError`: 不支持的格式
  - `ParseError`: 解析错误
  - `DependencyMissingError`: 依赖缺失

#### 2. Atomic 层（原子层）
独立的解析器实现，每个解析器负责一种文档格式：

- **基类** (`base.py`)
  - `FileParserBase`: 定义统一的解析器接口

- **具体解析器**
  - `TextParser`: 纯文本解析（txt, text, log）
  - `MarkdownParser`: Markdown解析（md, markdown, mdown, mkd）
  - `PDFParser`: PDF解析（pdf）支持 PyPDF2 和 pdfplumber
  - `DocxParser`: Word文档解析（docx）

#### 3. Pipeline 层（管道层）
- **DocumentParsePipeline** (`document_pipeline.py`)
  - 自动格式识别
  - 解析器选择和调度
  - 批量处理支持
  - 自定义解析器注册

## 🚀 快速使用

### 基础使用

```python
from ame.foundation.file import parse_document

# 使用便捷函数解析文档
doc = await parse_document("example.pdf")

# 访问解析结果
print(doc.raw_content)        # 原始文本
print(doc.get_outline())      # 文档大纲
print(doc.total_chars)        # 字符数
print(len(doc.sections))      # 章节数
```

### 使用管道

```python
from ame.foundation.file import DocumentParsePipeline

# 创建管道
pipeline = DocumentParsePipeline()

# 解析单个文档
doc = await pipeline.parse("document.md")

# 批量解析
docs = await pipeline.batch_parse([
    "file1.txt",
    "file2.md",
    "file3.pdf"
])

# 查看支持的格式
formats = pipeline.get_supported_formats()
```

### 访问结构化内容

```python
from ame.foundation.file import SectionType

# 获取所有标题
headings = doc.get_headings()
for h in headings:
    print(f"{'  ' * (h.level - 1)}{h.content}")

# 获取特定级别标题
h1_list = doc.get_headings(level=1)

# 获取段落
paragraphs = doc.get_paragraphs()

# 获取特定类型章节
code_blocks = doc.get_sections_by_type(SectionType.CODE_BLOCK)
tables = doc.get_sections_by_type(SectionType.TABLE)

# 转换为字典（可JSON序列化）
doc_dict = doc.to_dict()
```

### 自定义解析器

```python
from ame.foundation.file import FileParserBase, DocumentParsePipeline
from ame.foundation.file.core import ParsedDocument, DocumentFormat

class CustomParser(FileParserBase):
    """自定义解析器"""
    
    SUPPORTED_EXTENSIONS = {"custom"}
    
    def can_parse(self, file_path: str) -> bool:
        return self._get_file_extension(file_path) == "custom"
    
    async def parse(self, file_path: str) -> ParsedDocument:
        # 实现自定义解析逻辑
        pass

# 注册到管道
pipeline = DocumentParsePipeline()
pipeline.register_parser(CustomParser())
```

## 📦 数据模型

### ParsedDocument

```python
@dataclass
class ParsedDocument:
    format: DocumentFormat              # 文档格式
    file_path: str                      # 文件路径
    raw_content: str                    # 原始文本
    sections: List[DocumentSection]     # 结构化章节
    metadata: Dict[str, Any]            # 元数据
    total_chars: int                    # 总字符数
    total_words: int                    # 总词数
    total_pages: Optional[int]          # 总页数
    parsed_at: datetime                 # 解析时间
    
    # 便捷方法
    def get_headings(level=None) -> List[DocumentSection]
    def get_paragraphs() -> List[DocumentSection]
    def get_sections_by_type(section_type) -> List[DocumentSection]
    def get_outline() -> str
    def to_dict() -> Dict[str, Any]
```

### DocumentSection

```python
@dataclass
class DocumentSection:
    type: SectionType                   # 章节类型
    content: str                        # 章节内容
    level: int                          # 层级
    metadata: Dict[str, Any]            # 元数据
    start_position: Optional[int]       # 起始位置
    end_position: Optional[int]         # 结束位置
    page_number: Optional[int]          # 页码（PDF）
    line_number: Optional[int]          # 行号
```

## 🔧 依赖安装

### 基础功能（TXT、Markdown）
无需额外依赖

### PDF 解析
```bash
# 推荐使用 PyPDF2
pip install PyPDF2

# 或使用 pdfplumber（质量更高，支持表格）
pip install pdfplumber
```

### DOCX 解析
```bash
pip install python-docx
```

## 🎯 设计原则

1. **分层解耦**: Core、Atomic、Pipeline 三层职责清晰
2. **单一职责**: 每个解析器只负责一种格式
3. **开闭原则**: 通过继承 FileParserBase 扩展新格式
4. **统一接口**: 所有解析器返回统一的 ParsedDocument
5. **异常规范**: 使用自定义异常类型，便于错误处理

## 📝 使用示例

完整示例请查看：`ame/docs/examples/08_file_parsing.py`

## ⚠️ 注意事项

1. **PDF 质量**: 扫描版 PDF 可能无法提取文本
2. **编码问题**: TXT 文件建议使用 UTF-8 编码
3. **异步处理**: 所有解析方法均为异步，需使用 `await`
4. **依赖检查**: 使用 PDF/DOCX 前需安装相应库
5. **内存占用**: 大文件解析可能占用较多内存

## 🛠️ 扩展建议

- [ ] HTML 文档解析器
- [ ] Excel 文件解析器
- [ ] 图像 OCR 支持
- [ ] 流式解析（大文件）
- [ ] 解析结果缓存
- [ ] 并发解析优化
