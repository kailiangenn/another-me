"""
心情分析服务

职责: 情绪识别、趋势分析、建议生成

设计理念:
- 通过 CapabilityFactory 注入能力
- 使用 life_capability_bundle 预设包
- 遵循依赖注入和单一职责原则
"""
from typing import Dict, List
from datetime import datetime, timedelta
import logging

from ame.capabilities.factory import CapabilityFactory
from ame.capabilities.analysis import DataAnalyzer
from ame.capabilities.generation import StyleGenerator
from ame.capabilities.memory import MemoryManager
from ame.foundation.nlp.emotion import HybridEmotionDetector
from ame.models.report_models import MoodAnalysis, MoodTrend

logger = logging.getLogger(__name__)


class MoodService:
    """
    心情分析服务
    
    职责:
    - 情绪识别与分析
    - 情绪趋势追踪
    - 个性化建议生成
    
    设计:
    - 通过 CapabilityFactory 注入能力
    - 使用温暖风格的 StyleGenerator
    - 利用 DataAnalyzer 进行趋势分析
    """
    
    def __init__(
        self,
        capability_factory: CapabilityFactory
    ):
        """
        初始化心情分析服务
        
        Args:
            capability_factory: 能力工厂实例(注入)
        
        Example:
            >>> factory = CapabilityFactory(...)
            >>> mood_service = MoodService(capability_factory=factory)
        """
        self.factory = capability_factory
        
        # 从 factory 获取基础能力
        self.emotion_detector = HybridEmotionDetector(
            llm_caller=factory.llm,
            config={"use_llm": True}
        )
        
        # 使用 factory 创建高级能力
        self.analyzer = factory.create_data_analyzer(
            with_retriever=False,  # 心情分析不需要检索增强
            cache_key="mood_analyzer"
        )
        
        self.style_generator = factory.create_style_generator(
            with_retriever=True,  # 用于学习用户的表达风格
            cache_key="mood_style_generator"
        )
        
        self.memory_manager = factory.create_memory_manager(
            cache_key="mood_memory"
        )
        
        logger.info("MoodService 初始化完成(使用 CapabilityFactory)")
    
    async def analyze_mood(
        self,
        mood_entry: str,
        user_id: str,
        entry_time: datetime
    ) -> MoodAnalysis:
        """
        分析心情日记
        
        流程:
        1. 情绪识别 (HybridEmotionDetector)
        2. 触发因素分析 (LLM 提取)
        3. 历史趋势对比 (MemoryManager + DataAnalyzer)
        4. 生成温暖建议 (StyleGenerator)
        
        Args:
            mood_entry: 心情记录文本
            user_id: 用户ID
            entry_time: 记录时间
        
        Returns:
            MoodAnalysis: 心情分析结果
        """
        # Step 1: 情绪识别
        emotion_result = await self.emotion_detector.detect(
            text=mood_entry,
            context={"time": entry_time}
        )
        
        logger.debug(f"情绪识别: {emotion_result['type']}, 强度={emotion_result['intensity']:.2f}")
        
        # Step 2: 触发因素分析
        triggers = await self._extract_triggers(mood_entry)
        
        # Step 3: 历史对比
        mood_trend = await self._analyze_mood_trend(
            user_id=user_id,
            current_emotion=emotion_result,
            days=7
        )
        
        # Step 4: 生成温暖建议
        suggestions = await self.style_generator.generate_styled_text(
            template="mood_support",
            data={
                "emotion": emotion_result,
                "triggers": triggers,
                "trend": mood_trend
            },
            tone="warm",  # 温暖、关怀的语气
            context={"user_id": user_id}
        )
        
        logger.info(f"完成心情分析: user={user_id}, emotion={emotion_result['type']}")
        
        return MoodAnalysis(
            emotion_type=emotion_result["type"],
            emotion_intensity=emotion_result["intensity"],
            triggers=triggers,
            trend=mood_trend,
            suggestions=suggestions,
            analysis_time=datetime.now()
        )
    
    async def _extract_triggers(self, mood_entry: str) -> List[str]:
        """
        提取情绪触发因素
        
        使用 LLM 分析情绪触发原因
        
        Args:
            mood_entry: 心情记录
        
        Returns:
            triggers: 触发因素列表
        """
        try:
            prompt = f"""分析以下心情记录,提取情绪的主要触发因素。

心情记录:
{mood_entry}

请列出 2-3 个主要触发因素,每行一个,简洁明了。"""
            
            response = await self.factory.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # 解析触发因素
            triggers = [
                line.strip("- ").strip()
                for line in response.content.split("\n")
                if line.strip() and not line.strip().startswith("#")
            ]
            
            return triggers[:3]
        
        except Exception as e:
            logger.error(f"提取触发因素失败: {e}")
            return []
    
    async def _analyze_mood_trend(
        self,
        user_id: str,
        current_emotion: Dict,
        days: int = 7
    ) -> MoodTrend:
        """
        分析情绪趋势
        
        对比最近N天的情绪变化,判断趋势方向
        
        Args:
            user_id: 用户ID
            current_emotion: 当前情绪
            days: 统计天数
        
        Returns:
            MoodTrend: 情绪趋势
        """
        start_date = datetime.now() - timedelta(days=days)
        
        # 使用 MemoryManager 检索历史心情记录
        try:
            mood_memories = await self.memory_manager.retrieve(
                query="心情 情绪 感受",  # 通用查询
                top_k=50,
                filters={
                    "category": "mood",
                    "tags": [user_id]
                }
            )
            
            # 过滤时间范围
            recent_memories = [
                m for m in mood_memories
                if m.timestamp >= start_date
            ]
            
        except Exception as e:
            logger.warning(f"检索历史心情失败: {e}")
            recent_memories = []
        
        # 提取历史情绪数据
        historical_emotions = []
        for memory in recent_memories:
            emotion_data = memory.metadata.get("emotion")
            if emotion_data:
                historical_emotions.append({
                    "type": emotion_data.get("type", "neutral"),
                    "intensity": emotion_data.get("intensity", 0.5),
                    "date": memory.timestamp
                })
        
        # 趋势分析
        if len(historical_emotions) >= 3:
            avg_intensity = sum(e["intensity"] for e in historical_emotions) / len(historical_emotions)
            current_intensity = current_emotion.get("intensity", 0.5)
            
            if current_intensity > avg_intensity + 0.2:
                direction = "improving"  # 情绪改善
            elif current_intensity < avg_intensity - 0.2:
                direction = "declining"  # 情绪下降
            else:
                direction = "stable"  # 稳定
            
            # 预警机制
            alert = direction == "declining" and current_intensity < 0.3
        else:
            # 数据不足
            avg_intensity = current_emotion.get("intensity", 0.5)
            direction = "stable"
            alert = False
        
        logger.debug(
            f"情绪趋势: direction={direction}, "
            f"avg={avg_intensity:.2f}, current={current_intensity:.2f}"
        )
        
        return MoodTrend(
            current_emotion=current_emotion.get("type", "neutral"),
            average_intensity=avg_intensity,
            trend_direction=direction,
            alert=alert
        )
