# 文档解析模块使用指南

## 模块结构

```
foundation/file/
├── core/              # 核心层：数据模型和异常
├── atomic/            # 原子层：具体解析器实现
└── pipeline/          # 管道层：解析管道和工厂
```

## 快速开始

### 1. 基础导入

```python
from ame.foundation.file import (
    # 管道和便捷函数
    DocumentParsePipeline,
    parse_document,
    
    # 数据模型
    ParsedDocument,
    DocumentSection,
    DocumentFormat,
    SectionType,
    
    # 异常
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
)
```

### 2. 使用便捷函数

```python
# 最简单的方式
doc = await parse_document("example.pdf")
print(doc.raw_content)
```

### 3. 使用管道

```python
# 创建管道（可配置）
pipeline = DocumentParsePipeline(use_pdfplumber=True)

# 单文档解析
doc = await pipeline.parse("document.md")

# 批量解析
docs = await pipeline.batch_parse([
    "file1.txt",
    "file2.md",
    "file3.pdf"
], ignore_errors=True)
```

## 访问解析结果

### 原始内容

```python
doc = await parse_document("example.md")

# 原始文本
content = doc.raw_content

# 基本信息
format = doc.format          # DocumentFormat.MARKDOWN
path = doc.file_path
chars = doc.total_chars
words = doc.total_words
pages = doc.total_pages      # PDF/DOCX 专用
```

### 结构化内容

```python
# 获取所有标题
all_headings = doc.get_headings()

# 获取特定级别标题
h1_list = doc.get_headings(level=1)
h2_list = doc.get_headings(level=2)

# 获取段落
paragraphs = doc.get_paragraphs()

# 获取特定类型章节
code_blocks = doc.get_sections_by_type(SectionType.CODE_BLOCK)
tables = doc.get_sections_by_type(SectionType.TABLE)
quotes = doc.get_sections_by_type(SectionType.QUOTE)
lists = doc.get_sections_by_type(SectionType.LIST_ITEM)
```

### 文档大纲

```python
# 生成大纲（仅标题）
outline = doc.get_outline()
print(outline)

# 输出示例：
# - 一级标题
#   - 二级标题
#     - 三级标题
```

### 章节详情

```python
# 遍历所有章节
for section in doc.sections:
    print(f"类型: {section.type}")
    print(f"内容: {section.content}")
    print(f"级别: {section.level}")
    print(f"页码: {section.page_number}")
    print(f"行号: {section.line_number}")
    print(f"元数据: {section.metadata}")
```

### 转换为字典

```python
# 转换为字典（可 JSON 序列化）
doc_dict = doc.to_dict()

# 保存为 JSON
import json
with open("parsed_doc.json", "w", encoding="utf-8") as f:
    json.dump(doc_dict, f, ensure_ascii=False, indent=2)
```

## 高级用法

### 自定义解析器

```python
from ame.foundation.file.atomic import FileParserBase
from ame.foundation.file.core import (
    ParsedDocument,
    DocumentSection,
    DocumentFormat,
    SectionType,
)

class CustomParser(FileParserBase):
    """自定义解析器"""
    
    SUPPORTED_EXTENSIONS = {"custom", "cst"}
    
    def can_parse(self, file_path: str) -> bool:
        ext = self._get_file_extension(file_path)
        return ext in self.SUPPORTED_EXTENSIONS
    
    async def parse(self, file_path: str) -> ParsedDocument:
        # 验证文件
        path = self._validate_file_exists(file_path)
        
        # 读取内容
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 解析章节
        sections = []
        for line in content.split("\n"):
            if line.strip():
                sections.append(DocumentSection(
                    type=SectionType.PARAGRAPH,
                    content=line.strip()
                ))
        
        # 返回结果
        return ParsedDocument(
            format=DocumentFormat.UNKNOWN,
            file_path=str(path),
            raw_content=content,
            sections=sections
        )

# 注册到管道
pipeline = DocumentParsePipeline()
pipeline.register_parser(CustomParser())

# 使用
doc = await pipeline.parse("file.custom")
```

### 指定解析器

```python
# 强制使用特定解析器
doc = await pipeline.parse(
    "file.txt",
    parser_name="MarkdownParser"  # 按解析器类名指定
)
```

### 查看支持的格式

```python
pipeline = DocumentParsePipeline()

# 获取所有支持的格式
formats = pipeline.get_supported_formats()
print(formats)
# {
#     'MarkdownParser': ['md', 'markdown', 'mdown', 'mkd'],
#     'PDFParser': ['pdf'],
#     'DocxParser': ['docx'],
#     'TextParser': ['txt', 'text', 'log']
# }

# 检查是否支持某个文件
is_supported = pipeline.is_supported("example.pdf")  # True
```

## 异常处理

```python
from ame.foundation.file import (
    FileParserError,
    UnsupportedFormatError,
    ParseError,
    DependencyMissingError,
)

try:
    doc = await parse_document("file.xyz")
except FileNotFoundError as e:
    print("文件不存在")
except UnsupportedFormatError as e:
    print(f"不支持的格式: {e.format}")
except DependencyMissingError as e:
    print(f"缺少依赖: {e.dependency}")
    print(f"安装命令: {e.install_command}")
except ParseError as e:
    print(f"解析失败: {e.file_path}")
    print(f"原因: {e.reason}")
except FileParserError as e:
    print(f"解析错误: {e}")
```

## 实际应用场景

### 1. 文档知识库构建

```python
from ame.foundation.file import parse_document, SectionType

# 解析文档
doc = await parse_document("knowledge.pdf")

# 按段落分块存储
chunks = []
for section in doc.sections:
    if section.type == SectionType.PARAGRAPH:
        chunks.append({
            "content": section.content,
            "metadata": {
                "source": doc.file_path,
                "page": section.page_number,
                "type": section.type.value
            }
        })

# 存储到向量数据库
# await vector_store.add_documents(chunks)
```

### 2. 批量文档处理

```python
from pathlib import Path
from ame.foundation.file import DocumentParsePipeline

# 扫描目录
docs_dir = Path("./documents")
file_paths = [str(f) for f in docs_dir.rglob("*") if f.is_file()]

# 批量解析
pipeline = DocumentParsePipeline()
docs = await pipeline.batch_parse(file_paths, ignore_errors=True)

# 统计分析
total_chars = sum(doc.total_chars for doc in docs)
total_files = len(docs)
print(f"共解析 {total_files} 个文档，总字符数: {total_chars}")
```

### 3. 文档内容分析

```python
doc = await parse_document("report.docx")

# 生成统计信息
stats = {
    "字符数": doc.total_chars,
    "词数": doc.total_words,
    "页数": doc.total_pages,
    "段落数": len(doc.get_paragraphs()),
    "标题数": len(doc.get_headings()),
    "代码块数": len(doc.get_sections_by_type(SectionType.CODE_BLOCK)),
    "表格数": len(doc.get_sections_by_type(SectionType.TABLE)),
}

print(stats)
```

## 性能优化建议

1. **批量处理**: 使用 `batch_parse()` 而不是循环调用 `parse()`
2. **忽略错误**: 批量处理时设置 `ignore_errors=True` 避免中断
3. **选择合适的 PDF 引擎**: pdfplumber 质量更高但速度稍慢
4. **内存管理**: 处理大文件时注意及时释放 `ParsedDocument` 对象

## 常见问题

### Q: PDF 解析不出内容？
A: 可能是扫描版 PDF，需要 OCR 处理。或尝试切换 PDF 引擎：
```python
pipeline = DocumentParsePipeline(use_pdfplumber=True)
```

### Q: 如何处理中文编码问题？
A: TextParser 会自动尝试多种编码（utf-8, gbk, gb2312 等）

### Q: 如何获取 PDF 的页码信息？
A: 访问 `section.page_number` 属性：
```python
for section in doc.sections:
    if section.page_number:
        print(f"第 {section.page_number} 页: {section.content[:50]}")
```

### Q: 如何提取 Markdown 的代码块？
A: 使用类型过滤：
```python
code_blocks = doc.get_sections_by_type(SectionType.CODE_BLOCK)
for block in code_blocks:
    print(block.content)
```
