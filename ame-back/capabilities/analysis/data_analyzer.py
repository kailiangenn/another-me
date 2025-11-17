"""
统一的数据分析器
整合自：
- analysis/data_analyzer.py
- mem/analyze_engine.py 的分析逻辑

依赖 Foundation Layer:
- HybridEmotionDetector: 情绪分析
- OpenAICaller: LLM 调用
"""
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime

from ame.foundation.nlp.emotion import HybridEmotionDetector
from ame.foundation.llm import OpenAICaller
from ame.models.domain import Document


class DataAnalyzer:
    """
    数据分析器
    
    提供统一的数据分析能力：
    - 情绪分析
    - 关键词提取
    - 统计分析
    - 趋势分析
    """
    
    def __init__(
        self,
        emotion_detector: HybridEmotionDetector,
        llm_caller: OpenAICaller
    ):
        """
        初始化数据分析器
        
        Args:
            emotion_detector: 情绪检测器（来自 foundation.nlp.emotion）
            llm_caller: LLM 调用器（来自 foundation.llm）
        """
        self.emotion = emotion_detector
        self.llm = llm_caller
    
    async def analyze_emotions(
        self,
        documents: List[Document]
    ) -> List[Dict[str, Any]]:
        """
        批量情绪分析
        
        Args:
            documents: 文档列表
        
        Returns:
            情绪分析结果列表
        """
        results = []
        for doc in documents:
            emotion = await self.emotion.detect(
                text=doc.content,
                context={"timestamp": doc.timestamp}
            )
            results.append({
                "doc_id": doc.doc_id,
                "emotion_type": emotion.get("type"),
                "emotion_intensity": emotion.get("intensity"),
                "timestamp": doc.timestamp
            })
        return results
    
    async def extract_keywords(
        self,
        documents: List[Document],
        top_k: int = 10
    ) -> List[str]:
        """
        提取关键词
        
        Args:
            documents: 文档列表
            top_k: 返回前K个关键词
        
        Returns:
            关键词列表
        """
        if not documents:
            return []
        
        # 合并所有文本
        all_text = "\n\n".join([doc.content for doc in documents])
        
        # 使用 LLM 提取关键词
        prompt = f"""从以下文本中提取{top_k}个最重要的关键词。

文本内容：
{all_text[:2000]}  # 限制长度避免超token

要求：
1. 关键词应该是名词或名词短语
2. 按重要性排序
3. 以JSON数组格式返回，例如：["关键词1", "关键词2", "关键词3"]

请直接返回JSON数组，不要有其他说明文字。
"""
        
        try:
            response = await self.llm.generate(prompt, max_tokens=200)
            # 解析 JSON
            import json
            keywords = json.loads(response.strip())
            return keywords[:top_k] if isinstance(keywords, list) else []
        except Exception as e:
            # 降级：使用简单的词频统计
            return self._extract_keywords_by_frequency(documents, top_k)
    
    def _extract_keywords_by_frequency(
        self,
        documents: List[Document],
        top_k: int
    ) -> List[str]:
        """使用词频统计提取关键词（降级方案）"""
        from ame.foundation.utils import clean_text
        
        # 简单分词和统计
        words = []
        for doc in documents:
            cleaned = clean_text(doc.content)
            # 简单按空格分词
            words.extend(cleaned.split())
        
        # 统计词频
        word_freq = Counter(words)
        # 过滤单字和停用词
        filtered = {w: c for w, c in word_freq.items() if len(w) > 1}
        
        return [word for word, _ in Counter(filtered).most_common(top_k)]
    
    async def calculate_statistics(
        self,
        documents: List[Document]
    ) -> Dict[str, Any]:
        """
        计算统计数据
        
        Args:
            documents: 文档列表
        
        Returns:
            统计结果字典
        """
        if not documents:
            return {
                "total_count": 0,
                "avg_length": 0,
                "time_range": (None, None),
                "doc_types": {}
            }
        
        # 基本统计
        total_count = len(documents)
        total_length = sum(len(doc.content) for doc in documents)
        avg_length = total_length / total_count
        
        # 时间范围
        timestamps = [doc.timestamp for doc in documents if doc.timestamp]
        time_range = (
            min(timestamps) if timestamps else None,
            max(timestamps) if timestamps else None
        )
        
        # 文档类型分布
        doc_types = Counter(doc.doc_type.value for doc in documents if doc.doc_type)
        
        return {
            "total_count": total_count,
            "avg_length": avg_length,
            "total_length": total_length,
            "time_range": time_range,
            "doc_types": dict(doc_types)
        }
    
    async def analyze_trends(
        self,
        documents: List[Document],
        time_window_days: int = 7
    ) -> Dict[str, Any]:
        """
        趋势分析
        
        Args:
            documents: 文档列表
            time_window_days: 时间窗口（天）
        
        Returns:
            趋势分析结果
        """
        from datetime import timedelta
        
        if not documents:
            return {"trend": "stable", "change_rate": 0.0}
        
        # 按日期分组
        date_counts = Counter()
        for doc in documents:
            if doc.timestamp:
                date = doc.timestamp.date()
                date_counts[date] += 1
        
        if len(date_counts) < 2:
            return {"trend": "stable", "change_rate": 0.0}
        
        # 计算趋势
        dates = sorted(date_counts.keys())
        recent_avg = sum(date_counts[d] for d in dates[-time_window_days:]) / min(len(dates), time_window_days)
        early_avg = sum(date_counts[d] for d in dates[:time_window_days]) / min(len(dates), time_window_days)
        
        change_rate = (recent_avg - early_avg) / early_avg if early_avg > 0 else 0.0
        
        trend = "increasing" if change_rate > 0.1 else ("decreasing" if change_rate < -0.1 else "stable")
        
        return {
            "trend": trend,
            "change_rate": change_rate,
            "recent_avg": recent_avg,
            "early_avg": early_avg,
            "date_counts": {str(k): v for k, v in date_counts.items()}
        }
