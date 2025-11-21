"""
待办解析器 - 从自然语言文本中解析待办事项

配合TodoManager使用,提供纯解析功能(不涉及持久化)。
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re
from loguru import logger

from ame.foundation.algorithm import TodoItem, Priority, TaskStatus
from ame.foundation.llm import LLMCallerBase


class TodoParser:
    """待办解析器
    
    从自然语言文本解析待办事项,支持规则解析和LLM增强。
    """
    
    def __init__(self, llm_caller: Optional[LLMCallerBase] = None):
        """初始化
        
        Args:
            llm_caller: LLM调用器(可选)
        """
        self.llm = llm_caller
        logger.debug("TodoParser初始化完成")
    
    async def parse(
        self,
        text: str,
        use_llm: bool = True,
        existing_task_ids: Optional[List[str]] = None
    ) -> List[TodoItem]:
        """解析文本中的待办事项
        
        Args:
            text: 输入文本
            use_llm: 是否使用LLM增强
            existing_task_ids: 已存在的任务ID列表(用于检查依赖)
            
        Returns:
            待办事项列表
        """
        if not text or not text.strip():
            logger.warning("输入文本为空")
            return []
        
        # 1. 先尝试规则解析
        rule_based_todos = self._parse_by_rules(text)
        
        # 2. 如果规则解析成功且充分,直接返回
        if rule_based_todos and len(rule_based_todos) >= 3:
            logger.info(f"规则解析成功: {len(rule_based_todos)} 个待办")
            return rule_based_todos
        
        # 3. 否则使用LLM增强
        if use_llm and self.llm:
            llm_todos = await self._parse_by_llm(text, existing_task_ids)
            if llm_todos:
                logger.info(f"LLM解析成功: {len(llm_todos)} 个待办")
                return llm_todos
        
        # 4. 降级到规则解析结果(即使只有少量)
        return rule_based_todos
    
    def _parse_by_rules(self, text: str) -> List[TodoItem]:
        """基于规则解析待办
        
        支持以下格式:
        - [ ] 任务标题
        - TODO: 任务标题
        - 1. 任务标题
        - - 任务标题
        
        Args:
            text: 输入文本
            
        Returns:
            待办列表
        """
        todos = []
        lines = text.split('\n')
        
        # 正则模式
        patterns = [
            r'^-?\s*\[\s*\]\s+(.+)$',           # - [ ] 任务
            r'^-?\s*TODO:?\s+(.+)$',            # TODO: 任务
            r'^(\d+)\.\s+(.+)$',                 # 1. 任务
            r'^-\s+(.+)$',                       # - 任务
        ]
        
        task_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            matched = False
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    # 提取任务标题
                    title = match.group(2) if match.lastindex >= 2 else match.group(1)
                    title = title.strip()
                    
                    if not title:
                        continue
                    
                    # 解析优先级
                    priority = self._extract_priority(title)
                    
                    # 解析截止日期
                    due_date = self._extract_due_date(title)
                    
                    # 生成任务ID
                    task_id = f"task_{datetime.now().strftime('%Y%m%d')}_{task_counter}"
                    task_counter += 1
                    
                    todo = TodoItem(
                        id=task_id,
                        title=title,
                        description="",
                        priority=priority,
                        due_date=due_date,
                        status=TaskStatus.PENDING,
                        dependencies=[],
                        created_at=datetime.now()
                    )
                    
                    todos.append(todo)
                    matched = True
                    break
        
        return todos
    
    async def _parse_by_llm(
        self,
        text: str,
        existing_task_ids: Optional[List[str]] = None
    ) -> List[TodoItem]:
        """使用LLM解析待办
        
        Args:
            text: 输入文本
            existing_task_ids: 已存在的任务ID
            
        Returns:
            待办列表
        """
        if not self.llm:
            return []
        
        import json
        
        # 构建提示词
        existing_ids_str = ", ".join(existing_task_ids) if existing_task_ids else "无"
        
        prompt = f"""请从以下文本中提取待办事项,以JSON格式返回。

**文本内容:**
{text}

**已存在的任务ID(用于依赖关系):**
{existing_ids_str}

请返回JSON数组,每个待办包含:
- id: 任务ID(使用描述性的snake_case)
- title: 任务标题
- description: 详细描述(可选)
- priority: 优先级(high/medium/low)
- due_date: 截止日期(ISO格式,可选)
- dependencies: 依赖的任务ID数组(可选)

示例:
```json
[
  {{
    "id": "implement_login",
    "title": "实现登录功能",
    "description": "包含用户名密码验证",
    "priority": "high",
    "due_date": "2024-12-31T23:59:59",
    "dependencies": []
  }}
]
```

只返回JSON数组,不要其他内容。如果没有待办事项,返回空数组[]。
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(
                messages,
                max_tokens=1000,
                temperature=0.2
            )
            
            # 解析JSON
            raw_content = response.content.strip()
            
            # 清理markdown代码块
            if "```json" in raw_content:
                raw_content = raw_content.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_content:
                raw_content = raw_content.split("```")[1].split("```")[0].strip()
            
            todos_data = json.loads(raw_content)
            
            # 转换为TodoItem
            todos = []
            for item in todos_data:
                try:
                    todo = TodoItem(
                        id=item["id"],
                        title=item["title"],
                        description=item.get("description", ""),
                        priority=Priority(item.get("priority", "medium")),
                        due_date=datetime.fromisoformat(item["due_date"]) if item.get("due_date") else None,
                        dependencies=item.get("dependencies", []),
                        status=TaskStatus.PENDING,
                        created_at=datetime.now()
                    )
                    todos.append(todo)
                except Exception as e:
                    logger.error(f"解析待办项失败: {e}, 数据: {item}")
                    continue
            
            return todos
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM返回的JSON格式错误: {e}")
            return []
        except Exception as e:
            logger.error(f"LLM解析失败: {e}")
            return []
    
    def _extract_priority(self, text: str) -> Priority:
        """从文本提取优先级
        
        Args:
            text: 文本
            
        Returns:
            优先级
        """
        text_lower = text.lower()
        
        # 低优先级关键词(优先检查,避免被"重要"等词误判)
        if any(word in text_lower for word in ["低优", "不急", "低", "low", "later"]):
            return Priority.LOW
        
        # 高优先级关键词
        if any(word in text_lower for word in ["紧急", "重要", "优先", "urgent", "high", "!!!", "!!!"]):
            return Priority.HIGH
        
        # 默认中等优先级
        return Priority.MEDIUM
    
    def _extract_due_date(self, text: str) -> Optional[datetime]:
        """从文本提取截止日期
        
        Args:
            text: 文本
            
        Returns:
            截止日期
        """
        # 简单实现:识别常见的相对时间表达
        text_lower = text.lower()
        
        now = datetime.now()
        
        # 今天
        if any(word in text_lower for word in ["今天", "today"]):
            return now.replace(hour=23, minute=59, second=59)
        
        # 明天
        if any(word in text_lower for word in ["明天", "tomorrow"]):
            return (now + timedelta(days=1)).replace(hour=23, minute=59, second=59)
        
        # 本周
        if any(word in text_lower for word in ["本周", "this week"]):
            days_until_sunday = 6 - now.weekday()
            return (now + timedelta(days=days_until_sunday)).replace(hour=23, minute=59, second=59)
        
        # 下周
        if any(word in text_lower for word in ["下周", "next week"]):
            days_until_next_sunday = 6 - now.weekday() + 7
            return (now + timedelta(days=days_until_next_sunday)).replace(hour=23, minute=59, second=59)
        
        # 尝试匹配日期格式 YYYY-MM-DD
        date_pattern = r'(\d{4})-(\d{2})-(\d{2})'
        match = re.search(date_pattern, text)
        if match:
            try:
                year, month, day = match.groups()
                return datetime(int(year), int(month), int(day), 23, 59, 59)
            except ValueError:
                pass
        
        # 无法识别,返回None
        return None
