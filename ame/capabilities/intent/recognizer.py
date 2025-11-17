"""
IntentRecognizer - 意图识别器实现
"""
from typing import Optional, Dict, Any
import logging
import re

from ame.foundation.llm import LLMCallerBase
from ame.foundation.nlp.ner import NERBase
from ame.foundation.inference import CascadeInferenceEngine, InferenceLevelBase, InferenceResult
from ame.foundation.utils import validate_text

from .base import IntentRecognizerBase, IntentResult, UserIntent


logger = logging.getLogger(__name__)


class RuleIntentLevel(InferenceLevelBase):
    """规则意图识别层"""
    
    # 意图关键词映射
    INTENT_KEYWORDS = {
        UserIntent.SEARCH: [
            "搜索", "查找", "找", "检索", "有没有", "什么是",
            "search", "find", "query", "lookup"
        ],
        UserIntent.MEMORIZE: [
            "记住", "保存", "存储", "记录", "记下",
            "remember", "save", "store", "记忆"
        ],
        UserIntent.RECALL: [
            "回忆", "想起", "记得", "之前", "以前",
            "recall", "remember", "以前说过"
        ],
        UserIntent.ANALYZE: [
            "分析", "总结", "归纳", "统计", "报告",
            "analyze", "summary", "report", "统计"
        ],
    }
    
    async def infer(self, input_data: Any, context: Dict[str, Any]) -> InferenceResult:
        """规则意图识别"""
        text = input_data.lower()
        
        # 匹配关键词
        for intent, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return InferenceResult(
                        success=True,
                        confidence=0.7,
                        result={"intent": intent},
                        metadata={"method": "rule", "keyword": keyword}
                    )
        
        # 未匹配，返回低置信度
        return InferenceResult(
            success=False,
            confidence=0.0,
            result={"intent": UserIntent.UNKNOWN},
            metadata={"method": "rule"}
        )


class LLMIntentLevel(InferenceLevelBase):
    """LLM 意图识别层"""
    
    def __init__(self, llm_caller: LLMCallerBase):
        self.llm = llm_caller
    
    async def infer(self, input_data: Any, context: Dict[str, Any]) -> InferenceResult:
        """LLM 意图识别"""
        text = input_data
        
        # 构建提示词
        prompt = f"""分析用户意图，从以下类型中选择最合适的一个：
- search: 搜索、查找知识或信息
- chat: 闲聊、问候、日常对话
- memorize: 存储、记录信息或记忆
- recall: 回忆、回顾历史信息
- analyze: 分析、总结、统计
- unknown: 无法判断

用户输入：{text}

请以JSON格式回复：{{"intent": "类型", "confidence": 0-1之间的数字, "reason": "理由"}}"""
        
        try:
            response = await self.llm.call(
                prompt=prompt,
                temperature=0.1,
                max_tokens=100
            )
            
            # 解析响应
            import json
            result = json.loads(response.content)
            
            intent_str = result.get("intent", "unknown")
            confidence = float(result.get("confidence", 0.5))
            
            # 转换为枚举
            try:
                intent = UserIntent(intent_str)
            except ValueError:
                intent = UserIntent.UNKNOWN
            
            return InferenceResult(
                success=True,
                confidence=confidence,
                result={"intent": intent},
                metadata={"method": "llm", "reason": result.get("reason")}
            )
        
        except Exception as e:
            logger.error(f"LLM intent recognition failed: {e}")
            return InferenceResult(
                success=False,
                confidence=0.0,
                result={"intent": UserIntent.UNKNOWN},
                metadata={"method": "llm", "error": str(e)}
            )


class IntentRecognizer(IntentRecognizerBase):
    """
    意图识别器
    
    特性：
    - 规则 + LLM 级联识别
    - 实体提取
    - 槽位填充
    - 上下文感知
    """
    
    def __init__(
        self,
        llm_caller: LLMCallerBase,
        ner: Optional[NERBase] = None,
        use_cascade: bool = True,
        confidence_threshold: float = 0.7,
    ):
        """
        Args:
            llm_caller: LLM 调用器
            ner: 命名实体识别器（可选）
            use_cascade: 是否使用级联推理
            confidence_threshold: 置信度阈值
        """
        self.llm = llm_caller
        self.ner = ner
        self.use_cascade = use_cascade
        
        # 创建级联引擎
        if use_cascade:
            self.engine = CascadeInferenceEngine(
                confidence_threshold=confidence_threshold,
                enable_cache=True
            )
            self.engine.add_level(RuleIntentLevel())
            self.engine.add_level(LLMIntentLevel(llm_caller))
    
    async def recognize(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> IntentResult:
        """识别用户意图"""
        if not validate_text(text):
            return IntentResult(
                intent=UserIntent.UNKNOWN,
                confidence=0.0,
                entities={},
                slots={}
            )
        
        # 意图识别
        if self.use_cascade:
            result = await self.engine.infer(text, context or {})
            intent = result.result.get("intent", UserIntent.UNKNOWN)
            confidence = result.confidence
        else:
            # 直接使用 LLM
            level = LLMIntentLevel(self.llm)
            result = await level.infer(text, context or {})
            intent = result.result.get("intent", UserIntent.UNKNOWN)
            confidence = result.confidence
        
        # 实体提取
        entities = {}
        if self.ner:
            entity_list = await self.ner.extract(text)
            for entity in entity_list:
                entity_type = entity.entity_type.lower()
                if entity_type not in entities:
                    entities[entity_type] = []
                entities[entity_type].append(entity.text)
        
        # 槽位填充（基于意图）
        slots = self._extract_slots(text, intent, entities)
        
        return IntentResult(
            intent=intent,
            confidence=confidence,
            entities=entities,
            slots=slots,
            metadata=result.metadata
        )
    
    def _extract_slots(
        self,
        text: str,
        intent: UserIntent,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取槽位"""
        slots = {}
        
        if intent == UserIntent.SEARCH:
            # 搜索意图：提取搜索关键词
            slots["query"] = text
            if "topic" in entities:
                slots["topic"] = entities["topic"][0]
        
        elif intent == UserIntent.RECALL:
            # 回忆意图：提取时间范围
            time_patterns = {
                "today": r"今天|today",
                "yesterday": r"昨天|yesterday",
                "last_week": r"上周|上星期|last week",
                "last_month": r"上个月|上月|last month",
            }
            for time_key, pattern in time_patterns.items():
                if re.search(pattern, text, re.IGNORECASE):
                    slots["time_range"] = time_key
                    break
        
        elif intent == UserIntent.MEMORIZE:
            # 存储意图：提取要存储的内容
            slots["content"] = text
        
        elif intent == UserIntent.ANALYZE:
            # 分析意图：提取分析类型
            if "总结" in text or "summary" in text.lower():
                slots["analyze_type"] = "summary"
            elif "统计" in text or "statistics" in text.lower():
                slots["analyze_type"] = "statistics"
        
        return slots
