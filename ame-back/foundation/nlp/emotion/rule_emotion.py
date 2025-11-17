"""
规则情绪识别器

基于关键词词典进行情绪识别

特性：
- 快速识别（毫秒级）
- 基于词典匹配
- 支持中英文
- 可扩展词典

从 analysis/data_analyzer.py 提取并优化
"""

import logging
from typing import Dict, Any, Optional, Set

from .base import EmotionDetectorBase, EmotionResult, EmotionType

logger = logging.getLogger(__name__)


class RuleEmotionDetector(EmotionDetectorBase):
    """
    规则情绪识别器
    
    使用关键词匹配识别情绪
    """
    
    def __init__(
        self,
        positive_words: Optional[Set[str]] = None,
        negative_words: Optional[Set[str]] = None
    ):
        """
        初始化规则情绪识别器
        
        Args:
            positive_words: 积极词典（可选，使用默认词典）
            negative_words: 消极词典（可选，使用默认词典）
        """
        # 积极词典（中英文）
        self.positive_words = positive_words or {
            # 中文
            '开心', '快乐', '高兴', '喜欢', '爱', '好', '棒', '赞', '哈哈',
            '兴奋', '激动', '满意', '幸福', '愉快', '欢乐', '舒服', '美好',
            '太好了', '不错', '很棒', '完美', '优秀', '精彩', '赞同',
            # 英文
            'happy', 'joy', 'love', 'like', 'good', 'great', 'awesome',
            'excellent', 'wonderful', 'fantastic', 'perfect', 'amazing',
            'excited', 'glad', 'pleased', 'delighted', 'satisfied'
        }
        
        # 消极词典（中文 + 英文）
        self.negative_words = negative_words or {
            # 中文
            '难过', '伤心', '痛苦', '讨厌', '恨', '差', '烂', '糟', '唉',
            '失望', '沮丧', '郁闷', '焦虑', '害怕', '担心', '烦', '累',
            '不好', '不行', '失败', '错误', '问题', '糟糕', '可怕',
            # 英文
            'sad', 'unhappy', 'bad', 'terrible', 'awful', 'horrible',
            'disappointed', 'frustrated', 'angry', 'hate', 'dislike',
            'worried', 'anxious', 'afraid', 'scared', 'upset', 'depressed'
        }
        
        logger.info(
            f"规则情绪识别器初始化 "
            f"(positive={len(self.positive_words)}, negative={len(self.negative_words)})"
        )
    
    async def detect(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionResult:
        """
        基于规则识别情绪
        
        算法：
        1. 统计积极词和消极词出现次数
        2. 根据比例判断情绪类型
        3. 根据总数判断情绪强度
        4. 根据匹配词数判断置信度
        
        Args:
            text: 输入文本
            context: 上下文（未使用）
        
        Returns:
            result: 情绪识别结果
        """
        if not text:
            return EmotionResult(
                type=EmotionType.NEUTRAL.value,
                intensity=0.5,
                confidence=0.5,
                metadata={"method": "rule", "reason": "empty_text"}
            )
        
        # 转换为小写（英文匹配）
        text_lower = text.lower()
        
        # 统计关键词
        positive_count = sum(1 for word in self.positive_words if word in text_lower)
        negative_count = sum(1 for word in self.negative_words if word in text_lower)
        total_count = positive_count + negative_count
        
        # 判断情绪类型
        if positive_count > negative_count:
            emotion_type = EmotionType.POSITIVE.value
            dominant_count = positive_count
        elif negative_count > positive_count:
            emotion_type = EmotionType.NEGATIVE.value
            dominant_count = negative_count
        else:
            emotion_type = EmotionType.NEUTRAL.value
            dominant_count = 0
        
        # 计算情绪强度（基于主导情绪词数量）
        # 1个词: 0.6, 2个词: 0.75, 3+个词: 0.9
        if dominant_count == 0:
            intensity = 0.5  # 中性
        elif dominant_count == 1:
            intensity = 0.6
        elif dominant_count == 2:
            intensity = 0.75
        else:
            intensity = min(0.9, 0.6 + dominant_count * 0.1)
        
        # 计算置信度（基于总匹配词数和文本长度）
        text_length = len(text)
        if total_count == 0:
            # 没有匹配到任何情绪词，置信度较低
            confidence = 0.4
        elif total_count == 1:
            # 匹配到1个词，置信度中等
            confidence = 0.6
        elif total_count == 2:
            # 匹配到2个词，置信度较高
            confidence = 0.75
        else:
            # 匹配到3+个词，置信度高
            confidence = min(0.9, 0.6 + total_count * 0.1)
        
        # 如果文本很短但匹配到词，提升置信度
        if text_length < 20 and total_count > 0:
            confidence = min(1.0, confidence + 0.1)
        
        # 如果是中性但文本较长，降低置信度（可能需要 LLM 分析）
        if emotion_type == EmotionType.NEUTRAL.value and text_length > 50:
            confidence = 0.5
        
        logger.debug(
            f"规则情绪识别: {emotion_type} "
            f"(positive={positive_count}, negative={negative_count}, "
            f"intensity={intensity:.2f}, confidence={confidence:.2f})"
        )
        
        return EmotionResult(
            type=emotion_type,
            intensity=intensity,
            confidence=confidence,
            metadata={
                "method": "rule",
                "positive_count": positive_count,
                "negative_count": negative_count,
                "text_length": text_length
            }
        )
    
    def get_detector_name(self) -> str:
        """获取识别器名称"""
        return "RuleEmotionDetector"
    
    def add_positive_words(self, words: Set[str]):
        """添加积极词"""
        self.positive_words.update(words)
        logger.info(f"添加 {len(words)} 个积极词")
    
    def add_negative_words(self, words: Set[str]):
        """添加消极词"""
        self.negative_words.update(words)
        logger.info(f"添加 {len(words)} 个消极词")
