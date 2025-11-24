"""
摘要生成器 - 基于LLM的对话摘要和关键信息提取

Enhancements:
- 支持多种摘要策略 (extractive/generative/hybrid)
- 支持自定义摘要策略
- 优化的关键点提取算法
"""

from typing import List, Dict, Optional
from enum import Enum
from loguru import logger

from ..core import (
    Summary,
    Entity,
    EmotionResult,
    SummarizationError,
)


class SummaryStrategy(Enum):
    """摘要策略枚举"""
    EXTRACTIVE = "extractive"    # 抽取式：从原文提取关键句
    GENERATIVE = "generative"    # 生成式：用LLM重新生成
    HYBRID = "hybrid"            # 混合式：结合抽取和生成


class Summarizer:
    """摘要生成器（基于LLM）
    
    Enhancements:
    - 支持多种摘要策略
    - 支持自定义摘要函数
    - 优化的关键点提取
    """
    
    def __init__(
        self, 
        llm_caller,
        entity_extractor=None,
        emotion_analyzer=None,
        default_strategy: SummaryStrategy = SummaryStrategy.GENERATIVE
    ):
        """初始化
        
        Args:
            llm_caller: LLM调用器（必需）
            entity_extractor: 实体提取器（可选）
            emotion_analyzer: 情感分析器（可选）
            default_strategy: 默认摘要策略
        """
        if not llm_caller:
            raise SummarizationError("摘要生成器需要LLM调用器")
        
        self.llm = llm_caller
        self.entity_extractor = entity_extractor
        self.emotion_analyzer = emotion_analyzer
        self.strategy = default_strategy
        self.custom_strategy_func = None
    
    def set_strategy(self, strategy: SummaryStrategy) -> None:
        """设置摘要策略
        
        Args:
            strategy: 摘要策略
        """
        self.strategy = strategy
        logger.info(f"设置摘要策略: {strategy.value}")
    
    def set_custom_strategy(
        self,
        strategy_func,
        name: str = "custom"
    ) -> None:
        """设置自定义摘要策略
        
        Args:
            strategy_func: 自定义策略函数 (text: str, max_length: int) -> Dict[str, Any]
            name: 策略名称
        """
        self.custom_strategy_func = strategy_func
        self.strategy = None  # 标记为自定义
        logger.info(f"设置自定义摘要策略: {name}")
    
    async def _summarize_extractive(
        self,
        text: str,
        max_sentences: int = 5
    ) -> Dict[str, any]:
        """抽取式摘要：提取关键句
        
        Args:
            text: 输入文本
            max_sentences: 最多句子数
            
        Returns:
            摘要数据
        """
        import re
        
        # 简单实现：按句子分割并提取最长的几个
        sentences = re.split(r'[\u3002！？\n]', text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        
        # 按长度排序（假设长句更重要）
        sentences.sort(key=len, reverse=True)
        key_sentences = sentences[:max_sentences]
        
        # 提取话题（简单实现）
        topics = []
        if self.entity_extractor:
            entities = await self.entity_extractor.extract(text, use_llm=False, use_backend=True)
            topics = list(set([e.text for e in entities[:5]]))
        
        return {
            "summary": "\n".join(key_sentences),
            "key_points": key_sentences,
            "topics": topics
        }
    
    async def _summarize_generative(
        self,
        text: str,
        max_length: int = 200
    ) -> Dict[str, any]:
        """生成式摘要：用LLM重新生成
        
        Args:
            text: 输入文本
            max_length: 摘要最大长度
            
        Returns:
            摘要数据
        """
        prompt = f"""请为以下文本生成摘要，要求：
1. 提取3-5个关键点
2. 识别主要话题
3. 摘要长度不超过{max_length}字

文本:
{text}

请以JSON格式返回:
{{
  "summary": "摘要内容",
  "key_points": ["关键点1", "关键点2"],
  "topics": ["话题1", "话题2"]
}}

只返回JSON，不要其他内容。"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.generate(messages, max_tokens=500, temperature=0.3)
        
        # 解析响应
        import json
        raw_content = response.content.strip()
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
        
        return json.loads(raw_content)
    
    async def _summarize_hybrid(
        self,
        text: str,
        max_length: int = 200
    ) -> Dict[str, any]:
        """混合式摘要：结合抽取和生成
        
        Args:
            text: 输入文本
            max_length: 摘要最大长度
            
        Returns:
            摘要数据
        """
        # 1. 先用抽取式获取关键句
        extractive_result = await self._summarize_extractive(text, max_sentences=3)
        key_sentences = extractive_result["key_points"]
        
        # 2. 用LLM基于关键句生成摘要
        prompt = f"""基于以下关键信息生成简洁的摘要（不超过{max_length}字）：

关键信息:
{chr(10).join(key_sentences)}

请以JSON格式返回:
{{
  "summary": "摘要内容",
  "key_points": ["关键点1", "关键点2"],
  "topics": ["话题1", "话题2"]
}}

只返回JSON。"""
        
        messages = [{"role": "user", "content": prompt}]
        response = await self.llm.generate(messages, max_tokens=400, temperature=0.3)
        
        # 解析响应
        import json
        raw_content = response.content.strip()
        if "```json" in raw_content:
            raw_content = raw_content.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_content:
            raw_content = raw_content.split("```")[1].split("```")[0].strip()
        
        return json.loads(raw_content)
    
    async def summarize(
        self, 
        text: str,
        max_length: int = 200,
        strategy: Optional[SummaryStrategy] = None
    ) -> Summary:
        """总结单个文本
        
        Args:
            text: 输入文本
            max_length: 摘要最大长度
            strategy: 摘要策略 (默认使用实例策略)
            
        Returns:
            摘要结果
        """
        if not text or not text.strip():
            raise SummarizationError("输入文本不能为空")
        
        # 确定策略
        use_strategy = strategy or self.strategy
        
        try:
            # 根据策略生成摘要
            if self.custom_strategy_func:
                summary_data = self.custom_strategy_func(text, max_length)
                method = "custom"
            elif use_strategy == SummaryStrategy.EXTRACTIVE:
                summary_data = await self._summarize_extractive(text, max_sentences=5)
                method = "extractive"
            elif use_strategy == SummaryStrategy.HYBRID:
                summary_data = await self._summarize_hybrid(text, max_length)
                method = "hybrid"
            else:  # GENERATIVE
                summary_data = await self._summarize_generative(text, max_length)
                method = "generative"
            
            # 提取实体和情感（可选）
            entities = []
            emotions = []
            
            if self.entity_extractor:
                entities = await self.entity_extractor.extract(text, use_llm=False)
            
            if self.emotion_analyzer:
                emotion = await self.emotion_analyzer.analyze(text, use_llm=False)
                emotions.append(emotion)
            
            return Summary(
                content=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points", []),
                entities=entities,
                emotions=emotions,
                topics=summary_data.get("topics", []),
                metadata={"method": method, "source": "text", "strategy": use_strategy.value if use_strategy else "custom"}
            )
            
        except Exception as e:
            logger.error(f"文本摘要生成失败: {e}")
            raise SummarizationError(f"摘要生成失败: {e}")
    
    async def summarize_session(
        self, 
        messages: List[Dict[str, str]],
        extract_entities: bool = True,
        analyze_emotions: bool = True
    ) -> Summary:
        """总结Session对话
        
        用于LifeChat服务在对话终结时提取重要信息
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            extract_entities: 是否提取实体
            analyze_emotions: 是否分析情感
            
        Returns:
            摘要结果
        """
        if not messages:
            raise SummarizationError("消息列表不能为空")
        
        try:
            # 1. 合并所有用户消息
            user_messages = [
                msg['content'] 
                for msg in messages 
                if msg.get('role') == 'user'
            ]
            
            if not user_messages:
                raise SummarizationError("没有找到用户消息")
            
            full_text = "\n".join(user_messages)
            
            # 2. 构建对话摘要提示
            # 包含完整对话上下文以便更好理解
            conversation_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in messages
            ])
            
            prompt = f"""请总结以下对话，提取用户的重要信息：
1. 对话摘要（核心内容）
2. 关键点（3-5个）
3. 讨论的话题
4. 用户提到的重要信息（兴趣、偏好、经历等）

对话内容:
{conversation_text}

请以JSON格式返回:
{{
  "summary": "对话摘要",
  "key_points": ["关键点1", "关键点2"],
  "topics": ["话题1", "话题2"]
}}

只返回JSON，不要其他内容。"""
            
            messages_for_llm = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages_for_llm, max_tokens=500, temperature=0.3)
            
            # 3. 解析响应
            import json
            raw_content = response.content.strip()
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
            summary_data = json.loads(raw_content)
            
            # 4. 提取实体（可选）
            entities = []
            if extract_entities and self.entity_extractor:
                try:
                    entities = await self.entity_extractor.extract(full_text, use_llm=True)
                    logger.debug(f"从对话中提取到 {len(entities)} 个实体")
                except Exception as e:
                    logger.warning(f"实体提取失败: {e}")
            
            # 5. 分析情感（可选）
            emotions = []
            if analyze_emotions and self.emotion_analyzer:
                try:
                    emotion = await self.emotion_analyzer.analyze(full_text, use_llm=False)
                    emotions.append(emotion)
                    logger.debug(f"对话情感: {emotion.emotion.value}, 强度: {emotion.intensity}")
                except Exception as e:
                    logger.warning(f"情感分析失败: {e}")
            
            return Summary(
                content=summary_data.get("summary", ""),
                key_points=summary_data.get("key_points", []),
                entities=entities,
                emotions=emotions,
                topics=summary_data.get("topics", []),
                metadata={
                    "method": "llm",
                    "source": "session",
                    "message_count": len(messages),
                    "user_message_count": len(user_messages)
                }
            )
            
        except Exception as e:
            logger.error(f"对话摘要生成失败: {e}")
            raise SummarizationError(f"对话摘要失败: {e}")
    
    def _extract_key_points(self, summary_text: str) -> List[str]:
        """从摘要文本中提取关键点（备用方法）
        
        Args:
            summary_text: 摘要文本
            
        Returns:
            关键点列表
        """
        # 简单实现：按句子分割
        import re
        sentences = re.split(r'[。！？\n]', summary_text)
        key_points = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 5]
        return key_points[:5]  # 最多5个
    
    def _extract_topics(self, summary_text: str) -> List[str]:
        """从摘要中提取话题（备用方法）
        
        Args:
            summary_text: 摘要文本
            
        Returns:
            话题列表
        """
        # 简单实现：提取关键词作为话题
        # 在实际应用中应该使用更复杂的方法
        return []
