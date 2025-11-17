"""
会议纪要服务
职责: 会议内容结构化提取
"""
from typing import List, Dict, Optional
from datetime import datetime
import json
import re

from ame.capabilities.factory import CapabilityFactory


class MeetingService:
    """会议纪要服务"""
    
    def __init__(self, capability_factory: CapabilityFactory):
        """初始化会议纪要服务
        
        Args:
            capability_factory: 能力工厂实例
        """
        self.factory = capability_factory
        self.llm = capability_factory.llm
    
    async def summarize(
        self,
        meeting_content: str,
        meeting_date: datetime,
        participants: Optional[List[str]] = None
    ) -> Dict[str, any]:
        """
        会议内容结构化总结
        
        Args:
            meeting_content: 会议记录原文
            meeting_date: 会议日期
            participants: 参与者列表
        
        Returns:
            structured_summary: {
                'summary': str,
                'key_points': List[str],
                'decisions': List[str],
                'action_items': List[Dict],
                'formatted_minutes': str
            }
        """
        prompt = f"""请从以下会议记录中提取关键信息，以JSON格式返回：

**会议时间**: {meeting_date.strftime('%Y-%m-%d %H:%M')}
**参与者**: {', '.join(participants) if participants else '未记录'}

**会议内容**:
{meeting_content}

请提取以下信息并以JSON格式返回：
{{
  "summary": "会议核心摘要（2-3句话）",
  "key_points": ["要点1", "要点2", "要点3"],
  "decisions": ["决策1", "决策2"],
  "action_items": [
    {{"task": "任务描述", "owner": "负责人", "deadline": "截止日期或空字符串"}}
  ]
}}

只返回JSON，不要其他内容。
"""
        
        try:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            json_match = re.search(r'\{[^}]+\}', response.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {
                    "summary": meeting_content[:100] + "...",
                    "key_points": [],
                    "decisions": [],
                    "action_items": []
                }
            
            formatted_minutes = self._format_meeting_minutes(
                meeting_date, participants, data
            )
            
            return {
                **data,
                'formatted_minutes': formatted_minutes
            }
        
        except Exception as e:
            return {
                'summary': meeting_content[:100] + "...",
                'key_points': [],
                'decisions': [],
                'action_items': [],
                'formatted_minutes': f"# 会议纪要\n\n{meeting_content}",
                'error': str(e)
            }
    
    def _format_meeting_minutes(
        self,
        meeting_date: datetime,
        participants: Optional[List[str]],
        data: Dict[str, any]
    ) -> str:
        """生成 Markdown 格式会议纪要"""
        minutes = f"# 会议纪要\n\n"
        minutes += f"**时间**: {meeting_date.strftime('%Y年%m月%d日 %H:%M')}\n\n"
        
        if participants:
            minutes += f"**参与者**: {', '.join(participants)}\n\n"
        
        minutes += f"## 会议摘要\n\n{data.get('summary', '无')}\n\n"
        
        if data.get('key_points'):
            minutes += "## 关键要点\n\n"
            for point in data['key_points']:
                minutes += f"- {point}\n"
            minutes += "\n"
        
        if data.get('decisions'):
            minutes += "## 决策事项\n\n"
            for decision in data['decisions']:
                minutes += f"- {decision}\n"
            minutes += "\n"
        
        if data.get('action_items'):
            minutes += "## 行动项\n\n"
            for item in data['action_items']:
                task = item.get('task', '')
                owner = item.get('owner', '未指定')
                deadline = item.get('deadline', '待定')
                minutes += f"- **{task}** (负责人: {owner}, 截止: {deadline})\n"
            minutes += "\n"
        
        return minutes
