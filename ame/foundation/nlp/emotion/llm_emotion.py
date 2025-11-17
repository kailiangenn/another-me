"""
LLM 情绪识别器

使用 LLM 进行深度情绪分析

特性：
- 精确识别复杂情绪
- 支持上下文理解
- 细粒度情绪分类
- JSON 结构化输出

从 mem/analyze_engine.py 提取并优化
"""

import logging
import json
from typing import Dict, Any, Optional

from ame.foundation.llm import LLMCallerBase
from .base import EmotionDetectorBase, EmotionResult, EmotionType

logger = logging.getLogger(__name__)


class LLMEmotionDetector(EmotionDetectorBase):
    """
    LLM 情绪识别器
    
    使用大语言模型进行深度情绪分析
    """
    
    def __init__(self, llm_caller: LLMCallerBase):
        """
        初始化 LLM 情绪识别器
        
        Args:
            llm_caller: LLM 调用器
        """
        self.llm = llm_caller
        logger.info("LLM 情绪识别器初始化")
    
    async def detect(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EmotionResult:
        """
        使用 LLM 识别情绪
        
        Args:
            text: 输入文本
            context: 上下文信息（可选）
                - history: 历史对话
                - user_profile: 用户画像
        
        Returns:
            result: 情绪识别结果
        """
        if not text:
            return EmotionResult(
                type=EmotionType.NEUTRAL.value,
                intensity=0.5,
                confidence=0.5,
                metadata={"method": "llm", "reason": "empty_text"}
            )
        
        try:
            # 构建 Prompt
            prompt = self._build_prompt(text, context)
            
            # 调用 LLM
            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            # 解析结果
            result = self._parse_response(response.content, text)
            
            logger.debug(
                f"LLM 情绪识别: {result.type} "
                f"(intensity={result.intensity:.2f}, confidence={result.confidence:.2f})"
            )
            
            return result
        
        except Exception as e:
            logger.error(f"LLM 情绪识别失败: {e}", exc_info=True)
            
            # 失败时返回中性情绪，低置信度
            return EmotionResult(
                type=EmotionType.NEUTRAL.value,
                intensity=0.5,
                confidence=0.3,
                metadata={
                    "method": "llm",
                    "error": str(e),
                    "fallback": True
                }
            )
    
    def _build_prompt(self, text: str, context: Optional[Dict[str, Any]]) -> str:
        """
        构建 LLM Prompt
        
        Args:
            text: 输入文本
            context: 上下文信息
        
        Returns:
            prompt: 完整的 Prompt
        """
        prompt = f"""请分析以下文本的情绪，并以 JSON 格式返回结果。

**文本**:
{text}
"""
        
        # 添加上下文信息
        if context:
            if "history" in context and context["history"]:
                prompt += f"\n**历史对话**:\n{context['history'][:200]}...\n"
            
            if "user_profile" in context:
                prompt += f"\n**用户特征**: {context['user_profile']}\n"
        
        prompt += """
**任务**:
分析文本的情绪，返回以下 JSON 格式：

```json
{
  "type": "情绪类型（positive/negative/neutral/happy/sad/angry/anxious/frustrated/excited/calm）",
  "intensity": 0.0-1.0,  // 情绪强度
  "reason": "识别理由（简短说明）"
}
```

**要求**:
1. `type`: 从以下选项中选择最准确的：positive, negative, neutral, happy, sad, angry, anxious, frustrated, excited, calm
2. `intensity`: 0.0（无情绪）到 1.0（强烈情绪）
3. `reason`: 简短说明为什么判断为该情绪，引用关键词或表达

只返回 JSON，不要其他内容。
"""
        
        return prompt
    
    def _parse_response(self, response: str, original_text: str) -> EmotionResult:
        """
        解析 LLM 响应
        
        Args:
            response: LLM 返回的文本
            original_text: 原始输入文本
        
        Returns:
            result: 情绪识别结果
        """
        try:
            # 提取 JSON（可能包含 markdown 代码块）
            json_str = response.strip()
            
            # 移除 markdown 代码块标记
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            json_str = json_str.strip()
            
            # 解析 JSON
            data = json.loads(json_str)
            
            # 提取字段
            emotion_type = data.get("type", EmotionType.NEUTRAL.value)
            intensity = float(data.get("intensity", 0.5))
            reason = data.get("reason", "")
            
            # 验证和修正
            intensity = max(0.0, min(1.0, intensity))
            
            # LLM 识别通常置信度较高
            confidence = 0.9 if intensity > 0.3 else 0.7
            
            return EmotionResult(
                type=emotion_type,
                intensity=intensity,
                confidence=confidence,
                metadata={
                    "method": "llm",
                    "reason": reason,
                    "raw_response": response[:200]
                }
            )
        
        except json.JSONDecodeError as e:
            logger.warning(f"解析 LLM 响应 JSON 失败: {e}, response={response[:100]}")
            
            # JSON 解析失败，尝试从文本中提取信息
            return self._fallback_parse(response, original_text)
        
        except Exception as e:
            logger.error(f"解析 LLM 响应失败: {e}")
            
            return EmotionResult(
                type=EmotionType.NEUTRAL.value,
                intensity=0.5,
                confidence=0.5,
                metadata={
                    "method": "llm",
                    "error": str(e),
                    "parse_fallback": True
                }
            )
    
    def _fallback_parse(self, response: str, original_text: str) -> EmotionResult:
        """
        备用解析方法（当 JSON 解析失败时）
        
        尝试从自然语言中提取情绪信息
        """
        response_lower = response.lower()
        
        # 简单的关键词匹配
        if "positive" in response_lower or "happy" in response_lower or "joy" in response_lower:
            emotion_type = EmotionType.POSITIVE.value
            intensity = 0.7
        elif "negative" in response_lower or "sad" in response_lower or "angry" in response_lower:
            emotion_type = EmotionType.NEGATIVE.value
            intensity = 0.7
        else:
            emotion_type = EmotionType.NEUTRAL.value
            intensity = 0.5
        
        return EmotionResult(
            type=emotion_type,
            intensity=intensity,
            confidence=0.6,
            metadata={
                "method": "llm",
                "fallback_parse": True,
                "raw_response": response[:200]
            }
        )
    
    def get_detector_name(self) -> str:
        """获取识别器名称"""
        return "LLMEmotionDetector"
