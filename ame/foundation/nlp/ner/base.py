"""
NER 抽象基类
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class Entity:
    """实体数据结构"""
    text: str                                       # 实体文本
    type: str                                       # 实体类型
    score: float = 1.0                              # 置信度（0-1）
    metadata: Dict = field(default_factory=dict)    # 扩展元数据
    
    def __hash__(self):
        return hash(self.text)
    
    def __eq__(self, other):
        if isinstance(other, Entity):
            return self.text == other.text
        return False
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "text": self.text,
            "type": self.type,
            "score": self.score,
            "metadata": self.metadata
        }


class NERBase(ABC):
    """NER 抽象基类"""
    
    @abstractmethod
    async def extract(self, text: str) -> List[Entity]:
        """提取实体"""
        pass
    
    def filter_entities(
        self,
        entities: List[Entity],
        min_score: float = 0.5,
        min_length: int = 2,
        entity_types: Optional[List[str]] = None
    ) -> List[Entity]:
        """过滤实体"""
        filtered = []
        for entity in entities:
            if entity.score < min_score:
                continue
            if len(entity.text) < min_length:
                continue
            if entity_types and entity.type not in entity_types:
                continue
            filtered.append(entity)
        return filtered
    
    def deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """去重实体（保留高分）"""
        entity_map: Dict[str, Entity] = {}
        for entity in entities:
            if entity.text not in entity_map:
                entity_map[entity.text] = entity
            else:
                if entity.score > entity_map[entity.text].score:
                    entity_map[entity.text] = entity
        return list(entity_map.values())
