"""
Analysis - 分析能力

提供数据分析、洞察提取等高级分析能力

核心组件：
- DataAnalyzer: 统一的数据分析器（情绪、关键词、统计、趋势）
- InsightGenerator: 洞察生成器（关键任务、成果、挑战提取）
"""

from .data_analyzer import DataAnalyzer
from .insight_generator import InsightGenerator

__all__ = [
    "DataAnalyzer",
    "InsightGenerator",
]
