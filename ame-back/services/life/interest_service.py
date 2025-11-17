"""
兴趣追踪服务
职责: 兴趣演化分析、推荐生成

设计: 通过 CapabilityFactory 注入能力
"""
from typing import List
from datetime import datetime, timedelta
from collections import Counter
import logging

from ame.capabilities.factory import CapabilityFactory
from ame.capabilities.memory import MemoryManager
from ame.capabilities.generation import StyleGenerator
from ame.capabilities.analysis import InsightGenerator
from ame.models.report_models import InterestReport, InterestTopic

logger = logging.getLogger(__name__)


class InterestService:
    """兴趣追踪服务"""
    
    def __init__(self, capability_factory: CapabilityFactory):
        self.factory = capability_factory
        self.ner = factory.ner
        self.memory_manager = factory.create_memory_manager(cache_key="interest_memory")
        self.style_generator = factory.create_style_generator(with_retriever=True, cache_key="interest_style")
        self.insight_generator = factory.create_insight_generator(cache_key="interest_insight")
        logger.info("InterestService 初始化完成")
    
    async def track_interests(
        self,
        user_id: str,
        period_days: int = 30
    ) -> InterestReport:
        """
        追踪兴趣爱好演化
        
        Args:
            user_id: 用户ID
            period_days: 统计时间范围（天）
        
        Returns:
            InterestReport: 兴趣追踪报告
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        # Step 1: 收集数据
        life_records = await self.memory_manager.retrieve(
            query="兴趣 爱好 活动",
            top_k=100,
            filters={"category": "life", "tags": [user_id]}
        )
        
        if not life_records:
            return InterestReport(
                user_id=user_id,
                period_days=period_days,
                report="暂无数据"
            )
        
        # Step 2: 提取实体和主题
        all_entities = []
        entity_timestamps = {}
        
        for doc in life_records:
            entities = doc.entities if hasattr(doc, 'entities') else []
            all_entities.extend(entities)
            for entity in entities:
                if entity not in entity_timestamps:
                    entity_timestamps[entity] = []
                entity_timestamps[entity].append(doc.timestamp)
        
        # Step 3: 频率统计
        entity_freq = Counter(all_entities)
        
        # Step 4: 生成兴趣主题
        top_interests = []
        for entity, count in entity_freq.most_common(10):
            timestamps = entity_timestamps.get(entity, [])
            if timestamps:
                top_interests.append(InterestTopic(
                    topic=entity,
                    frequency=count,
                    first_mentioned=min(timestamps),
                    last_mentioned=max(timestamps),
                    trend="stable"
                ))
        
        # Step 5: 识别新兴趣和衰减兴趣
        new_interests, declining_interests = await self._analyze_interest_evolution(
            user_id, period_days
        )
        
        # Step 6: 生成推荐
        recommendations = await self.style_generator.generate_styled_text(
            template="interest_recommendations",
            data={"topics": [t.topic for t in top_interests[:3]], "new_interests": new_interests},
            tone="casual"
        )
        
        # Step 7: 生成报告
        report = self._generate_report(
            top_interests, new_interests, declining_interests, period_days
        )
        
        return InterestReport(
            user_id=user_id,
            period_days=period_days,
            top_interests=top_interests,
            new_interests=new_interests,
            declining_interests=declining_interests,
            recommendations=recommendations,
            report=report,
            generated_at=datetime.now()
        )
    
    async def _analyze_interest_evolution(
        self,
        user_id: str,
        current_period_days: int
    ) -> tuple:
        """分析兴趣演化"""
        end_date = datetime.now()
        current_start = end_date - timedelta(days=current_period_days)
        previous_start = current_start - timedelta(days=current_period_days)
        
        current_docs = await self.memory.retrieve_by_timerange(
            start_time=current_start,
            end_time=end_date,
            filters={"user_id": user_id}
        )
        
        previous_docs = await self.memory.retrieve_by_timerange(
            start_time=previous_start,
            end_time=current_start,
            filters={"user_id": user_id}
        )
        
        current_entity_freq = Counter()
        for doc in current_docs:
            entities = doc.entities if hasattr(doc, 'entities') else []
            current_entity_freq.update(entities)
        
        previous_entity_freq = Counter()
        for doc in previous_docs:
            entities = doc.entities if hasattr(doc, 'entities') else []
            previous_entity_freq.update(entities)
        
        new_interests = []
        for entity, count in current_entity_freq.most_common(20):
            prev_count = previous_entity_freq.get(entity, 0)
            if count >= 2 and (prev_count == 0 or count > prev_count * 2):
                new_interests.append(entity)
        
        declining_interests = []
        for entity, count in previous_entity_freq.most_common(20):
            curr_count = current_entity_freq.get(entity, 0)
            if count >= 3 and (curr_count == 0 or curr_count < count * 0.5):
                declining_interests.append(entity)
        
        return new_interests[:5], declining_interests[:5]
    
    async def _generate_recommendations(
        self,
        top_interests: List[InterestTopic],
        new_interests: List[str]
    ) -> List[str]:
        """生成兴趣推荐"""
        if not top_interests:
            return []
        
        topics = [t.topic for t in top_interests[:3]]
        recommendations_text = await self.generator.generate(
            template="interest_recommendations",
            data={
                "topics": topics,
                "new_interests": new_interests
            }
        )
        
        return [line.strip("- ").strip() for line in recommendations_text.split("\n") if line.strip()][:5]
    
    def _generate_report(
        self,
        top_interests: List[InterestTopic],
        new_interests: List[str],
        declining_interests: List[str],
        period_days: int
    ) -> str:
        """生成兴趣追踪报告"""
        report = f"# 兴趣追踪报告（最近 {period_days} 天）\n\n"
        
        if top_interests:
            report += "## 主要兴趣\n\n"
            for interest in top_interests[:5]:
                report += f"- **{interest.topic}**: 提及 {interest.frequency} 次\n"
            report += "\n"
        
        if new_interests:
            report += "## 新兴趣\n\n"
            for interest in new_interests:
                report += f"- {interest}\n"
            report += "\n"
        
        if declining_interests:
            report += "## 兴趣减弱\n\n"
            for interest in declining_interests:
                report += f"- {interest}\n"
            report += "\n"
        
        return report
