"""
风格化文本生成器 - Capabilities Layer
职责: 根据模板和用户风格生成文本
"""
from typing import Dict, Any, List, Optional

from ame.foundation.llm import OpenAICaller
from ame.capabilities.retrieval import HybridRetriever


class StyleGenerator:
    """风格化文本生成器"""
    
    def __init__(
        self,
        llm_caller: OpenAICaller,
        retriever: Optional[HybridRetriever] = None
    ):
        self.llm = llm_caller
        self.retriever = retriever
    
    async def generate_styled_text(
        self,
        template: str,
        data: Dict[str, Any],
        tone: str = "casual",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成用户风格的文本
        
        Args:
            template: 模板类型 (weekly_report/daily_report/todo_list/mood_support)
            data: 数据字典
            tone: 语气风格 (professional/casual/warm)
            context: 上下文信息
        
        Returns:
            生成的文本
        """
        # 检索相关历史（如果有 retriever）
        relevant_history = []
        if self.retriever:
            query = f"{template} {tone}"
            results = await self.retriever.retrieve(query=query, top_k=3)
            relevant_history = [r.to_dict() for r in results]
        
        # 构建提示词
        system_prompt = self._build_template_prompt(template, tone, relevant_history)
        user_prompt = self._format_template_data(template, data, context)
        
        # 生成文本
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = await self.llm.generate(
            messages=messages,
            temperature=0.7 if tone == "warm" else 0.5
        )
        
        return response.content
    
    def _build_template_prompt(
        self,
        template: str,
        tone: str,
        history: List[Dict]
    ) -> str:
        """构建模板提示词"""
        tone_descriptions = {
            "professional": "专业、简洁、条理清晰",
            "casual": "轻松、自然、接地气",
            "warm": "温暖、关怀、鼓励"
        }
        
        tone_desc = tone_descriptions.get(tone, "自然、真诚")
        
        template_guides = {
            "weekly_report": "生成工作周报，包含关键任务、成就、挑战等内容。使用 Markdown 格式。",
            "daily_report": "生成工作日报，总结今天的工作进展和明日计划。使用 Markdown 格式。",
            "todo_list": "整理待办事项，按优先级分组，每项任务简洁明确。使用 Markdown 格式。",
            "mood_support": "分析心情并提供情绪支持，语气要温暖、共情、鼓励。使用 Markdown 格式。"
        }
        
        template_guide = template_guides.get(template, "生成相关内容")
        
        prompt = f"""你是用户的 AI 分身，任务是：{template_guide}

**语气风格**: {tone_desc}

**注意事项**:
1. 用第一人称"我"来表达
2. 保持{tone_desc}的语气
3. 使用 Markdown 格式输出
4. 不要过于形式化，保持真实感
"""
        
        if history:
            examples = "\n".join([f"- {h.get('content', '')[:80]}..." for h in history[:2]])
            prompt += f"\n**参考用户的历史表达**:\n{examples}\n"
        
        return prompt
    
    def _format_template_data(
        self,
        template: str,
        data: Dict[str, Any],
        context: Optional[Dict]
    ) -> str:
        """格式化模板数据"""
        if template == "weekly_report":
            return f"""请生成本周的工作周报：

**时间范围**: {context.get('period', '未知') if context else '未知'}
**工作记录数**: {context.get('total_logs', 0) if context else 0}

**关键任务**: 
{self._format_list(data.get('key_tasks', []))}

**成就**: 
{self._format_list(data.get('achievements', []))}

**挑战**: 
{self._format_list(data.get('challenges', []))}

请以 Markdown 格式生成完整的周报。
"""
        
        elif template == "mood_support":
            emotion = data.get('emotion', {})
            return f"""请分析以下心情并提供支持：

**情绪类型**: {emotion.get('type', '未知')}
**情绪强度**: {emotion.get('intensity', 0.5) * 10:.1f}/10
**触发因素**: {', '.join(data.get('triggers', [])) or '未知'}
**趋势**: {data.get('trend', {}).get('trend_direction', '稳定') if data.get('trend') else '稳定'}

请以温暖、关怀的语气，提供 2-3 条具体的建议。
"""
        
        else:
            return f"""请根据以下数据生成内容：

{str(data)}
"""
    
    def _format_list(self, items: List) -> str:
        """格式化列表"""
        if not items:
            return "无"
        
        result = ""
        for item in items[:5]:
            if isinstance(item, dict):
                result += f"- {item.get('entity', item.get('content', '未知'))}\n"
            else:
                result += f"- {str(item)}\n"
        return result
