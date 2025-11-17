"""
Inference - 推理框架能力

提供统一的推理框架，支持级联推理、规则引擎、融合算法等。

核心组件：
- CascadeInferenceEngine: 级联推理引擎（规则 → 快速模型 → LLM）
- InferenceLevelBase: 推理层级抽象基类
- InferenceResult: 推理结果封装
"""

from .cascade_inference import (
    CascadeInferenceEngine,
    InferenceLevelBase,
    InferenceResult,
    InferenceLevel,
    create_rule_level,
    create_llm_level,
)

__all__ = [
    "CascadeInferenceEngine",
    "InferenceLevelBase",
    "InferenceResult",
    "InferenceLevel",
    "create_rule_level",
    "create_llm_level",
]
