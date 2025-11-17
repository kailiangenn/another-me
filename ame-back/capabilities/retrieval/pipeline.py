"""
Capabilities Layer - Retrieval Pipeline

检索管道编排器（责任链模式）
"""

import logging
from typing import List, Dict, Any, Optional

from ame.foundation.retrieval import RetrievalResult
from .stages.base import StageBase

logger = logging.getLogger(__name__)


class RetrievalPipeline:
    """
    检索管道：支持多阶段组合
    
    设计模式：责任链模式
    核心优势：
    1. 可组合性：任意组合检索阶段
    2. 可扩展性：新增阶段无需修改现有代码
    3. 可测试性：每个阶段独立测试
    """
    
    def __init__(self, name: str = "default"):
        """
        初始化检索管道
        
        Args:
            name: 管道名称（用于日志识别）
        """
        self.name = name
        self.stages: List[StageBase] = []
        
        logger.info(f"创建检索管道: {name}")
    
    def add_stage(self, stage: StageBase) -> 'RetrievalPipeline':
        """
        添加检索阶段（支持链式调用）
        
        Args:
            stage: 检索阶段实例
        
        Returns:
            self: 支持链式调用
        """
        self.stages.append(stage)
        logger.debug(f"[{self.name}] 添加阶段: {stage.get_name()}")
        return self
    
    async def execute(
        self, 
        query: str, 
        top_k: int = 10,
        context: Optional[Dict] = None
    ) -> List[RetrievalResult]:
        """
        执行检索管道
        
        流程：
        1. 初始化上下文（共享查询、参数）
        2. 顺序执行各阶段
        3. 每阶段接收前序结果，输出新结果
        4. 返回最终 top_k 结果
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            context: 上下文信息（可选）
        
        Returns:
            检索结果列表
        """
        if not query or not query.strip():
            logger.warning(f"[{self.name}] 查询为空")
            return []
        
        if not self.stages:
            logger.warning(f"[{self.name}] 管道为空，没有配置任何阶段")
            return []
        
        # 初始化上下文
        ctx = context or {}
        ctx.update({
            "query": query,
            "top_k": top_k,
            "pipeline_name": self.name
        })
        
        # 顺序执行各阶段
        results = None
        
        for i, stage in enumerate(self.stages):
            stage_name = stage.get_name()
            
            try:
                logger.debug(
                    f"[{self.name}] 执行阶段 {i+1}/{len(self.stages)}: {stage_name}"
                )
                
                results = await stage.process(query, results, ctx)
                
                logger.debug(
                    f"[{self.name}] 阶段 {stage_name} 完成，"
                    f"输出 {len(results) if results else 0} 个结果"
                )
                
            except Exception as e:
                logger.error(
                    f"[{self.name}] 阶段 {stage_name} 执行失败: {e}",
                    exc_info=True
                )
                
                # 失败时使用前序结果继续
                if results is None:
                    results = []
        
        # 返回最终结果
        final_results = results[:top_k] if results else []
        
        logger.info(
            f"[{self.name}] 管道执行完成，返回 {len(final_results)} 个结果"
        )
        
        return final_results
    
    def get_stage_names(self) -> List[str]:
        """获取所有阶段名称"""
        return [stage.get_name() for stage in self.stages]
    
    def __repr__(self) -> str:
        stages_str = " -> ".join(self.get_stage_names())
        return f"RetrievalPipeline(name={self.name}, stages=[{stages_str}])"
