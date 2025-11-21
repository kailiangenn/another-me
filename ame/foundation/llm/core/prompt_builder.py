"""
提示词构建器

提供模板化提示词构建、历史嵌入和Few-shot示例支持。
"""

from typing import List, Dict, Optional, Any
from string import Template
import logging

logger = logging.getLogger(__name__)


class PromptBuilder:
    """
    提示词构建器
    
    Features:
    - 模板变量替换
    - 对话历史嵌入
    - Few-shot示例构建
    - 系统提示词管理
    """
    
    def __init__(self, default_system_prompt: Optional[str] = None):
        """
        初始化提示词构建器
        
        Args:
            default_system_prompt: 默认系统提示词
        """
        self.default_system_prompt = default_system_prompt
        logger.debug("PromptBuilder initialized")
    
    def build(
        self,
        template: str,
        variables: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建基础提示词
        
        使用模板和变量构建提示词。支持两种变量替换方式:
        1. 使用 ${var_name} 格式的模板替换
        2. 使用 context 参数传递上下文信息
        
        Args:
            template: 提示词模板,支持${变量名}格式
            variables: 要替换的变量字典
            context: 额外的上下文信息
        
        Returns:
            构建好的提示词
        
        Example:
            >>> builder = PromptBuilder()
            >>> template = "请分析以下内容: ${content}"
            >>> prompt = builder.build(template, {"content": "今天天气很好"})
            >>> print(prompt)
            请分析以下内容: 今天天气很好
        """
        if variables is None:
            variables = {}
        if context is None:
            context = {}
        
        # 合并变量和上下文
        all_vars = {**context, **variables}
        
        try:
            # 使用Template进行安全的变量替换
            t = Template(template)
            result = t.safe_substitute(all_vars)
            
            logger.debug(f"Built prompt with {len(all_vars)} variables")
            return result
        
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            # 失败时返回原模板
            return template
    
    def build_with_history(
        self,
        template: str,
        history: List[Dict[str, str]],
        max_history_messages: int = 10,
        variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建带历史对话的提示词
        
        将对话历史格式化后嵌入到提示词模板中。
        历史格式: "User: xxx\\nAssistant: xxx\\n"
        
        Args:
            template: 提示词模板,应包含${history}占位符
            history: 对话历史列表,每项包含role和content
            max_history_messages: 最多包含的历史消息数
            variables: 其他要替换的变量
        
        Returns:
            包含历史的提示词
        
        Example:
            >>> history = [
            ...     {"role": "user", "content": "你好"},
            ...     {"role": "assistant", "content": "你好!有什么可以帮您?"}
            ... ]
            >>> template = "对话历史:\\n${history}\\n\\n请继续对话。"
            >>> prompt = builder.build_with_history(template, history)
        """
        if variables is None:
            variables = {}
        
        # 格式化历史
        formatted_history = self._format_history(history, max_history_messages)
        
        # 添加历史到变量中
        variables_with_history = {
            **variables,
            "history": formatted_history
        }
        
        return self.build(template, variables_with_history)
    
    def build_few_shot(
        self,
        task_description: str,
        examples: List[Dict[str, str]],
        query: str,
        instruction: Optional[str] = None
    ) -> str:
        """
        构建Few-shot提示词
        
        格式:
        [任务描述]
        
        示例1:
        输入: xxx
        输出: xxx
        
        示例2:
        输入: xxx
        输出: xxx
        
        现在请处理:
        输入: [query]
        输出:
        
        Args:
            task_description: 任务描述
            examples: 示例列表,每项包含input和output
            query: 要处理的查询
            instruction: 额外的指令(可选)
        
        Returns:
            Few-shot提示词
        
        Example:
            >>> examples = [
            ...     {"input": "今天天气很好", "output": "正面"},
            ...     {"input": "我很难过", "output": "负面"}
            ... ]
            >>> prompt = builder.build_few_shot(
            ...     "情感分类任务",
            ...     examples,
            ...     "我很开心"
            ... )
        """
        parts = []
        
        # 任务描述
        parts.append(task_description)
        parts.append("")
        
        # 额外指令
        if instruction:
            parts.append(instruction)
            parts.append("")
        
        # 添加示例
        for i, example in enumerate(examples, 1):
            parts.append(f"示例{i}:")
            parts.append(f"输入: {example.get('input', '')}")
            parts.append(f"输出: {example.get('output', '')}")
            parts.append("")
        
        # 添加查询
        parts.append("现在请处理:")
        parts.append(f"输入: {query}")
        parts.append("输出:")
        
        result = "\n".join(parts)
        logger.debug(f"Built few-shot prompt with {len(examples)} examples")
        return result
    
    def build_with_system(
        self,
        user_prompt: str,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        构建包含系统提示词的消息列表
        
        返回适合OpenAI API的消息格式:
        [
            {"role": "system", "content": "..."},
            {"role": "user", "content": "..."}
        ]
        
        Args:
            user_prompt: 用户提示词
            system_prompt: 系统提示词,为None时使用默认值
        
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统提示词
        sys_prompt = system_prompt or self.default_system_prompt
        if sys_prompt:
            messages.append({
                "role": "system",
                "content": sys_prompt
            })
        
        # 添加用户提示词
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        return messages
    
    def build_messages_with_history(
        self,
        user_message: str,
        history: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_history_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        构建完整的消息列表(系统提示词+历史+新消息)
        
        Args:
            user_message: 新的用户消息
            history: 对话历史
            system_prompt: 系统提示词
            max_history_messages: 最多包含的历史消息数
        
        Returns:
            完整的消息列表
        """
        messages = []
        
        # 1. 系统提示词
        sys_prompt = system_prompt or self.default_system_prompt
        if sys_prompt:
            messages.append({
                "role": "system",
                "content": sys_prompt
            })
        
        # 2. 历史消息(截断到最近N条)
        recent_history = history[-max_history_messages:] if history else []
        messages.extend(recent_history)
        
        # 3. 新消息
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        logger.debug(
            f"Built message list: system={1 if sys_prompt else 0}, "
            f"history={len(recent_history)}, new=1"
        )
        
        return messages
    
    def _format_history(
        self,
        history: List[Dict[str, str]],
        max_messages: int = 10
    ) -> str:
        """
        格式化对话历史
        
        Args:
            history: 对话历史
            max_messages: 最多包含的消息数
        
        Returns:
            格式化后的历史字符串
        """
        if not history:
            return "(无历史对话)"
        
        # 截取最近的消息
        recent_history = history[-max_messages:]
        
        # 格式化每条消息
        formatted = []
        for msg in recent_history:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            # 角色名称映射
            role_name = {
                "user": "User",
                "assistant": "Assistant",
                "system": "System"
            }.get(role, role.capitalize())
            
            formatted.append(f"{role_name}: {content}")
        
        return "\n".join(formatted)
    
    def set_default_system_prompt(self, prompt: str):
        """
        设置默认系统提示词
        
        Args:
            prompt: 系统提示词
        """
        self.default_system_prompt = prompt
        logger.info("Updated default system prompt")


# ============================================================================
# 预定义模板
# ============================================================================

class PromptTemplates:
    """常用提示词模板"""
    
    # 情感分析
    EMOTION_ANALYSIS = """请分析以下文本的情感倾向和情绪类型。

文本: ${text}

请返回:
1. 情绪类型(喜悦/悲伤/愤怒/恐惧/惊讶/厌恶)
2. 情绪强度(0-1)
3. 情感倾向(正面/负面/中性)
4. 关键词"""
    
    # 实体提取
    ENTITY_EXTRACTION = """请从以下文本中提取所有实体。

文本: ${text}

请提取以下类型的实体:
- 人名
- 地名
- 组织机构
- 时间
- 事件

以JSON格式返回。"""
    
    # 文本摘要
    SUMMARIZATION = """请对以下文本进行摘要,保留核心信息。

文本: ${text}

摘要要求:
- 长度不超过${max_length}字
- 保留关键信息
- 语言简洁清晰"""
    
    # 对话生成
    DIALOGUE_GENERATION = """你是一个智能对话助手。请根据上下文生成合适的回复。

对话历史:
${history}

用户: ${user_message}

请生成自然、有帮助的回复。"""
    
    # 意图识别
    INTENT_RECOGNITION = """请识别以下消息的意图类型。

消息: ${message}

可能的意图类型:
- 查询信息
- 寻求帮助
- 闲聊对话
- 执行任务
- 表达情感

请返回最可能的意图类型和置信度。"""
