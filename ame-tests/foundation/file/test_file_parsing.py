"""
文档解析模块单元测试
"""

import pytest
import sys

import tempfile
from pathlib import Path
sys.path.append(Path(__file__).parent.parent.parent.parent)
sys.path.append('/Users/kaiiangs/Desktop/another-me/ame')
print(sys.path)

from ame.foundation.file import (
    DocumentParsePipeline,
    parse_document,
    TextParser,
    MarkdownParser,
    DocumentFormat,
    SectionType,
)


class TestTextParser:
    """测试文本解析器"""
    
    @pytest.mark.asyncio
    async def test_parse_simple_text(self):
        """测试解析简单文本"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("第一段\n\n第二段\n\n第三段")
            temp_path = f.name
        
        try:
            # 解析
            parser = TextParser()
            doc = await parser.parse(temp_path)
            
            # 验证
            assert doc.format == DocumentFormat.TEXT
            assert len(doc.sections) == 3
            assert all(s.type == SectionType.PARAGRAPH for s in doc.sections)
            assert doc.sections[0].content == "第一段"
            assert doc.sections[1].content == "第二段"
            assert doc.sections[2].content == "第三段"
        
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_encoding_detection(self):
        """测试编码检测"""
        # 创建UTF-8文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write("中文测试内容")
            temp_path = f.name
        
        try:
            parser = TextParser()
            doc = await parser.parse(temp_path)
            assert "中文测试内容" in doc.raw_content
        
        finally:
            Path(temp_path).unlink()


class TestMarkdownParser:
    """测试Markdown解析器"""
    
    @pytest.mark.asyncio
    async def test_parse_headings(self):
        """测试解析标题"""
        content = """# 一级标题
## 二级标题
### 三级标题

段落内容
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = MarkdownParser()
            doc = await parser.parse(temp_path)
            
            # 验证标题
            headings = doc.get_headings()
            assert len(headings) == 3
            assert headings[0].type == SectionType.HEADING_1
            assert headings[0].content == "一级标题"
            assert headings[1].type == SectionType.HEADING_2
            assert headings[2].type == SectionType.HEADING_3
        
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_parse_code_blocks(self):
        """测试解析代码块"""
        content = """# 标题

```python
def hello():
    print("Hello")
```

段落
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = MarkdownParser()
            doc = await parser.parse(temp_path)
            
            # 验证代码块
            code_blocks = doc.get_sections_by_type(SectionType.CODE_BLOCK)
            assert len(code_blocks) >= 1
            assert 'def hello()' in code_blocks[0].content
        
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_parse_list(self):
        """测试解析列表"""
        content = """- 列表项1
- 列表项2
* 列表项3
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(content)
            temp_path = f.name
        
        try:
            parser = MarkdownParser()
            doc = await parser.parse(temp_path)
            
            # 验证列表
            lists = doc.get_sections_by_type(SectionType.LIST_ITEM)
            assert len(lists) == 3
        
        finally:
            Path(temp_path).unlink()


class TestDocumentParsePipeline:
    """测试文档解析管道"""
    
    @pytest.mark.asyncio
    async def test_auto_select_parser(self):
        """测试自动选择解析器"""
        pipeline = DocumentParsePipeline()
        
        # TXT
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("text content")
            temp_path = f.name
        
        try:
            doc = await pipeline.parse(temp_path)
            assert doc.format == DocumentFormat.TEXT
        finally:
            Path(temp_path).unlink()
        
        # Markdown
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Title")
            temp_path = f.name
        
        try:
            doc = await pipeline.parse(temp_path)
            assert doc.format == DocumentFormat.MARKDOWN
        finally:
            Path(temp_path).unlink()
    
    def test_get_supported_formats(self):
        """测试获取支持的格式"""
        pipeline = DocumentParsePipeline()
        formats = pipeline.get_supported_formats()
        
        assert "TextParser" in formats
        assert "MarkdownParser" in formats
        assert "txt" in formats["TextParser"]
        assert "md" in formats["MarkdownParser"]
    
    def test_is_supported(self):
        """测试判断是否支持"""
        pipeline = DocumentParsePipeline()
        
        assert pipeline.is_supported("file.txt") is True
        assert pipeline.is_supported("file.md") is True
        assert pipeline.is_supported("file.unknown") is False
    
    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """测试文件不存在"""
        pipeline = DocumentParsePipeline()
        
        with pytest.raises(FileNotFoundError):
            await pipeline.parse("nonexistent_file.txt")
    
    @pytest.mark.asyncio
    async def test_batch_parse(self):
        """测试批量解析"""
        pipeline = DocumentParsePipeline()
        
        # 创建多个临时文件
        temp_files = []
        for i in range(3):
            f = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
            f.write(f"Content {i}")
            f.close()
            temp_files.append(f.name)
        
        try:
            docs = await pipeline.batch_parse(temp_files)
            assert len(docs) == 3
            
            for i, doc in enumerate(docs):
                assert f"Content {i}" in doc.raw_content
        
        finally:
            for path in temp_files:
                Path(path).unlink()


class TestParsedDocument:
    """测试解析结果类"""
    
    @pytest.mark.asyncio
    async def test_get_outline(self):
        """测试生成大纲"""
        content = """# H1
## H2
### H3
## H2-2
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            doc = await parse_document(temp_path)
            outline = doc.get_outline()
            
            assert "H1" in outline
            assert "H2" in outline
            assert "H3" in outline
        
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_to_dict(self):
        """测试转换为字典"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            doc = await parse_document(temp_path)
            doc_dict = doc.to_dict()
            
            assert "format" in doc_dict
            assert "file_path" in doc_dict
            assert "raw_content" in doc_dict
            assert "sections" in doc_dict
            assert doc_dict["format"] == DocumentFormat.TEXT.value
        
        finally:
            Path(temp_path).unlink()
    
    @pytest.mark.asyncio
    async def test_statistics(self):
        """测试统计信息"""
        content = "Hello world. This is a test."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        try:
            doc = await parse_document(temp_path)
            
            assert doc.total_chars == len(content)
            assert doc.total_words == len(content.split())
        
        finally:
            Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
