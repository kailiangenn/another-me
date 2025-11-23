"""LLM Core - 核心实现

提供LLM调用器的抽象基类和具体实现。
BaseLLMCaller已内置所有组件能力，对外只暴露chat、chat_stream、agent三个方法。

使用方式:
    # 创建调用器
    caller = OpenAICaller(api_key="sk-xxx")
    
    # 对话模式 - 自动管理历史
    response = await caller.chat("你好")
    
    # 流式对话
    async for chunk in caller.chat_stream("讲个故事"):
        print(chunk, end='')
    
    # Agent模式 - NER/分词等任务
    response = await caller.agent(prompt="提取人名", task_type="ner")
"""

from .base import BaseLLMCaller
from .openai_caller import OpenAICaller

__all__ = [
    "BaseLLMCaller",  # 基础调用器（内置组件能力）
    "OpenAICaller",   # OpenAI调用器
]
