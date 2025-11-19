"""
情感分析器 - 基于情感词典和LLM的情感分析
"""

from typing import Dict, List, Optional
from loguru import logger

from ..core import (
    EmotionType,
    EmotionResult,
    EmotionAnalysisError,
)


class EmotionAnalyzer:
    """情感分析器（基于词典+LLM混合策略）"""
    
    def __init__(self, llm_caller=None):
        """初始化
        
        Args:
            llm_caller: LLM调用器（可选）
        """
        self.llm = llm_caller
        self._emotion_dict = self._load_emotion_dict()
    
    def _load_emotion_dict(self) -> Dict[EmotionType, List[str]]:
        """加载情感词典
        
        Returns:
            情绪类型到关键词的映射
        """
        return {
            EmotionType.JOY: [
                "开心", "快乐", "高兴", "喜悦", "兴奋", "愉快", "欣喜",
                "幸福", "满足", "舒心", "愉悦", "欢乐", "哈哈", "😊", "😄",
            ],
            EmotionType.SADNESS: [
                "难过", "伤心", "悲伤", "失落", "沮丧", "低落", "郁闷",
                "痛苦", "心痛", "哭", "泪", "😢", "😭",
            ],
            EmotionType.ANGER: [
                "生气", "愤怒", "气愤", "恼火", "烦躁", "暴躁", "恨",
                "讨厌", "可恶", "😡", "😠",
            ],
            EmotionType.FEAR: [
                "害怕", "恐惧", "担心", "焦虑", "紧张", "不安", "慌张",
                "惊恐", "忧虑", "😰", "😱",
            ],
            EmotionType.SURPRISE: [
                "惊讶", "吃惊", "震惊", "意外", "惊奇", "😲", "😮",
            ],
            EmotionType.DISGUST: [
                "恶心", "厌恶", "反感", "嫌弃", "🤮",
            ],
        }
    
    def _analyze_by_dict(self, text: str) -> EmotionResult:
        """基于词典的情感分析
        
        Args:
            text: 输入文本
            
        Returns:
            情感分析结果
        """
        emotion_scores = {emotion: 0 for emotion in EmotionType if emotion != EmotionType.NEUTRAL}
        matched_keywords = {emotion: [] for emotion in EmotionType if emotion != EmotionType.NEUTRAL}
        
        # 统计每种情绪的关键词匹配数
        for emotion, keywords in self._emotion_dict.items():
            for keyword in keywords:
                count = text.count(keyword)
                if count > 0:
                    emotion_scores[emotion] += count
                    matched_keywords[emotion].append(keyword)
        
        # 找到得分最高的情绪
        max_score = max(emotion_scores.values())
        
        if max_score == 0:
            # 未匹配到任何情感词
            return EmotionResult(
                emotion=EmotionType.NEUTRAL,
                intensity=0.5,
                valence=0.0,
                keywords=[],
                metadata={"method": "dict", "all_scores": emotion_scores}
            )
        
        # 获取得分最高的情绪
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        
        # 计算强度（基于匹配数归一化）
        intensity = min(1.0, max_score / 5.0)  # 最多5个关键词达到最大强度
        
        # 计算效价（正向/负向）
        positive_emotions = {EmotionType.JOY, EmotionType.SURPRISE}
        negative_emotions = {EmotionType.SADNESS, EmotionType.ANGER, EmotionType.FEAR, EmotionType.DISGUST}
        
        if dominant_emotion in positive_emotions:
            valence = intensity
        elif dominant_emotion in negative_emotions:
            valence = -intensity
        else:
            valence = 0.0
        
        return EmotionResult(
            emotion=dominant_emotion,
            intensity=intensity,
            valence=valence,
            keywords=matched_keywords[dominant_emotion],
            metadata={"method": "dict", "all_scores": emotion_scores}
        )
    
    async def _analyze_by_llm(self, text: str) -> EmotionResult:
        """使用LLM进行情感分析
        
        Args:
            text: 输入文本
            
        Returns:
            情感分析结果
        """
        if not self.llm:
            logger.warning("未配置LLM调用器，无法使用LLM情感分析")
            return EmotionResult(
                emotion=EmotionType.NEUTRAL,
                intensity=0.5,
                valence=0.0,
                keywords=[],
                metadata={"method": "default", "reason": "no_llm"}
            )
        
        try:
            prompt = f"""请分析以下文本的情感倾向，从以下情绪类型中选择：
- joy: 喜悦、快乐
- sadness: 悲伤、难过
- anger: 愤怒、生气
- fear: 恐惧、担心
- surprise: 惊讶
- disgust: 厌恶
- neutral: 中性

文本: {text}

请返回JSON格式:
{{
  "emotion": "joy",
  "intensity": 0.8,
  "valence": 0.8
}}

其中intensity为强度(0-1)，valence为效价(-1到1，负向到正向)。只返回JSON，不要其他内容。"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages, max_tokens=100, temperature=0)
            
            # 解析JSON
            import json
            try:
                raw_content = response.content.strip()
                if "```json" in raw_content:
                    raw_content = raw_content.split("```json")[1].split("```")[0].strip()
                elif "```" in raw_content:
                    raw_content = raw_content.split("```")[1].split("```")[0].strip()
                
                emotion_data = json.loads(raw_content)
                
                # 映射情绪类型
                emotion_str = emotion_data.get("emotion", "neutral")
                emotion_map = {
                    "joy": EmotionType.JOY,
                    "sadness": EmotionType.SADNESS,
                    "anger": EmotionType.ANGER,
                    "fear": EmotionType.FEAR,
                    "surprise": EmotionType.SURPRISE,
                    "disgust": EmotionType.DISGUST,
                    "neutral": EmotionType.NEUTRAL,
                }
                emotion = emotion_map.get(emotion_str, EmotionType.NEUTRAL)
                
                intensity = float(emotion_data.get("intensity", 0.5))
                valence = float(emotion_data.get("valence", 0.0))
                
                # 确保在合理范围内
                intensity = max(0.0, min(1.0, intensity))
                valence = max(-1.0, min(1.0, valence))
                
                return EmotionResult(
                    emotion=emotion,
                    intensity=intensity,
                    valence=valence,
                    keywords=[],
                    metadata={"method": "llm", "raw_response": raw_content}
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"LLM返回的JSON格式错误: {e}, 原始内容: {response.content}")
                return EmotionResult(
                    emotion=EmotionType.NEUTRAL,
                    intensity=0.5,
                    valence=0.0,
                    keywords=[],
                    metadata={"method": "llm_failed", "error": str(e)}
                )
                
        except Exception as e:
            logger.error(f"LLM情感分析失败: {e}")
            return EmotionResult(
                emotion=EmotionType.NEUTRAL,
                intensity=0.5,
                valence=0.0,
                keywords=[],
                metadata={"method": "error", "error": str(e)}
            )
    
    async def analyze(self, text: str, use_llm: bool = False) -> EmotionResult:
        """分析情感
        
        Args:
            text: 输入文本
            use_llm: 是否使用LLM增强（默认使用词典）
            
        Returns:
            情感分析结果
        """
        if not text or not text.strip():
            raise EmotionAnalysisError("输入文本不能为空")
        
        # 优先使用LLM（如果启用）
        if use_llm and self.llm:
            return await self._analyze_by_llm(text)
        
        # 否则使用词典
        return self._analyze_by_dict(text)
    
    def analyze_sync(self, text: str) -> EmotionResult:
        """同步分析（仅使用词典）
        
        Args:
            text: 输入文本
            
        Returns:
            情感分析结果
        """
        if not text or not text.strip():
            raise EmotionAnalysisError("输入文本不能为空")
        
        return self._analyze_by_dict(text)
