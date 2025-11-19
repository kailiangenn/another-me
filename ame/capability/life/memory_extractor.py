"""
记忆提取器 - 从对话Session中提取重要信息并存入图谱

在对话结束时提取关键信息、实体、情感等，并持久化到Life图谱。
"""

from typing import List, Dict, Optional, Any
from loguru import logger
from datetime import datetime

from ame.foundation.storage import GraphStoreBase, GraphNode, GraphEdge, NodeLabel, RelationType
from ame.foundation.nlp import Summarizer, Entity, EmotionResult, Summary


class MemoryExtractor:
    """记忆提取器
    
    从对话Session中提取并持久化重要信息到图谱。
    """
    
    def __init__(
        self,
        graph_store: GraphStoreBase,
        summarizer: Summarizer
    ):
        """初始化
        
        Args:
            graph_store: 图存储实例
            summarizer: 摘要生成器
        """
        self.graph_store = graph_store
        self.summarizer = summarizer
        logger.debug("MemoryExtractor初始化完成")
    
    async def extract_and_save(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        extract_entities: bool = True,
        analyze_emotions: bool = True
    ) -> Dict[str, Any]:
        """提取并保存记忆
        
        Args:
            session_id: Session ID
            messages: 消息列表
            extract_entities: 是否提取实体
            analyze_emotions: 是否分析情感
            
        Returns:
            提取结果统计
        """
        try:
            logger.info(f"开始提取Session {session_id} 的记忆")
            
            # 1. 生成摘要
            summary = await self.summarizer.summarize_session(
                messages=messages,
                extract_entities=extract_entities,
                analyze_emotions=analyze_emotions
            )
            
            # 2. 保存记忆节点
            memory_node_id = await self._save_memory_node(
                session_id=session_id,
                summary=summary
            )
            
            # 3. 保存实体
            entity_count = 0
            if extract_entities and summary.entities:
                entity_count = await self._save_entities(
                    memory_node_id=memory_node_id,
                    entities=summary.entities
                )
            
            # 4. 保存话题
            topic_count = 0
            if summary.topics:
                topic_count = await self._save_topics(
                    memory_node_id=memory_node_id,
                    topics=summary.topics
                )
            
            # 5. 保存情感
            emotion_count = 0
            if analyze_emotions and summary.emotions:
                emotion_count = await self._save_emotions(
                    memory_node_id=memory_node_id,
                    emotions=summary.emotions
                )
            
            result = {
                "memory_node_id": memory_node_id,
                "summary_length": len(summary.content),
                "key_points": len(summary.key_points),
                "entities": entity_count,
                "topics": topic_count,
                "emotions": emotion_count,
                "session_id": session_id
            }
            
            logger.info(f"记忆提取完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"记忆提取失败: {e}")
            return {
                "error": str(e),
                "session_id": session_id
            }
    
    async def _save_memory_node(
        self,
        session_id: str,
        summary: Summary
    ) -> str:
        """保存记忆节点
        
        Args:
            session_id: Session ID
            summary: 摘要对象
            
        Returns:
            记忆节点ID
        """
        # 创建记忆节点
        memory_node = GraphNode(
            label=NodeLabel.MEMORY,
            properties={
                "session_id": session_id,
                "content": summary.content,
                "summary": summary.content,
                "key_points": summary.key_points,
                "topics": summary.topics,
                "timestamp": datetime.now(),
                "created_at": summary.created_at,
                "source": "life_chat"
            }
        )
        
        node_id = await self.graph_store.create_node(memory_node)
        logger.debug(f"创建记忆节点: {node_id}")
        
        return node_id
    
    async def _save_entities(
        self,
        memory_node_id: str,
        entities: List[Entity]
    ) -> int:
        """保存实体并建立关系
        
        Args:
            memory_node_id: 记忆节点ID
            entities: 实体列表
            
        Returns:
            保存的实体数量
        """
        saved_count = 0
        
        for entity in entities:
            try:
                # 映射实体类型到节点标签
                label_map = {
                    "person": NodeLabel.PERSON,
                    "location": NodeLabel.LOCATION,
                    "organization": NodeLabel.ORGANIZATION,
                    "concept": NodeLabel.CONCEPT,
                    "time": NodeLabel.TIME,
                    "event": NodeLabel.EVENT,
                }
                
                node_label = label_map.get(
                    entity.type.value,
                    NodeLabel.CONCEPT
                )
                
                # 检查实体是否已存在
                existing_nodes = await self.graph_store.find_nodes(
                    label=node_label,
                    properties={"name": entity.text},
                    limit=1
                )
                
                if existing_nodes:
                    # 实体已存在，使用现有节点
                    entity_node_id = existing_nodes[0].id
                else:
                    # 创建新实体节点
                    entity_node = GraphNode(
                        label=node_label,
                        properties={
                            "name": entity.text,
                            "type": entity.type.value,
                            "confidence": entity.confidence,
                            "created_at": datetime.now()
                        }
                    )
                    entity_node_id = await self.graph_store.create_node(entity_node)
                
                # 创建记忆到实体的关系
                edge = GraphEdge(
                    source_id=memory_node_id,
                    target_id=entity_node_id,
                    relation=RelationType.MENTIONS,
                    properties={
                        "created_at": datetime.now()
                    }
                )
                await self.graph_store.create_edge(edge)
                
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"保存实体失败: {entity.text}, 错误: {e}")
        
        return saved_count
    
    async def _save_topics(
        self,
        memory_node_id: str,
        topics: List[str]
    ) -> int:
        """保存话题并建立关系
        
        Args:
            memory_node_id: 记忆节点ID
            topics: 话题列表
            
        Returns:
            保存的话题数量
        """
        saved_count = 0
        
        for topic in topics:
            try:
                # 检查话题是否已存在
                existing_nodes = await self.graph_store.find_nodes(
                    label=NodeLabel.CONCEPT,
                    properties={"name": topic, "type": "topic"},
                    limit=1
                )
                
                if existing_nodes:
                    topic_node_id = existing_nodes[0].id
                else:
                    # 创建话题节点
                    topic_node = GraphNode(
                        label=NodeLabel.CONCEPT,
                        properties={
                            "name": topic,
                            "type": "topic",
                            "created_at": datetime.now()
                        }
                    )
                    topic_node_id = await self.graph_store.create_node(topic_node)
                
                # 创建关系
                edge = GraphEdge(
                    source_id=memory_node_id,
                    target_id=topic_node_id,
                    relation=RelationType.ABOUT,
                    properties={
                        "created_at": datetime.now()
                    }
                )
                await self.graph_store.create_edge(edge)
                
                saved_count += 1
                
            except Exception as e:
                logger.warning(f"保存话题失败: {topic}, 错误: {e}")
        
        return saved_count
    
    async def _save_emotions(
        self,
        memory_node_id: str,
        emotions: List[EmotionResult]
    ) -> int:
        """保存情感信息
        
        Args:
            memory_node_id: 记忆节点ID
            emotions: 情感结果列表
            
        Returns:
            保存的情感数量
        """
        # 简化实现：将情感信息更新到记忆节点属性中
        if not emotions:
            return 0
        
        try:
            # 取第一个情感结果（主要情感）
            emotion = emotions[0]
            
            await self.graph_store.update_node(
                node_id=memory_node_id,
                properties={
                    "emotion": emotion.emotion.value,
                    "emotion_intensity": emotion.intensity,
                    "emotion_valence": emotion.valence
                }
            )
            
            return 1
            
        except Exception as e:
            logger.warning(f"保存情感失败: {e}")
            return 0
    
    async def link_to_user(self, memory_node_id: str) -> bool:
        """将记忆节点关联到用户节点
        
        Args:
            memory_node_id: 记忆节点ID
            
        Returns:
            是否成功
        """
        try:
            # 查找用户节点
            user_nodes = await self.graph_store.find_nodes(
                label=NodeLabel.PERSON,
                properties={"is_user": True},
                limit=1
            )
            
            if not user_nodes:
                logger.warning("未找到用户节点，无法建立关联")
                return False
            
            user_node_id = user_nodes[0].id
            
            # 创建用户到记忆的关系
            edge = GraphEdge(
                source_id=user_node_id,
                target_id=memory_node_id,
                relation=RelationType.HAS_MEMORY,
                properties={
                    "created_at": datetime.now()
                }
            )
            await self.graph_store.create_edge(edge)
            
            logger.debug(f"记忆节点 {memory_node_id} 已关联到用户")
            return True
            
        except Exception as e:
            logger.error(f"关联用户失败: {e}")
            return False
