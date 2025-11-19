"""
管道层 - 轻量数据操作编排

包含:
- GraphPipelineBase: 管道基类
- LifeGraphPipeline: 生活图谱管道
- WorkGraphPipeline: 工作图谱管道
"""

from .base import GraphPipelineBase
from .life_graph_pipeline import LifeGraphPipeline
from .work_graph_pipeline import WorkGraphPipeline

__all__ = [
    "GraphPipelineBase",
    "LifeGraphPipeline",
    "WorkGraphPipeline",
]
