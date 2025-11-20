"""
意图识别器 - 基于规则+LLM的意图识别
"""

import re
from typing import Dict, List, Optional
from loguru import logger

from ..core import (
    IntentType,
    IntentResult,
    IntentRecognitionError,
)


class IntentRecognizer:
    """意图识别器（基于规则+LLM混合策略）
    
    Enhancements:
    - 支持自定义意图类型
    - 支持自定义规则模式
    - 支持动态注册意图
    - 支持配置文件加载
    """
    
    def __init__(
        self,
        llm_caller=None,
        custom_intents: Optional[List[str]] = None,
        intent_rules: Optional[Dict[str, List[str]]] = None,
        extend_default: bool = True
    ):
        """初始化
        
        Args:
            llm_caller: LLM调用器（可选，用于规则无法识别时的LLM增强）
            custom_intents: 自定义意图类型列表 (e.g., ["book_query", "music_recommendation"])
            intent_rules: 自定义意图规则 {intent_name: [pattern1, pattern2, ...]}
            extend_default: 是否扩展默认规则(否则完全替换)
        """
        self.llm = llm_caller
        self.custom_intents = custom_intents or []
        self.extend_default = extend_default
        
        # 初始化规则模式
        if extend_default:
            self._rule_patterns = self._init_rules()
            # 扩展自定义规则
            if intent_rules:
                self._extend_rules(intent_rules)
        else:
            # 完全使用自定义规则
            self._rule_patterns = self._convert_custom_rules(intent_rules or {})
    
    def _init_rules(self) -> Dict[IntentType, List[str]]:
        """初始化规则模式
        
        Returns:
            意图类型到正则模式的映射
        """
        return {
            IntentType.QUERY_SELF: [
                r"我.*?(喜欢|兴趣|爱好)",
                r"我.*?(是谁|什么样|性格)",
                r"介绍.*?我",
                r"我的.*?(特点|优点|缺点)",
                r"了解.*?我",
            ],
            IntentType.COMFORT: [
                r"(难过|伤心|失落|沮丧|焦虑|抑郁|痛苦)",
                r"(安慰|倾诉|聊聊)",
                r"心情.*?(不好|糟糕|低落)",
                r"(想哭|想死|没意思)",
            ],
            IntentType.ANALYZE: [
                r"分析.*?我",
                r"评价.*?我",
                r"怎么看.*?我",
                r"我.*?(表现|行为|状态)",
            ],
        }
    
    def _convert_custom_rules(self, intent_rules: Dict[str, List[str]]) -> Dict[IntentType, List[str]]:
        """转换自定义规则为IntentType映射
        
        Args:
            intent_rules: {intent_name: [pattern1, ...]}
            
        Returns:
            {IntentType: [pattern1, ...]}
        """
        converted = {}
        for intent_name, patterns in intent_rules.items():
            try:
                # 尝试映射到预定义的IntentType
                intent_type = IntentType(intent_name.lower())
                converted[intent_type] = patterns
            except ValueError:
                # 自定义意图，使用CUSTOM类型
                logger.info(f"自定义意图: {intent_name}, 映射为CUSTOM")
                if IntentType.CUSTOM not in converted:
                    converted[IntentType.CUSTOM] = []
                # 为自定义意图添加标记
                converted[IntentType.CUSTOM].extend(
                    [f"__CUSTOM:{intent_name}__" + p for p in patterns]
                )
        return converted
    
    def _extend_rules(self, custom_rules: Dict[str, List[str]]) -> None:
        """扩展默认规则
        
        Args:
            custom_rules: {intent_name: [pattern1, ...]}
        """
        for intent_name, patterns in custom_rules.items():
            try:
                intent_type = IntentType(intent_name.lower())
                if intent_type not in self._rule_patterns:
                    self._rule_patterns[intent_type] = []
                self._rule_patterns[intent_type].extend(patterns)
                logger.info(f"扩展意图 '{intent_name}' 的规则: {len(patterns)} 个模式")
            except ValueError:
                # 自定义意图
                if IntentType.CUSTOM not in self._rule_patterns:
                    self._rule_patterns[IntentType.CUSTOM] = []
                self._rule_patterns[IntentType.CUSTOM].extend(
                    [f"__CUSTOM:{intent_name}__" + p for p in patterns]
                )
                logger.info(f"添加自定义意图 '{intent_name}': {len(patterns)} 个模式")
    
    def register_intent(
        self,
        intent_name: str,
        patterns: List[str],
        replace: bool = False
    ) -> None:
        """动态注册意图
        
        Args:
            intent_name: 意图名称 (e.g., "book_query")
            patterns: 正则模式列表
            replace: 是否替换现有规则(否则扩展)
        """
        try:
            intent_type = IntentType(intent_name.lower())
            if replace or intent_type not in self._rule_patterns:
                self._rule_patterns[intent_type] = patterns
            else:
                self._rule_patterns[intent_type].extend(patterns)
            logger.info(f"注册意图 '{intent_name}': {len(patterns)} 个模式")
        except ValueError:
            # 自定义意图
            if IntentType.CUSTOM not in self._rule_patterns:
                self._rule_patterns[IntentType.CUSTOM] = []
            tagged_patterns = [f"__CUSTOM:{intent_name}__" + p for p in patterns]
            if replace:
                # 移除旧的同名意图
                self._rule_patterns[IntentType.CUSTOM] = [
                    p for p in self._rule_patterns[IntentType.CUSTOM]
                    if not p.startswith(f"__CUSTOM:{intent_name}__")
                ]
            self._rule_patterns[IntentType.CUSTOM].extend(tagged_patterns)
            logger.info(f"注册自定义意图 '{intent_name}': {len(patterns)} 个模式")
    
    def get_registered_intents(self) -> List[str]:
        """获取所有已注册的意图类型
        
        Returns:
            意图类型列表
        """
        intents = [intent.value for intent in self._rule_patterns.keys()]
        
        # 提取自定义意图
        if IntentType.CUSTOM in self._rule_patterns:
            custom_intents = set()
            for pattern in self._rule_patterns[IntentType.CUSTOM]:
                if pattern.startswith("__CUSTOM:"):
                    intent_name = pattern.split("__")[2].split(":")[0]
                    custom_intents.add(intent_name)
            intents.extend(list(custom_intents))
        
        return intents
    
    def _match_rules(self, text: str) -> tuple:
        """规则匹配
        
        Args:
            text: 输入文本
            
        Returns:
            (匹配到的意图类型, 自定义意图名称)
        """
        for intent, patterns in self._rule_patterns.items():
            for pattern in patterns:
                # 处理自定义意图
                custom_name = None
                actual_pattern = pattern
                if pattern.startswith("__CUSTOM:"):
                    # 格式: __CUSTOM:intent_name__pattern
                    parts = pattern.split("__", 2)  # 最多分为3部分
                    if len(parts) >= 3:
                        custom_info = parts[1]  # CUSTOM:intent_name
                        actual_pattern = parts[2]  # 实际pattern
                        if ":" in custom_info:
                            custom_name = custom_info.split(":", 1)[1]
                
                if re.search(actual_pattern, text, re.IGNORECASE):
                    logger.debug(f"规则匹配到意图: {intent.value}, 模式: {actual_pattern}")
                    return intent, custom_name
        
        return IntentType.UNKNOWN, None
    
    async def _llm_recognize(self, text: str) -> IntentResult:
        """LLM识别意图
        
        Args:
            text: 输入文本
            
        Returns:
            意图识别结果
        """
        if not self.llm:
            logger.warning("未配置LLM调用器，无法使用LLM增强识别")
            return IntentResult(
                intent=IntentType.CHAT,
                confidence=0.5,
                keywords=[],
                metadata={"method": "default", "reason": "no_llm"}
            )
        
        try:
            # 构建提示词
            prompt = f"""请识别以下文本的意图类型，从以下选项中选择：
- chat: 普通聊天
- query_self: 查询自己的信息（兴趣、记忆、性格等）
- analyze: 请求分析（情绪、行为、状态等）
- comfort: 需要安慰、倾诉

文本: {text}

请直接返回意图类型（只返回一个单词，如 chat 或 query_self），不要有其他内容。"""
            
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(messages, max_tokens=10, temperature=0)
            
            # 解析响应
            intent_str = response.content.strip().lower()
            
            # 映射到IntentType
            intent_map = {
                "chat": IntentType.CHAT,
                "query_self": IntentType.QUERY_SELF,
                "analyze": IntentType.ANALYZE,
                "comfort": IntentType.COMFORT,
            }
            
            intent = intent_map.get(intent_str, IntentType.CHAT)
            
            return IntentResult(
                intent=intent,
                confidence=0.85,
                keywords=[],
                metadata={"method": "llm", "raw_response": intent_str}
            )
            
        except Exception as e:
            logger.error(f"LLM意图识别失败: {e}")
            return IntentResult(
                intent=IntentType.CHAT,
                confidence=0.5,
                keywords=[],
                metadata={"method": "default", "error": str(e)}
            )
    
    async def recognize(self, text: str, use_llm: bool = True) -> IntentResult:
        """识别意图
        
        先用规则匹配，规则不匹配且use_llm=True时再用LLM增强
        
        Args:
            text: 输入文本
            use_llm: 是否启用LLM增强（规则匹配失败时）
            
        Returns:
            意图识别结果
        """
        if not text or not text.strip():
            raise IntentRecognitionError("输入文本不能为空")
        
        # 1. 规则匹配
        intent, custom_name = self._match_rules(text)
        if intent != IntentType.UNKNOWN:
            metadata = {"method": "rule"}
            if custom_name:
                metadata["custom_intent"] = custom_name
            
            return IntentResult(
                intent=intent,
                confidence=0.80,
                keywords=self._extract_keywords(text, intent),
                metadata=metadata
            )
        
        # 2. LLM识别（可选）
        if use_llm and self.llm:
            return await self._llm_recognize(text)
        
        # 3. 默认为聊天
        return IntentResult(
            intent=IntentType.CHAT,
            confidence=0.6,
            keywords=[],
            metadata={"method": "default"}
        )
    
    def _extract_keywords(self, text: str, intent: IntentType) -> List[str]:
        """提取关键词（简单实现）
        
        Args:
            text: 文本
            intent: 意图类型
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 根据意图类型提取特定关键词
        keyword_patterns = {
            IntentType.QUERY_SELF: [r"喜欢", r"兴趣", r"爱好", r"性格"],
            IntentType.COMFORT: [r"难过", r"伤心", r"焦虑", r"安慰"],
            IntentType.ANALYZE: [r"分析", r"评价", r"怎么看"],
        }
        
        patterns = keyword_patterns.get(intent, [])
        for pattern in patterns:
            if re.search(pattern, text):
                keywords.append(pattern.strip(r"\\"))
        
        return keywords
    
    def recognize_sync(self, text: str) -> IntentResult:
        """同步识别（仅使用规则）
        
        Args:
            text: 输入文本
            
        Returns:
            意图识别结果
        """
        if not text or not text.strip():
            raise IntentRecognitionError("输入文本不能为空")
        
        intent, _ = self._match_rules(text)
        if intent == IntentType.UNKNOWN:
            intent = IntentType.CHAT
        
        return IntentResult(
            intent=intent,
            confidence=0.75 if intent != IntentType.CHAT else 0.6,
            keywords=self._extract_keywords(text, intent),
            metadata={"method": "rule_sync"}
        )
