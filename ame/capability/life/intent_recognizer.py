"""
Life场景意图识别器

对Foundation层IntentRecognizer的封装,针对生活场景优化。
"""

from typing import List, Optional
from loguru import logger

from ame.foundation.nlp import IntentRecognizer as BaseIntentRecognizer
from ame.foundation.nlp import IntentType, IntentResult


class LifeIntentRecognizer:
    """Life场景意图识别器
    
    针对生活场景对话的意图识别,扩展了更多生活相关的意图规则。
    """
    
    def __init__(self, llm_caller=None):
        """初始化
        
        Args:
            llm_caller: LLM调用器(可选)
        """
        # 定义Life场景特有的意图规则
        life_intent_rules = {
            "query_self": [
                r"我.*?(喜欢|兴趣|爱好)",
                r"我.*?(是谁|什么样|性格)",
                r"介绍.*?我",
                r"我的.*?(特点|优点|缺点|经历|故事)",
                r"了解.*?我",
                r"关于.*?我",
                r"我.*?(做过|经历过)",
            ],
            "comfort": [
                r"(难过|伤心|失落|沮丧|焦虑|抑郁|痛苦|难受)",
                r"(安慰|倾诉|聊聊)",
                r"心情.*?(不好|糟糕|低落|很差)",
                r"(想哭|想死|没意思|没意义)",
                r"(孤独|寂寞|无助|绝望)",
                r"(压力|烦恼|困扰).*?(很大|太大|好多)",
            ],
            "analyze": [
                r"分析.*?我",
                r"评价.*?我",
                r"怎么看.*?我",
                r"我.*?(表现|行为|状态|怎么样)",
                r"给.*?建议",
                r"帮我.*?(看看|分析)",
            ],
            "chat": [
                r"^(嗨|你好|hi|hello)",
                r"(聊天|闲聊|说说话)",
                r"(今天|最近).*?(怎么样|如何)",
            ],
            "share_emotion": [
                r"我.*?(开心|高兴|快乐|兴奋)",
                r"我.*?(生气|愤怒|火大)",
                r"我.*?(害怕|恐惧|担心)",
                r"(分享|告诉你).*?(心情|感受|情绪)",
            ],
            "recall_memory": [
                r"(记得|还记得|回忆).*?(吗|我们)",
                r"(上次|之前|以前).*?(说过|提过|聊过)",
                r"那时候.*?(我们|你|我)",
            ],
        }
        
        # 使用扩展规则初始化基础识别器
        self.base_recognizer = BaseIntentRecognizer(
            llm_caller=llm_caller,
            intent_rules=life_intent_rules,
            extend_default=True  # 扩展默认规则
        )
        
        logger.debug("LifeIntentRecognizer初始化完成")
    
    async def recognize(
        self,
        text: str,
        use_llm: bool = True,
        context: Optional[List[str]] = None
    ) -> IntentResult:
        """识别意图
        
        Args:
            text: 输入文本
            use_llm: 是否使用LLM增强
            context: 上下文信息(可选,用于更准确的意图识别)
            
        Returns:
            意图识别结果
        """
        # 如果提供了上下文,可以基于上下文调整识别策略
        if context:
            logger.debug(f"基于 {len(context)} 条上下文进行意图识别")
            # TODO: 可以基于上下文优化识别逻辑
        
        # 调用基础识别器
        result = await self.base_recognizer.recognize(text, use_llm=use_llm)
        
        # 对结果进行Life场景特定的后处理
        result = self._post_process_result(result, text)
        
        return result
    
    def _post_process_result(
        self,
        result: IntentResult,
        text: str
    ) -> IntentResult:
        """后处理识别结果
        
        针对Life场景进行特殊处理和置信度调整。
        
        Args:
            result: 原始识别结果
            text: 输入文本
            
        Returns:
            处理后的结果
        """
        # 如果识别为CUSTOM,检查是否是Life特有意图
        if result.intent == IntentType.CUSTOM:
            custom_intent = result.metadata.get("custom_intent", "")
            
            # 映射Life特有意图到标准意图
            if custom_intent == "share_emotion":
                # 情绪分享可以归类为CHAT或COMFORT
                if any(word in text for word in ["开心", "高兴", "快乐"]):
                    result.intent = IntentType.CHAT
                else:
                    result.intent = IntentType.COMFORT
                result.confidence = min(result.confidence + 0.05, 0.95)
                result.metadata["original_custom_intent"] = custom_intent
            
            elif custom_intent == "recall_memory":
                # 回忆记忆归类为QUERY_SELF
                result.intent = IntentType.QUERY_SELF
                result.confidence = min(result.confidence + 0.05, 0.95)
                result.metadata["original_custom_intent"] = custom_intent
        
        # 如果是COMFORT意图,提高置信度(Life场景中很重要)
        if result.intent == IntentType.COMFORT:
            result.confidence = min(result.confidence + 0.1, 0.95)
            result.metadata["life_boost"] = True
        
        return result
    
    def recognize_sync(self, text: str) -> IntentResult:
        """同步识别(仅使用规则)
        
        Args:
            text: 输入文本
            
        Returns:
            意图识别结果
        """
        result = self.base_recognizer.recognize_sync(text)
        return self._post_process_result(result, text)
    
    def get_supported_intents(self) -> List[str]:
        """获取支持的意图类型列表
        
        Returns:
            意图类型列表
        """
        return self.base_recognizer.get_registered_intents()
    
    def register_custom_intent(
        self,
        intent_name: str,
        patterns: List[str],
        replace: bool = False
    ) -> None:
        """注册自定义意图
        
        Args:
            intent_name: 意图名称
            patterns: 正则模式列表
            replace: 是否替换现有规则
        """
        self.base_recognizer.register_intent(intent_name, patterns, replace)
        logger.info(f"Life场景注册自定义意图: {intent_name}")
