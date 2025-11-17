"""
文档解析管道层

包含:
- DocumentParsePipeline: 文档解析管道
- parse_document: 便捷解析函数
"""

from .document_pipeline import DocumentParsePipeline, parse_document

__all__ = [
    "DocumentParsePipeline",
    "parse_document",
]
