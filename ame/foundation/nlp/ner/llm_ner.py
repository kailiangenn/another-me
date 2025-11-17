"""
LLM NER - 基于 LLM 的精确实体识别

特性：
- 精确识别
- 支持复杂实体
- JSON 结构化输出
"""

import logging
import json
from typing import List

from ame.foundation.llm import LLMCallerBase
from .base import NERBase, Entity

logger = logging.getLogger(__name__)


class LLMNER(NERBase):
    """基于 LLM 的精确实体识别"""
    
    def __init__(self, llm_caller: LLMCallerBase, temperature: float = 0.1):
        self.llm = llm_caller
        self.temperature = temperature
    
    async def extract(self, text: str) -> List[Entity]:
        """提取实体"""
        if not text:
            return []
        
        prompt = f"""从以下文本中提取关键实体，返回 JSON 格式。

文本: {text}

返回格式: [{{"text": "实体", "type": "类型", "score": 0.95}}]

类型包括: PERSON, LOCATION, ORGANIZATION, TOPIC, OTHER

只返回 JSON，不要其他内容。"""
        
        try:
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            
            data = json.loads(content)
            
            entities = []
            for item in data:
                entities.append(Entity(
                    text=item["text"],
                    type=item["type"],
                    score=item.get("score", 0.9),
                    metadata={"method": "llm"}
                ))
            
            return entities
        
        except Exception as e:
            logger.error(f"LLM NER 失败: {e}")
            return []
