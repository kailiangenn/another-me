"""
Cascade Inference 框架 - 级联推理引擎

设计目标：
1. 统一「规则 → LLM 兜底」模式
2. 降低 LLM 调用成本（60-70%）
3. 提升推理速度（3-5倍）
4. 可扩展的多层级推理

适用场景：
- NER 实体识别（规则 NER → LLM NER）
- 情绪识别（规则情绪 → LLM 情绪）
- 意图分类（规则意图 → LLM 意图）
- 任何需要「快速 + 准确」的推理任务
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class InferenceLevel(Enum):
    """推理层级"""
    RULE = "rule"          # 规则层
    FAST_MODEL = "fast"    # 快速模型层
    LLM = "llm"            # LLM 层
    ENSEMBLE = "ensemble"  # 集成层


@dataclass
class InferenceResult:
    """推理结果"""
    value: Any                              # 推理结果值
    confidence: float                       # 置信度（0-1）
    level: InferenceLevel                   # 推理层级
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class InferenceLevelBase(ABC):
    """推理层级抽象基类"""
    
    @abstractmethod
    async def infer(self, input_data: Any, context: Dict[str, Any]) -> InferenceResult:
        """
        执行推理
        
        Args:
            input_data: 输入数据
            context: 上下文信息
        
        Returns:
            result: 推理结果
        """
        pass
    
    @abstractmethod
    def get_level(self) -> InferenceLevel:
        """获取推理层级"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """获取层级名称"""
        pass


class CascadeInferenceEngine:
    """
    级联推理引擎
    
    核心机制：
    1. 多层级推理：规则 → 快速模型 → LLM
    2. 置信度判断：低于阈值时级联到下一层
    3. 成本控制：优先使用低成本方法
    4. 结果缓存：避免重复推理
    """
    
    def __init__(
        self,
        confidence_threshold: float = 0.7,
        enable_cache: bool = True,
        fallback_strategy: str = "cascade"
    ):
        """
        初始化级联推理引擎
        
        Args:
            confidence_threshold: 置信度阈值（低于此值级联到下一层）
            enable_cache: 是否启用缓存
            fallback_strategy: 兜底策略
                - cascade: 级联到下一层
                - ensemble: 集成多层结果
        """
        self.confidence_threshold = confidence_threshold
        self.enable_cache = enable_cache
        self.fallback_strategy = fallback_strategy
        
        self.levels: List[InferenceLevelBase] = []
        self.cache: Dict[str, InferenceResult] = {}
        
        logger.info(
            f"CascadeInferenceEngine 初始化 "
            f"(threshold={confidence_threshold}, cache={enable_cache}, "
            f"strategy={fallback_strategy})"
        )
    
    def add_level(self, level: InferenceLevelBase) -> 'CascadeInferenceEngine':
        """
        添加推理层级（按优先级排序）
        
        Args:
            level: 推理层级实例
        
        Returns:
            self: 支持链式调用
        """
        self.levels.append(level)
        logger.debug(f"添加推理层级: {level.get_name()}")
        return self
    
    async def infer(
        self,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
        force_level: Optional[InferenceLevel] = None
    ) -> InferenceResult:
        """
        执行级联推理
        
        流程：
        1. 检查缓存
        2. 按优先级执行各层级推理
        3. 置信度判断：高于阈值则返回，否则级联
        4. 缓存结果
        
        Args:
            input_data: 输入数据
            context: 上下文信息
            force_level: 强制使用指定层级（跳过级联）
        
        Returns:
            result: 最终推理结果
        """
        if not self.levels:
            raise ValueError("未添加任何推理层级")
        
        ctx = context or {}
        
        # 1. 缓存检查
        cache_key = self._get_cache_key(input_data)
        if self.enable_cache and cache_key in self.cache:
            logger.debug(f"命中缓存: {cache_key}")
            return self.cache[cache_key]
        
        # 2. 强制使用指定层级
        if force_level:
            for level in self.levels:
                if level.get_level() == force_level:
                    result = await level.infer(input_data, ctx)
                    self._update_cache(cache_key, result)
                    return result
            
            logger.warning(f"未找到指定层级: {force_level}，使用级联模式")
        
        # 3. 级联推理
        if self.fallback_strategy == "ensemble":
            result = await self._ensemble_inference(input_data, ctx)
        else:
            result = await self._cascade_inference(input_data, ctx)
        
        # 4. 缓存结果
        self._update_cache(cache_key, result)
        
        return result
    
    async def _cascade_inference(
        self,
        input_data: Any,
        context: Dict[str, Any]
    ) -> InferenceResult:
        """
        级联推理模式
        
        规则：
        1. 按优先级执行各层级
        2. 置信度 >= 阈值时返回
        3. 否则继续下一层级
        4. 最后一层强制返回
        """
        for i, level in enumerate(self.levels):
            is_last = (i == len(self.levels) - 1)
            
            try:
                logger.debug(f"执行推理层级 {i+1}/{len(self.levels)}: {level.get_name()}")
                
                result = await level.infer(input_data, context)
                
                logger.debug(
                    f"层级 {level.get_name()} 完成: "
                    f"confidence={result.confidence:.3f}, "
                    f"value={str(result.value)[:50]}"
                )
                
                # 判断是否需要级联
                if result.confidence >= self.confidence_threshold or is_last:
                    logger.info(
                        f"级联推理完成于层级 {level.get_name()} "
                        f"(confidence={result.confidence:.3f})"
                    )
                    return result
                
                logger.debug(
                    f"层级 {level.get_name()} 置信度不足 "
                    f"({result.confidence:.3f} < {self.confidence_threshold})，"
                    f"级联到下一层"
                )
                
            except Exception as e:
                logger.error(f"层级 {level.get_name()} 执行失败: {e}", exc_info=True)
                
                if is_last:
                    # 最后一层失败，返回默认结果
                    return InferenceResult(
                        value=None,
                        confidence=0.0,
                        level=level.get_level(),
                        metadata={"error": str(e)}
                    )
                else:
                    # 非最后一层失败，继续下一层
                    continue
        
        # 理论上不应该到达这里
        raise RuntimeError("所有推理层级均失败")
    
    async def _ensemble_inference(
        self,
        input_data: Any,
        context: Dict[str, Any]
    ) -> InferenceResult:
        """
        集成推理模式
        
        规则：
        1. 执行所有层级
        2. 根据置信度加权融合结果
        """
        results = []
        
        for level in self.levels:
            try:
                result = await level.infer(input_data, context)
                results.append(result)
            except Exception as e:
                logger.error(f"层级 {level.get_name()} 执行失败: {e}")
                continue
        
        if not results:
            raise RuntimeError("所有推理层级均失败")
        
        # 简单策略：选择置信度最高的结果
        best_result = max(results, key=lambda r: r.confidence)
        
        logger.info(
            f"集成推理完成，选择最佳结果来自: {best_result.level.value} "
            f"(confidence={best_result.confidence:.3f})"
        )
        
        return best_result
    
    def _get_cache_key(self, input_data: Any) -> str:
        """生成缓存键"""
        if isinstance(input_data, str):
            return f"input:{hash(input_data)}"
        else:
            return f"input:{id(input_data)}"
    
    def _update_cache(self, key: str, result: InferenceResult):
        """更新缓存"""
        if self.enable_cache:
            self.cache[key] = result
    
    def clear_cache(self):
        """清空缓存"""
        self.cache.clear()
        logger.debug("缓存已清空")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            stats: 统计数据
        """
        return {
            "total_levels": len(self.levels),
            "cache_size": len(self.cache),
            "confidence_threshold": self.confidence_threshold,
            "fallback_strategy": self.fallback_strategy
        }


# 便捷函数：创建推理层级

def create_rule_level(
    rule_func: Callable[[Any, Dict], InferenceResult],
    name: str = "Rule"
) -> InferenceLevelBase:
    """
    创建规则层级
    
    Args:
        rule_func: 规则函数
        name: 层级名称
    
    Returns:
        level: 规则层级实例
    """
    class RuleLevel(InferenceLevelBase):
        async def infer(self, input_data, context):
            return rule_func(input_data, context)
        
        def get_level(self):
            return InferenceLevel.RULE
        
        def get_name(self):
            return name
    
    return RuleLevel()


def create_llm_level(
    llm_caller,
    prompt_builder: Callable[[Any, Dict], str],
    result_parser: Callable[[str], InferenceResult],
    name: str = "LLM"
) -> InferenceLevelBase:
    """
    创建 LLM 层级
    
    Args:
        llm_caller: LLM 调用器
        prompt_builder: Prompt 构建函数
        result_parser: 结果解析函数
        name: 层级名称
    
    Returns:
        level: LLM 层级实例
    """
    class LLMLevel(InferenceLevelBase):
        async def infer(self, input_data, context):
            prompt = prompt_builder(input_data, context)
            
            response = await llm_caller.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            
            return result_parser(content)
        
        def get_level(self):
            return InferenceLevel.LLM
        
        def get_name(self):
            return name
    
    return LLMLevel()
