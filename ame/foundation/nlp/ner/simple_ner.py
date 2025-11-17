"""
Simple NER - 基于 jieba 的快速实体识别

特性：
- 快速识别（基于词性标注）
- 轻量级（无需 LLM）
- 支持中文
"""

import logging
from typing import List

from .base import NERBase, Entity

logger = logging.getLogger(__name__)


class SimpleNER(NERBase):
    """基于 jieba 的快速实体识别"""
    
    POS_TO_TYPE = {
        "nr": "PERSON",
        "ns": "LOCATION",
        "nt": "ORGANIZATION",
        "nz": "OTHER",
        "n": "TOPIC",
        "vn": "TOPIC",
        "eng": "TOPIC",
    }
    
    def __init__(self, min_length: int = 2, extract_nouns: bool = True):
        self.min_length = min_length
        self.extract_nouns = extract_nouns
        
        try:
            import jieba.posseg as posseg
            self.posseg = posseg
        except ImportError:
            raise ImportError("需要安装 jieba: pip install jieba")
    
    async def extract(self, text: str) -> List[Entity]:
        """提取实体"""
        if not text:
            return []
        
        entities = []
        words = self.posseg.cut(text)
        
        for word, pos in words:
            if len(word) < self.min_length:
                continue
            
            entity_type = self.POS_TO_TYPE.get(pos)
            if entity_type:
                entities.append(Entity(
                    text=word,
                    type=entity_type,
                    score=0.8,
                    metadata={"method": "jieba", "pos": pos}
                ))
        
        return self.deduplicate_entities(entities)
