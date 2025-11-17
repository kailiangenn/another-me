"""
洞察生成器
从 mem/analyze_engine.extract_insights 提取

提供从大量数据中提取关键洞察的能力
"""
from typing import List, Dict, Any
from datetime import datetime
from collections import Counter

from ame.foundation.llm import OpenAICaller
from ame.models.domain import Document


class InsightGenerator:
    """
    洞察生成器
    
    从大量数据中提取关键洞察，支持：
    - 关键任务提取
    - 成果总结
    - 挑战识别
    - 时间统计
    """
    
    def __init__(self, llm_caller: OpenAICaller):
        """
        初始化洞察生成器
        
        Args:
            llm_caller: LLM 调用器
        """
        self.llm = llm_caller
    
    async def extract_insights(
        self,
        documents: List[Document],
        metrics: List[str]
    ) -> Dict[str, Any]:
        """
        提取关键洞察
        
        Args:
            documents: 文档列表
            metrics: 需要提取的指标列表，如：
                    ["key_tasks", "achievements", "challenges", "time_stats"]
        
        Returns:
            洞察字典，key为metric名称
        """
        insights = {}
        
        for metric in metrics:
            if metric == "key_tasks":
                insights["key_tasks"] = await self._extract_key_tasks(documents)
            elif metric == "achievements":
                insights["achievements"] = await self._extract_achievements(documents)
            elif metric == "challenges":
                insights["challenges"] = await self._extract_challenges(documents)
            elif metric == "time_stats":
                insights["time_stats"] = self._calculate_time_stats(documents)
            elif metric == "highlights":
                insights["highlights"] = await self._extract_highlights(documents)
        
        return insights
    
    async def _extract_key_tasks(self, documents: List[Document]) -> List[Dict]:
        """提取关键任务"""
        if not documents:
            return []
        
        prompt = self._build_extraction_prompt(
            documents,
            "关键任务",
            "提取文档中提到的重要任务，包括任务名称、描述和状态"
        )
        
        response = await self.llm.generate(prompt, max_tokens=500)
        return self._parse_list_response(response)
    
    async def _extract_achievements(self, documents: List[Document]) -> List[Dict]:
        """提取成果"""
        if not documents:
            return []
        
        prompt = self._build_extraction_prompt(
            documents,
            "成果或完成的工作",
            "提取文档中提到的成果、完成的任务或取得的进展"
        )
        
        response = await self.llm.generate(prompt, max_tokens=500)
        return self._parse_list_response(response)
    
    async def _extract_challenges(self, documents: List[Document]) -> List[str]:
        """提取挑战"""
        if not documents:
            return []
        
        prompt = self._build_extraction_prompt(
            documents,
            "挑战或问题",
            "提取文档中提到的遇到的挑战、问题或困难"
        )
        
        response = await self.llm.generate(prompt, max_tokens=300)
        parsed = self._parse_list_response(response)
        
        # 如果返回的是字典列表，提取title或description
        if parsed and isinstance(parsed[0], dict):
            return [item.get("title") or item.get("description") or str(item) for item in parsed]
        return parsed
    
    async def _extract_highlights(self, documents: List[Document]) -> List[str]:
        """提取亮点"""
        if not documents:
            return []
        
        prompt = self._build_extraction_prompt(
            documents,
            "亮点",
            "提取文档中的重点内容、有价值的信息或值得关注的要点"
        )
        
        response = await self.llm.generate(prompt, max_tokens=300)
        parsed = self._parse_list_response(response)
        
        if parsed and isinstance(parsed[0], dict):
            return [item.get("title") or item.get("description") or str(item) for item in parsed]
        return parsed
    
    def _calculate_time_stats(self, documents: List[Document]) -> Dict[str, Any]:
        """计算时间统计"""
        if not documents:
            return {
                "total_days": 0,
                "total_entries": 0,
                "avg_per_day": 0.0,
                "most_active_date": None
            }
        
        # 按日期分组
        date_counts = Counter()
        for doc in documents:
            if doc.timestamp:
                date = doc.timestamp.date()
                date_counts[date] += 1
        
        total_days = len(date_counts)
        total_entries = len(documents)
        avg_per_day = total_entries / total_days if total_days > 0 else 0.0
        
        most_active = date_counts.most_common(1)
        most_active_date = str(most_active[0][0]) if most_active else None
        
        return {
            "total_days": total_days,
            "total_entries": total_entries,
            "avg_per_day": round(avg_per_day, 2),
            "most_active_date": most_active_date
        }
    
    def _build_extraction_prompt(
        self,
        documents: List[Document],
        target: str,
        instruction: str
    ) -> str:
        """
        构建提取 Prompt
        
        Args:
            documents: 文档列表
            target: 提取目标（如"关键任务"）
            instruction: 提取指令
        """
        # 限制文档数量和长度
        selected_docs = documents[:20]
        content_parts = []
        
        for i, doc in enumerate(selected_docs, 1):
            timestamp = doc.timestamp.strftime("%Y-%m-%d %H:%M") if doc.timestamp else "未知时间"
            content = doc.content[:500]  # 限制每个文档长度
            content_parts.append(f"[{i}] {timestamp}\n{content}")
        
        content = "\n\n".join(content_parts)
        
        return f"""请{instruction}。

文档内容：
{content}

要求：
1. 以JSON数组格式返回
2. 每个项目包含：title（标题）、description（描述）、importance（重要性0.0-1.0）
3. 按重要性降序排列
4. 最多返回5个项目

格式示例：
[
  {{"title": "...", "description": "...", "importance": 0.9}},
  {{"title": "...", "description": "...", "importance": 0.7}}
]

请直接返回JSON数组，不要有其他说明文字。
"""
    
    def _parse_list_response(self, response: str) -> List:
        """解析列表响应"""
        import json
        import re
        
        try:
            # 尝试直接解析
            return json.loads(response.strip())
        except:
            try:
                # 尝试提取JSON部分
                json_match = re.search(r'\[.*\]', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
        
        # 降级：返回空列表
        return []
