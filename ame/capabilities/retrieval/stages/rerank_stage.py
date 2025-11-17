"""
Capabilities Layer - Semantic Rerank Stage

语义重排序阶段
"""

import logging
import re
from typing import List, Dict, Any, Optional

from .base import StageBase
from ame.foundation.retrieval import RetrievalResult
from ame.foundation.llm import LLMCallerBase

logger = logging.getLogger(__name__)


class SemanticRerankStage(StageBase):
    """
    语义重排序阶段
    
    职责：
    1. 使用 LLM 或规则计算精准相关性
    2. 重新排序结果
    """
    
    def __init__(self, llm_caller: Optional[LLMCallerBase] = None, use_llm: bool = False):
        """
        初始化语义重排序阶段
        
        Args:
            llm_caller: LLM 调用器（可选）
            use_llm: 是否使用 LLM 重排序（默认 False，使用规则）
        """
        self.llm = llm_caller
        self.use_llm = use_llm
        
        logger.debug(f"SemanticRerankStage 初始化 (use_llm={use_llm})")
    
    async def process(
        self,
        query: str,
        previous_results: Optional[List[RetrievalResult]],
        context: Dict[str, Any]
    ) -> List[RetrievalResult]:
        """
        执行语义重排序
        
        Args:
            query: 查询文本
            previous_results: 前序结果
            context: 上下文信息
        
        Returns:
            重排序后的结果
        """
        if not previous_results or len(previous_results) <= 1:
            logger.debug("SemanticRerankStage: 结果数量 <= 1，跳过重排序")
            return previous_results if previous_results else []
        
        logger.debug(f"SemanticRerankStage: 重排序 {len(previous_results)} 个结果")
        
        try:
            if self.use_llm and self.llm:
                reranked = await self._llm_rerank(query, previous_results)
            else:
                reranked = await self._rule_based_rerank(query, previous_results)
            
            logger.info(f"SemanticRerankStage: 重排序完成")
            
            return reranked
            
        except Exception as e:
            logger.error(f"SemanticRerankStage 执行失败: {e}", exc_info=True)
            return previous_results
    
    async def _llm_rerank(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        LLM 重排序
        
        流程：
        1. 构建 Prompt（查询 + 文档列表）
        2. LLM 返回排序索引
        3. 解析并重排序
        """
        # 限制数量，避免 Prompt 过长
        top_results = results[:10]
        
        # 构建 Prompt
        docs_text = "\n\n".join([
            f"文档{i}: {r.content[:200]}..."
            for i, r in enumerate(top_results)
        ])
        
        prompt = f"""根据查询意图，对文档按相关性排序。

查询：{query}

文档列表：
{docs_text}

请返回文档编号，按相关性从高到低，用逗号分隔（例如：0,2,1,3）："""
        
        try:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            # 解析排序
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            indices = [int(n) for n in re.findall(r'\d+', content)]
            
            # 重排序
            reranked = [top_results[i] for i in indices if i < len(top_results)]
            
            # 补充未排序的文档
            remaining = [r for i, r in enumerate(top_results) if i not in indices]
            reranked.extend(remaining)
            
            # 补充原始结果中剩余的文档
            if len(results) > 10:
                reranked.extend(results[10:])
            
            return reranked
            
        except Exception as e:
            logger.error(f"LLM 重排序失败: {e}", exc_info=True)
            return results
    
    async def _rule_based_rerank(
        self,
        query: str,
        results: List[RetrievalResult]
    ) -> List[RetrievalResult]:
        """
        基于规则的重排序（关键词匹配）
        
        规则：
        1. 计算查询关键词与文档的重叠度
        2. 提升分数
        3. 重新排序
        """
        query_words = set(re.findall(r'\w+', query.lower()))
        
        for result in results:
            content_words = set(re.findall(r'\w+', result.content.lower()))
            overlap = len(query_words & content_words)
            
            # 计算重叠率
            overlap_ratio = overlap / max(len(query_words), 1)
            
            # 调整分数（提升 0-10%）
            boost = overlap_ratio * 0.1
            result.score += boost
            
            result.metadata["keyword_overlap"] = overlap
            result.metadata["rerank_boost"] = boost
        
        # 重新排序
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    def get_name(self) -> str:
        return "SemanticRerank"
