"""
File模块测试

测试新设计的file模块功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from ame.foundation.file import AMEParser, DocumentFormat


async def test_ameparser():
    """测试AMEParser基础功能"""
    print("=" * 60)
    print("测试 AMEParser")
    print("=" * 60)
    
    parser = AMEParser()
    
    # 测试格式识别
    print("\n1. 支持的文件格式:")
    print(f"   {parser.SUPPORTED_EXTENSIONS}")
    
    # 测试can_parse
    print("\n2. 测试can_parse:")
    test_files = [
        "test.pdf",
        "test.docx",
        "test.md",
        "test.txt",
        "test.xlsx",  # 不支持
    ]
    
    for file_path in test_files:
        can_parse = parser.can_parse(file_path)
        print(f"   {file_path}: {'✓' if can_parse else '✗'}")
    
    print("\n" + "=" * 60)


async def test_custom_parser():
    """测试自定义解析器"""
    print("\n" + "=" * 60)
    print("测试自定义解析器")
    print("=" * 60)
    
    class MyCustomParser(AMEParser):
        """自定义解析器示例"""
        
        async def _parse_pdf(self, path):
            """自定义PDF解析逻辑"""
            print(f"\n   使用自定义逻辑解析PDF: {path.name}")
            
            # 这里可以实现自己的解析逻辑
            content = f"这是自定义解析的PDF内容\n文件: {path.name}"
            metadata = {
                "parser": "MyCustomParser",
                "file_size": path.stat().st_size,
                "custom_field": "自定义元数据"
            }
            
            return content, metadata
    
    parser = MyCustomParser()
    print("\n   自定义解析器创建成功")
    print(f"   支持的格式: {parser.SUPPORTED_EXTENSIONS}")
    
    print("\n" + "=" * 60)


async def test_markdown_conversion():
    """测试Markdown转换组件"""
    print("\n" + "=" * 60)
    print("测试Markdown转换组件")
    print("=" * 60)
    
    from ame.foundation.file import Trans2Markdown
    
    converter = Trans2Markdown()
    
    # 测试文本转Markdown
    test_content = """这是第一段内容

这是第二段内容

这是第三段内容"""
    
    result = await converter.convert(
        content=test_content,
        source_format=DocumentFormat.TEXT,
        file_path="/test/example.txt",
        metadata={"test": "metadata"}
    )
    
    print("\n   转换结果:")
    print(f"   - 源格式: {result.source_format.value}")
    print(f"   - 文件路径: {result.file_path}")
    print(f"   - 字符数: {result.total_chars}")
    print(f"   - 词数: {result.total_words}")
    print(f"\n   Markdown内容预览:")
    print("   " + "-" * 50)
    for line in result.markdown_content.split('\n')[:5]:
        print(f"   {line}")
    print("   " + "-" * 50)
    
    print("\n" + "=" * 60)


async def test_architecture():
    """测试架构设计"""
    print("\n" + "=" * 60)
    print("架构设计说明")
    print("=" * 60)
    
    print("""
    新的file模块架构:
    
    1. utils/ - 工具层
       ├── models.py      - 数据模型（ParsedMarkdown）
       └── exceptions.py  - 异常定义
    
    2. components/ - 组件层
       └── trans2markdown.py - Markdown转换器
    
    3. core/ - 核心层
       ├── base.py        - 解析器基类（定义接口）
       └── ameparser.py   - 统一解析器（实现所有格式）
    
    设计优势:
    
    ✓ 用户只需继承AMEParser
    ✓ 只需重写感兴趣的_parse_*方法
    ✓ 无需关注主流程和组件调用
    ✓ 所有结果统一转换为Markdown格式
    ✓ 自动处理格式识别和错误处理
    
    使用示例:
    
    # 1. 直接使用
    parser = AMEParser()
    result = await parser.parse("document.pdf")
    print(result.markdown_content)
    
    # 2. 自定义扩展
    class MyParser(AMEParser):
        async def _parse_pdf(self, path):
            # 自定义PDF解析
            content = "..."
            metadata = {...}
            return content, metadata
    
    my_parser = MyParser()
    result = await my_parser.parse("document.pdf")
    """)
    
    print("=" * 60)


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("File模块测试")
    print("=" * 60)
    
    await test_ameparser()
    await test_custom_parser()
    await test_markdown_conversion()
    await test_architecture()
    
    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
