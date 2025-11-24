# File模块 - 文档解析与Markdown转换

## 📚 概述

File模块是AME Foundation层的核心组件，负责将各种格式的文档统一解析为Markdown格式，并**自动提取和保留文档的层级结构**。

### 核心特性

- ✅ **自动结构提取**：智能识别文档中的标题、段落、列表等层级结构
- ✅ **统一Markdown输出**：所有格式统一转换为结构化的Markdown
- ✅ **用户透明**：无需关注结构提取细节，自动完成
- ✅ **支持多种格式**：PDF、DOCX、PPT、Markdown、TXT
- ✅ **高度可扩展**：简单的继承接口，支持自定义解析逻辑

## 🏗️ 架构设计

### 目录结构

```
ame/foundation/file/
├── utils/              # 工具层
│   ├── models.py       # 数据模型（DocumentSection, DocumentStructure, ParsedMarkdown）
│   └── exceptions.py   # 异常定义
├── components/         # 组件层
│   ├── trans2markdown.py      # Markdown转换器
│   └── structure_extractor.py # 层级结构提取器
└── core/              # 核心层
    ├── base.py        # 解析器基类
    └── ameparser.py   # 统一解析器（实现所有常见格式）
```

### 三层架构说明

1. **utils** - 工具层
   - `DocumentFormat`: 文档格式枚举
   - `SectionType`: 章节类型枚举（h1-h6、paragraph、list等）
   - `DocumentSection`: 单个章节数据类
   - `DocumentStructure`: 文档层级结构
   - `ParsedMarkdown`: 最终解析结果

2. **components** - 组件层
   - `StructureExtractor`: 自动提取文档层级结构
   - `Trans2Markdown`: 基于结构生成Markdown

3. **core** - 核心层
   - `FileParserBase`: 定义解析器接口
   - `AMEParser`: 实现所有常见格式的解析

### 工作流程

```
用户调用 parser.parse("file.pdf")
        ↓
AMEParser._parse_pdf(path) 
        ↓ 返回 (content, metadata)
        ↓
Trans2Markdown.convert()
        ↓ 调用
StructureExtractor.extract()
        ↓ 优先从 metadata["sections"] 提取
        ↓ 或智能识别文本结构
        ↓ 生成
DocumentStructure 对象
        ↓ 调用
DocumentStructure.to_markdown()
        ↓ 生成
Markdown 内容（保留层级）
        ↓
返回 ParsedMarkdown 对象
        ↓
用户获得完整结果
```

## ✨ 核心特性

### 1. 自动层级结构提取与保留

**所有文档格式解析时都会自动提取层级结构**，无需用户干预：

```python
from ame.foundation.file import AMEParser

parser = AMEParser()
result = await parser.parse("thesis.pdf")

# Markdown内容已自动保留层级结构
print(result.markdown_content)
# 输出:
# # 第一章 绪论
#
# 这是绪论的内容...
#
# ## 1.1 研究背景
#
# 这是研究背景的内容...

# 获取文档大纲
print(result.get_outline())
# 输出:
# - 第一章 绪论
#   - 1.1 研究背景
#   - 1.2 研究意义

# 访问结构化信息
if result.structure:
    headings = result.structure.get_headings()
    for h in headings:
        print(f"{'  ' * (h.level - 1)}{h.content}")
```

### 2. 统一的Markdown输出

所有文档格式解析后统一转换为Markdown，便于后续处理：

```python
from ame.foundation.file import AMEParser

parser = AMEParser()
result = await parser.parse("document.pdf")

# 统一的数据结构
print(result.source_format)      # 源格式: pdf
print(result.markdown_content)   # Markdown内容
print(result.structure)          # 层级结构对象
print(result.total_chars)        # 字符统计
print(result.metadata)           # 元数据
```

### 3. 支持多种格式

- ✅ PDF (PyPDF2 / pdfplumber)
- ✅ DOCX (python-docx)
- ✅ PPT/PPTX (python-pptx)
- ✅ Markdown (.md)
- ✅ Text (.txt)

### 4. 简单的扩展接口

用户只需继承 `AMEParser`，重写感兴趣的方法即可，**结构提取和Markdown转换自动完成**：

```python
from ame.foundation.file import AMEParser
from pathlib import Path

class MyCustomParser(AMEParser):
    async def _parse_pdf(self, path: Path):
        """自定义PDF解析逻辑"""
        content = "自定义解析的内容"
        
        # 可选：提供结构化信息，转换器会自动使用
        metadata = {
            "custom": "data",
            "sections": [  # 提供结构化信息
                {"type": "h1", "content": "标题1", "level": 1},
                {"type": "paragraph", "content": "段落内容"},
            ]
        }
        return content, metadata

# 使用自定义解析器（结构自动提取和转换）
parser = MyCustomParser()
result = await parser.parse("document.pdf")
print(result.get_outline())  # 自动生成大纲
```

### 5. 自动格式识别

无需手动指定格式，解析器自动根据文件扩展名识别：

```python
parser = AMEParser()

# 自动识别格式
await parser.parse("report.pdf")      # 识别为PDF
await parser.parse("notes.docx")      # 识别为DOCX
await parser.parse("readme.md")       # 识别为Markdown
```

## 🚀 快速开始

### 基础使用

```python
from ame.foundation.file import AMEParser

async def parse_document():
    parser = AMEParser()
    
    # 解析PDF（自动提取结构）
    result = await parser.parse("document.pdf")
    
    print(f"源格式: {result.source_format.value}")
    print(f"文件路径: {result.file_path}")
    print(f"内容长度: {result.total_chars} 字符")
    print(f"\nMarkdown内容:\n{result.markdown_content}")
    print(f"\n文档大纲:\n{result.get_outline()}")
```

### 层级结构示例

#### 示例1：PDF文档

```python
# 假设PDF内容如下:
"""
第一章 绪论

这是绪论的内容...

1.1 研究背景

这是研究背景的内容...

1.2 研究意义

这是研究意义的内容...
"""

# 解析后自动识别层级
result = await parser.parse("thesis.pdf")

# 查看生成的Markdown（自动保留结构）
print(result.markdown_content)
# 输出:
# # 第一章 绪论
#
# 这是绪论的内容...
#
# ## 1.1 研究背景
#
# 这是研究背景的内容...
#
# ## 1.2 研究意义
#
# 这是研究意义的内容...

# 查看大纲
print(result.get_outline())
# 输出:
# - 第一章 绪论
#   - 1.1 研究背景
#   - 1.2 研究意义
```

#### 示例2：DOCX文档

```python
# DOCX文档中包含Heading样式
# 解析时自动提取样式信息并转换为层级结构

result = await parser.parse("report.docx")

# 结构信息已自动提取到 result.structure
for section in result.structure.sections:
    if section.type.value.startswith('h'):
        print(f"标题 (Level {section.level}): {section.content}")
    else:
        print(f"段落: {section.content[:50]}...")

# 或直接查看Markdown（已包含标题层级）
print(result.markdown_content)
```

#### 示例3：PPT文档

```python
# PPT自动按幻灯片组织结构

result = await parser.parse("presentation.pptx")

# 每张幻灯片的标题自动识别为二级标题
# 列表项自动识别并转换为Markdown列表
print(result.markdown_content)
# 输出:
# ## 幻灯片 1 - 项目介绍
#
# - 项目背景
# - 项目目标
# - 项目范围
#
# ---
#
# ## 幻灯片 2 - 技术架构
#
# - 前端技术栈
# - 后端技术栈
# - 数据库选型
```

### 高级用法：自定义解析器

如果你使用了更高级的PDF解析库（如PyMuPDF），也能自动利用层级结构提取：

```python
from ame.foundation.file import AMEParser
from pathlib import Path
from typing import Dict, Any

class EnhancedPDFParser(AMEParser):
    """增强的PDF解析器"""
    
    async def _parse_pdf(self, path: Path):
        import fitz  # PyMuPDF
        
        doc = fitz.open(path)
        sections_data = []
        
        # 提取文档结构
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block["type"] == 0:  # 文本块
                    for line in block["lines"]:
                        text = " ".join([span["text"] for span in line["spans"]])
                        
                        # 根据字体大小判断是否是标题
                        font_size = line["spans"][0]["size"]
                        
                        if font_size > 18:
                            sections_data.append({
                                "type": "h1",
                                "content": text,
                                "level": 1
                            })
                        elif font_size > 14:
                            sections_data.append({
                                "type": "h2",
                                "content": text,
                                "level": 2
                            })
                        else:
                            sections_data.append({
                                "type": "paragraph",
                                "content": text
                            })
        
        doc.close()
        
        # 返回内容和元数据（包含结构化信息）
        content = "\n\n".join([s["content"] for s in sections_data])
        metadata = {
            "parser": "PyMuPDF",
            "file_size": path.stat().st_size,
            "sections": sections_data  # 关键：传递结构化信息
        }
        
        return content, metadata

# 使用自定义解析器
parser = AdvancedPDFParser()
result = await parser.parse("document.pdf")

# 结构会自动从metadata的sections中提取
# 然后自动转换为Markdown
print(result.markdown_content)
print(result.get_outline())
```

### 批量处理

```python
from ame.foundation.file import AMEParser
from pathlib import Path

async def batch_parse():
    parser = AMEParser()
    
    files = [
        "report1.pdf",
        "notes.docx",
        "readme.md",
        "data.txt",
    ]
    
    results = []
    for file_path in files:
        try:
            result = await parser.parse(file_path)
            results.append(result)
            print(f"✓ {file_path}: {result.total_chars} 字符")
        except Exception as e:
            print(f"✗ {file_path}: {e}")
    
    return results
```

## 📦 数据结构详解

### 1. DocumentSection - 章节数据类

表示文档中的单个章节或段落：

```python
from ame.foundation.file import DocumentSection, SectionType

# 创建一个章节（通常由 StructureExtractor 自动创建）
section = DocumentSection(
    type=SectionType.HEADING_1,
    content="第一章 引言",
    level=1,
    metadata={"custom": "data"}
)

# 转换为Markdown
markdown = section.to_markdown()
print(markdown)  # 输出: # 第一章 引言
```

### 2. DocumentStructure - 文档结构类

表示文档的完整层级结构：

```python
from ame.foundation.file import DocumentStructure, DocumentSection, SectionType

# 创建文档结构（通常由 StructureExtractor 自动生成）
structure = DocumentStructure(sections=[
    DocumentSection(type=SectionType.HEADING_1, content="标题1", level=1),
    DocumentSection(type=SectionType.PARAGRAPH, content="这是段落内容"),
    DocumentSection(type=SectionType.HEADING_2, content="标题2", level=2),
])

# 转换为完整Markdown
markdown = structure.to_markdown()
print(markdown)

# 获取大纲
outline = structure.get_outline()
print(outline)
# 输出:
# - 标题1
#   - 标题2

# 获取所有标题
headings = structure.get_headings()
for h in headings:
    print(f"{h.type.value}: {h.content}")

# 获取特定级别标题
h1_list = structure.get_headings(level=1)
```

### 3. ParsedMarkdown - 解析结果类

完整的解析结果，包含所有信息：

```python
# 完整的解析结果包含:
result = await parser.parse("document.pdf")

print(f"源格式: {result.source_format}")          # DocumentFormat.PDF
print(f"文件路径: {result.file_path}")           # /path/to/document.pdf
print(f"Markdown: {result.markdown_content}")    # 完整Markdown内容
print(f"结构: {result.structure}")               # DocumentStructure对象
print(f"元数据: {result.metadata}")              # 文件元数据
print(f"字符数: {result.total_chars}")           # 总字符数
print(f"词数: {result.total_words}")             # 总词数
print(f"解析时间: {result.parsed_at}")           # 解析时间戳

# 便捷方法
outline = result.get_outline()                   # 获取大纲
dict_data = result.to_dict()                     # 转换为字典
```

## 🔧 组件详解

### 1. StructureExtractor - 结构提取器

自动从不同格式的文档中提取层级结构：

```python
from ame.foundation.file import StructureExtractor, DocumentFormat

extractor = StructureExtractor()

# 从文本中提取结构
structure = extractor.extract(
    content="第一章 引言\n\n内容...",
    source_format=DocumentFormat.TEXT,
    metadata={}
)

# 结构会自动识别标题、段落等
for section in structure.sections:
    print(f"{section.type.value}: {section.content}")
```

### 2. Trans2Markdown - Markdown转换器

基于 DocumentStructure 生成Markdown：

```python
from ame.foundation.file import Trans2Markdown, DocumentFormat

converter = Trans2Markdown()

result = await converter.convert(
    content="原始内容",
    source_format=DocumentFormat.TEXT,
    file_path="/path/to/file.txt",
    metadata={}
)

# 结果包含 structure 和 markdown_content
print(result.markdown_content)
print(result.structure.get_outline())
```

### 3. FileParserBase - 解析器基类

定义解析器必须实现的接口：

```python
class FileParserBase(ABC):
    """所有解析器的基类"""
    
    @abstractmethod
    async def can_parse(self, file_path: str) -> bool:
        """判断是否支持该文件"""
        pass
    
    async def parse(self, file_path: str) -> ParsedMarkdown:
        """统一的解析入口（已实现）"""
        # 1. 验证文件
        # 2. 识别格式
        # 3. 调用_parse_*方法
        # 4. 转换为Markdown
        pass
    
    # 子类需要实现的方法
    async def _parse_pdf(self, path: Path): ...
    async def _parse_docx(self, path: Path): ...
    async def _parse_ppt(self, path: Path): ...
    async def _parse_markdown(self, path: Path): ...
    async def _parse_text(self, path: Path): ...
```

## 💡 设计理念

### 1. 用户无感知的自动化

- **用户只需调用 `parse()`**：所有结构提取和转换自动完成
- **无需关注组件调用**：StructureExtractor 和 Trans2Markdown 自动工作
- **无需关注数据转换**：DocumentStructure 自动生成 Markdown

### 2. 层级结构的统一表达

- **DocumentSection**：表示单个章节，支持标题、段落、列表等多种类型
- **DocumentStructure**：表示完整文档结构，提供便捷方法
- **自动转换**：每个 Section 都知道如何转换为 Markdown

### 3. 关注点分离

- **用户只需关注解析逻辑**：重写 `_parse_*` 方法
- **无需关注主流程**：格式识别、Markdown转换由基类处理
- **无需关注组件调用**：`Trans2Markdown` 自动调用

### 4. 统一的数据格式

所有文档统一输出为 `ParsedMarkdown`，提供：
- 标准化的内容格式（Markdown）
- 一致的元数据结构
- 自动的统计信息

### 5. 灵活的扩展性

```python
# 场景1: 只自定义PDF解析
class MyParser(AMEParser):
    async def _parse_pdf(self, path):
        # 自定义PDF解析
        pass

# 场景2: 添加新格式支持
class ExtendedParser(AMEParser):
    SUPPORTED_EXTENSIONS = AMEParser.SUPPORTED_EXTENSIONS | {"xlsx", "csv"}
    
    async def _parse_excel(self, path):
        # Excel解析逻辑
        pass
```

## 🎯 最佳实践

### 1. 利用结构化信息

```python
result = await parser.parse("document.pdf")

# 获取文档大纲
outline = result.get_outline()
print(f"文档大纲:\n{outline}")

# 获取所有一级标题
if result.structure:
    h1_headings = result.structure.get_headings(level=1)
    for h in h1_headings:
        print(f"章节: {h.content}")

# 统计章节数量
headings = result.structure.get_headings()
print(f"共有 {len(headings)} 个标题")
```

### 2. 错误处理

```python
from ame.foundation.file import AMEParser, UnsupportedFormatError

parser = AMEParser()

try:
    result = await parser.parse("document.unknown")
except FileNotFoundError:
    print("文件不存在")
except UnsupportedFormatError as e:
    print(f"不支持的格式: {e.format}")
except Exception as e:
    print(f"解析失败: {e}")
```

### 3. 性能优化

```python
# 对于大文件，使用pdfplumber可能更准确但更慢
parser_accurate = AMEParser(use_pdfplumber=True)

# 对于速度要求高的场景，使用PyPDF2
parser_fast = AMEParser(use_pdfplumber=False)
```

### 4. 元数据利用

```python
result = await parser.parse("document.pdf")

# 访问元数据
print(f"解析器: {result.metadata['parser']}")
print(f"文件大小: {result.metadata['file_size']}")
print(f"总页数: {result.metadata.get('total_pages')}")
```

## 🧪 测试

运行测试：

```bash
cd ame-tests/foundation/file
python test_new_file_module.py
```

## 📝 迁移说明

从旧的 file-back 模块迁移：

```python
# 旧代码（file-back）
from ame.foundation.file_back import parse_document
doc = await parse_document("file.pdf")
print(doc.raw_content)
print(doc.sections)

# 新代码（统一为 Markdown + 结构）
from ame.foundation.file import AMEParser
parser = AMEParser()
result = await parser.parse("file.pdf")
print(result.markdown_content)  # 统一为Markdown格式
print(result.structure)         # 层级结构对象
print(result.get_outline())     # 文档大纲
```

## 🤝 贡献

欢迎贡献新的解析器实现或改进现有解析逻辑！

## 📄 许可证

与AME项目保持一致
