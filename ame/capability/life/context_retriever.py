"""
上下文检索器 - 从图谱中检索相关上下文信息

用于Life对话服务中根据用户意图检索相关历史信息。
"""

from typing import List, Dict, Optional, Any
from loguru import logger
from datetime import datetime

from ame.foundation.storage import GraphStoreBase, NodeLabel, RelationType
from ame.foundation.nlp import IntentType, Entity


class ContextRetriever:
    """上下文检索器
    
    从Life图谱中检索与当前对话相关的上下文信息。
    """
    
    def __init__(self, graph_store: GraphStoreBase):
        """初始化
        
        Args:
            graph_store: 图存储实例
        """
        self.graph_store = graph_store
        logger.debug("ContextRetriever初始化完成")
    
    async def retrieve_by_intent(
        self,
        intent: IntentType,
        entities: Optional[List[Entity]] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """根据意图检索上下文
        
        Args:
            intent: 意图类型
            entities: 提取的实体列表
            limit: 返回结果数量限制
            
        Returns:
            上下文信息列表
        """
        contexts = []
        
        try:
            if intent == IntentType.QUERY_SELF:
                # 查询用户自己的信息（兴趣、性格等）
                contexts = await self._retrieve_user_profile(limit=limit)
                
            elif intent == IntentType.COMFORT:
                # 需要安慰时，检索过往相似情绪的对话
                contexts = await self._retrieve_similar_emotions(limit=limit)
                
            elif intent == IntentType.ANALYZE:
                # 分析请求，检索用户的行为模式
                contexts = await self._retrieve_behavior_patterns(limit=limit)
                
            else:
                # 普通聊天，检索最近的对话记忆
                contexts = await self._retrieve_recent_memories(limit=limit)
            
            logger.debug(f"检索到 {len(contexts)} 条上下文信息")
            return contexts
            
        except Exception as e:
            logger.error(f"上下文检索失败: {e}")
            return []
    
    async def _retrieve_user_profile(self, limit: int = 5) -> List[Dict[str, Any]]:
        """检索用户画像信息
        
        Args:
            limit: 限制数量
            
        Returns:
            用户画像信息列表
        """
        try:
            # 查找用户节点
            user_nodes = await self.graph_store.find_nodes(
                label=NodeLabel.PERSON,
                properties={"is_user": True},
                limit=1
            )
            
            if not user_nodes:
                logger.warning("未找到用户节点")
                return []
            
            user_node = user_nodes[0]
            contexts = []
            
            # 获取用户的兴趣
            interests = await self.graph_store.get_neighbors(
                node_id=user_node.id,
                direction="outgoing",
                relation_type=RelationType.INTERESTED_IN,
                limit=limit
            )
            
            for interest in interests:
                contexts.append({
                    "type": "interest",
                    "content": interest.properties.get("name", ""),
                    "metadata": interest.properties
                })
            
            # 获取用户特征
            if "personality" in user_node.properties:
                contexts.append({
                    "type": "personality",
                    "content": user_node.properties["personality"],
                    "metadata": {"source": "user_profile"}
                })
            
            return contexts
            
        except Exception as e:
            logger.error(f"检索用户画像失败: {e}")
            return []
    
    async def _retrieve_similar_emotions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """检索相似情绪的历史对话
        
        Args:
            limit: 限制数量
            
        Returns:
            相似情绪的对话列表
        """
        try:
            # 查找带有负面情绪的记忆节点
            memory_nodes = await self.graph_store.find_nodes(
                label=NodeLabel.MEMORY,
                limit=limit * 2  # 多获取一些以便筛选
            )
            
            contexts = []
            for node in memory_nodes:
                emotion = node.properties.get("emotion")
                if emotion in ["sadness", "fear", "anger"]:
                    contexts.append({
                        "type": "emotion_memory",
                        "content": node.properties.get("content", ""),
                        "emotion": emotion,
                        "timestamp": node.properties.get("timestamp"),
                        "metadata": node.properties
                    })
            
            # 按时间倒序排列，返回最近的
            contexts.sort(
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )
            
            return contexts[:limit]
            
        except Exception as e:
            logger.error(f"检索相似情绪失败: {e}")
            return []
    
    async def _retrieve_behavior_patterns(self, limit: int = 5) -> List[Dict[str, Any]]:
        """检索用户行为模式
        
        Args:
            limit: 限制数量
            
        Returns:
            行为模式列表
        """
        try:
            # 查找事件节点
            event_nodes = await self.graph_store.find_nodes(
                label=NodeLabel.EVENT,
                limit=limit * 2
            )
            
            contexts = []
            for node in event_nodes:
                contexts.append({
                    "type": "behavior",
                    "content": node.properties.get("description", ""),
                    "event_type": node.properties.get("event_type"),
                    "timestamp": node.properties.get("timestamp"),
                    "metadata": node.properties
                })
            
            # 按时间倒序
            contexts.sort(
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )
            
            return contexts[:limit]
            
        except Exception as e:
            logger.error(f"检索行为模式失败: {e}")
            return []
    
    async def _retrieve_recent_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """检索最近的对话记忆
        
        Args:
            limit: 限制数量
            
        Returns:
            最近记忆列表
        """
        try:
            # 查找最近的记忆节点
            memory_nodes = await self.graph_store.find_nodes(
                label=NodeLabel.MEMORY,
                limit=limit
            )
            
            contexts = []
            for node in memory_nodes:
                contexts.append({
                    "type": "recent_memory",
                    "content": node.properties.get("content", ""),
                    "summary": node.properties.get("summary", ""),
                    "timestamp": node.properties.get("timestamp"),
                    "metadata": node.properties
                })
            
            # 按时间倒序
            contexts.sort(
                key=lambda x: x.get("timestamp", datetime.min),
                reverse=True
            )
            
            return contexts[:limit]
            
        except Exception as e:
            logger.error(f"检索最近记忆失败: {e}")
            return []
    
    async def retrieve_by_keywords(
        self,
        keywords: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """根据关键词检索上下文
        
        Args:
            keywords: 关键词列表
            limit: 限制数量
            
        Returns:
            相关上下文列表
        """
        # 简化实现：查找包含关键词的节点
        # 实际应该使用向量检索或全文检索
        contexts = []
        
        try:
            for keyword in keywords:
                # 查找包含关键词的记忆节点
                nodes = await self.graph_store.find_nodes(
                    label=NodeLabel.MEMORY,
                    limit=limit
                )
                
                for node in nodes:
                    content = node.properties.get("content", "")
                    if keyword.lower() in content.lower():
                        contexts.append({
                            "type": "keyword_match",
                            "content": content,
                            "keyword": keyword,
                            "metadata": node.properties
                        })
            
            # 去重
            seen = set()
            unique_contexts = []
            for ctx in contexts:
                key = ctx["content"]
                if key not in seen:
                    seen.add(key)
                    unique_contexts.append(ctx)
            
            return unique_contexts[:limit]
            
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []
