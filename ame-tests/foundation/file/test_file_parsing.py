"""
文档解析模块脚本化测试
"""

import sys
import asyncio
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from ame.foundation.file import (
    DocumentParsePipeline,
    parse_document,
    DocumentFormat,
    SectionType,
)


def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}")
    else:
        print("-" * 80)


def print_section(section, indent=0):
    """打印文档片段"""
    prefix = "  " * indent
    print(f"{prefix}[{section.type.value}] {section.content[:100]}..." if len(section.content) > 100 else f"{prefix}[{section.type.value}] {section.content}")


async def test_file(file_path: str):
    """测试单个文件的解析"""
    print_separator(f"测试文件: {Path(file_path).name}")
    
    try:
        # 解析文档
        doc = await parse_document(file_path)
        
        # 基本信息
        print(f"\n📄 文件格式: {doc.format.value}")
        print(f"📊 统计信息:")
        print(f"   - 总字符数: {doc.total_chars}")
        print(f"   - 总单词数: {doc.total_words}")
        print(f"   - 片段数量: {len(doc.sections)}")
        
        # 原始内容预览
        print(f"\n📝 原始内容预览 (前200字符):")
        print(f"   {doc.raw_content[:200]}..." if len(doc.raw_content) > 200 else f"   {doc.raw_content}")
        
        # 片段详情
        print(f"\n📑 片段列表:")
        for i, section in enumerate(doc.sections[:10], 1):  # 只显示前10个
            print_section(section)
        
        if len(doc.sections) > 10:
            print(f"   ... 还有 {len(doc.sections) - 10} 个片段")
        
        # 标题大纲(如果有)
        headings = doc.get_headings()
        if headings:
            print(f"\n🗂️  文档大纲:")
            for heading in headings:
                indent = int(heading.type.value.split('_')[-1]) - 1 if 'HEADING' in heading.type.value else 0
                print(f"{'  ' * indent}- {heading.content}")
        
        # 字典格式
        print(f"\n📦 字典格式 (部分):")
        doc_dict = doc.to_dict()
        print(f"   Keys: {list(doc_dict.keys())}")
        print(f"   Metadata: {doc_dict.get('metadata', {})}")
        
        print(f"\n✅ 解析成功!")
        
    except Exception as e:
        print(f"\n❌ 解析失败: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """主测试流程"""
    # 测试文件目录
    test_dir = Path(__file__).parent / "test_file"
    
    print_separator("文档解析模块脚本化测试")
    print(f"\n测试目录: {test_dir}")
    
    # 列出所有测试文件
    test_files = sorted(test_dir.glob("*"))
    test_files = [f for f in test_files if f.is_file()]
    
    print(f"\n发现 {len(test_files)} 个测试文件:")
    for f in test_files:
        print(f"  - {f.name} ({f.suffix})")
    
    # 显示支持的格式
    pipeline = DocumentParsePipeline()
    print(f"\n支持的格式:")
    formats = pipeline.get_supported_formats()
    for parser, exts in formats.items():
        print(f"  - {parser}: {', '.join(exts)}")
    
    # 测试每个文件
    for file_path in test_files:
        if pipeline.is_supported(str(file_path)):
            await test_file(str(file_path))
        else:
            print_separator(f"跳过不支持的文件: {file_path.name}")
            print(f"   文件类型: {file_path.suffix}")
    
    print_separator("所有测试完成")


if __name__ == "__main__":
    asyncio.run(main())
