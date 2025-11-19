"""
待办管理器 - 根据用户输入生成待办、管理依赖关系、持久化到WorkGraph
"""

from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger
import json

from ame.foundation.llm import LLMCallerBase
from ame.foundation.storage import (
    GraphStoreBase,
    GraphNode,
    GraphEdge,
    NodeLabel,
    RelationType
)
from ame.foundation.algorithm import (
    TodoSorter,
    TodoItem,
    SortedTodoList,
    Priority,
    TaskStatus
)


class TodoManager:
    """待办管理器
    
    生成、排序、更新待办，并同步到WorkGraph。
    """
    
    def __init__(
        self,
        llm_caller: LLMCallerBase,
        graph_store: GraphStoreBase,
        todo_sorter: TodoSorter
    ):
        """初始化
        
        Args:
            llm_caller: LLM调用器
            graph_store: 图存储（WorkGraph）
            todo_sorter: 待办排序器
        """
        self.llm = llm_caller
        self.graph = graph_store
        self.sorter = todo_sorter
        logger.debug("TodoManager初始化完成")
    
    async def generate_and_sort(
        self,
        user_id: str,
        new_info: str,
        project_name: Optional[str] = None
    ) -> SortedTodoList:
        """生成并排序待办
        
        Args:
            user_id: 用户ID
            new_info: 用户提供的新信息
            project_name: 项目名称（可选）
            
        Returns:
            排序后的待办列表
        """
        logger.info(f"开始为用户 {user_id} 生成待办")
        
        # 1. 查询WorkGraph中已有的待办
        existing_todos = await self._fetch_existing_todos(user_id, project_name)
        logger.debug(f"查询到 {len(existing_todos)} 个已有待办")
        
        # 2. 使用LLM解析用户输入，生成新待办
        new_todos = await self._parse_todos_from_text(
            new_info,
            existing_todos,
            project_name
        )
        logger.info(f"LLM解析出 {len(new_todos)} 个新待办")
        
        # 3. 合并待办列表
        all_todos = existing_todos + new_todos
        
        # 4. 使用TodoSorter进行拓扑排序
        sorted_result = self.sorter.sort(
            all_todos,
            consider_dependencies=True,
            consider_due_date=True
        )
        logger.info(f"排序完成，共 {len(sorted_result.sorted_todos)} 个待办")
        
        # 5. 持久化新待办到WorkGraph
        if new_todos:
            await self._persist_todos_to_graph(user_id, new_todos, project_name)
        
        return sorted_result
    
    async def update_status(
        self,
        user_id: str,
        task_id: str,
        new_status: str
    ) -> bool:
        """更新待办状态
        
        Args:
            user_id: 用户ID
            task_id: 任务ID
            new_status: 新状态（pending/in_progress/completed）
            
        Returns:
            是否成功
        """
        try:
            # 验证状态值
            status_enum = TaskStatus(new_status)
            
            # 构建Cypher更新语句
            query = """
            MATCH (u:User {id: $user_id})-[:HAS_TASK]->(t:Task {id: $task_id})
            SET t.status = $new_status, t.updated_at = $updated_at
            RETURN t
            """
            
            params = {
                "user_id": user_id,
                "task_id": task_id,
                "new_status": new_status,
                "updated_at": datetime.now().isoformat()
            }
            
            result = await self.graph.execute_query(query, params)
            
            if result:
                logger.info(f"任务 {task_id} 状态更新为 {new_status}")
                return True
            else:
                logger.warning(f"未找到任务 {task_id}")
                return False
                
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False
    
    async def get_active_todos(
        self,
        user_id: str,
        project_name: Optional[str] = None
    ) -> SortedTodoList:
        """获取活跃待办（已排序）
        
        Args:
            user_id: 用户ID
            project_name: 项目名称（可选）
            
        Returns:
            排序后的待办列表
        """
        todos = await self._fetch_existing_todos(user_id, project_name)
        
        # 排序
        sorted_result = self.sorter.sort(
            todos,
            consider_dependencies=True,
            consider_due_date=True
        )
        
        return sorted_result
    
    async def _fetch_existing_todos(
        self,
        user_id: str,
        project_name: Optional[str] = None
    ) -> List[TodoItem]:
        """从WorkGraph查询已有待办
        
        Args:
            user_id: 用户ID
            project_name: 项目名称（可选）
            
        Returns:
            待办列表
        """
        try:
            # 构建Cypher查询
            if project_name:
                query = """
                MATCH (u:User {id: $user_id})-[:HAS_TASK]->(t:Task)
                WHERE t.project_name = $project_name AND t.status <> 'completed'
                OPTIONAL MATCH (t)-[d:DEPENDS_ON]->(dep:Task)
                RETURN t, collect(dep.id) as dependencies
                """
                params = {"user_id": user_id, "project_name": project_name}
            else:
                query = """
                MATCH (u:User {id: $user_id})-[:HAS_TASK]->(t:Task)
                WHERE t.status <> 'completed'
                OPTIONAL MATCH (t)-[d:DEPENDS_ON]->(dep:Task)
                RETURN t, collect(dep.id) as dependencies
                """
                params = {"user_id": user_id}
            
            result = await self.graph.execute_query(query, params)
            
            todos = []
            if result and "data" in result:
                for row in result["data"]:
                    task_node = row.get("t")
                    deps = row.get("dependencies", [])
                    
                    if task_node:
                        todos.append(self._node_to_todo_item(task_node, deps))
            
            return todos
            
        except Exception as e:
            logger.error(f"查询待办失败: {e}")
            return []
    
    async def _parse_todos_from_text(
        self,
        text: str,
        existing_todos: List[TodoItem],
        project_name: Optional[str] = None
    ) -> List[TodoItem]:
        """使用LLM解析文本生成待办列表
        
        Args:
            text: 用户输入文本
            existing_todos: 已有待办列表
            project_name: 项目名称
            
        Returns:
            新待办列表
        """
        # 构建已有待办摘要
        existing_summary = self._build_existing_summary(existing_todos)
        
        # 构建提示词
        prompt = f"""你是一位专业的任务管理助手，请基于用户的描述生成待办事项列表。

**用户输入:**
{text}

**已有待办（避免重复）:**
{existing_summary}

请生成新的待办事项，以JSON格式返回：

```json
[
  {{
    "id": "task_unique_id",
    "title": "任务标题",
    "description": "详细描述",
    "priority": "high/medium/low",
    "due_date": "2024-01-01T00:00:00",  // ISO格式，可选
    "dependencies": ["task_id1", "task_id2"]  // 依赖的任务ID，可选
  }}
]
```

注意事项:
1. id必须唯一，使用描述性的snake_case命名
2. priority只能是high/medium/low之一
3. dependencies中的task_id必须是已存在的任务
4. 如果没有新任务，返回空数组[]
5. 只返回JSON，不要其他内容

项目名称: {project_name or "无"}
"""
        
        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.generate(
                messages,
                max_tokens=1000,
                temperature=0.3
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
            new_todos = []
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
                    new_todos.append(todo)
                except Exception as e:
                    logger.error(f"解析待办项失败: {e}, 数据: {item}")
                    continue
            
            return new_todos
            
        except json.JSONDecodeError as e:
            logger.error(f"LLM返回的JSON格式错误: {e}, 原始内容: {response.content}")
            return []
        except Exception as e:
            logger.error(f"解析待办失败: {e}")
            return []
    
    async def _persist_todos_to_graph(
        self,
        user_id: str,
        todos: List[TodoItem],
        project_name: Optional[str] = None
    ):
        """持久化待办到WorkGraph
        
        Args:
            user_id: 用户ID
            todos: 待办列表
            project_name: 项目名称
        """
        try:
            for todo in todos:
                # 创建Task节点
                task_node = GraphNode(
                    label=NodeLabel.TASK,
                    properties={
                        "id": todo.id,
                        "title": todo.title,
                        "description": todo.description,
                        "priority": todo.priority.value,
                        "status": todo.status.value,
                        "due_date": todo.due_date.isoformat() if todo.due_date else None,
                        "project_name": project_name or "",
                        "created_at": todo.created_at.isoformat()
                    }
                )
                
                created_node = await self.graph.create_node(task_node)
                
                # 创建User->Task关系
                user_task_edge = GraphEdge(
                    source_id=user_id,
                    target_id=todo.id,
                    relation=RelationType.HAS_TASK,
                    properties={}
                )
                await self.graph.create_edge(user_task_edge)
                
                # 创建依赖关系
                for dep_id in todo.dependencies:
                    dep_edge = GraphEdge(
                        source_id=todo.id,
                        target_id=dep_id,
                        relation=RelationType.DEPENDS_ON,
                        properties={}
                    )
                    await self.graph.create_edge(dep_edge)
                
                logger.debug(f"待办 {todo.id} 已持久化到WorkGraph")
                
        except Exception as e:
            logger.error(f"持久化待办到图数据库失败: {e}")
    
    def _build_existing_summary(self, todos: List[TodoItem]) -> str:
        """构建已有待办摘要
        
        Args:
            todos: 待办列表
            
        Returns:
            摘要文本
        """
        if not todos:
            return "无"
        
        summary_lines = []
        for todo in todos[:20]:  # 最多显示20个
            summary_lines.append(f"- [{todo.id}] {todo.title} (优先级: {todo.priority.value})")
        
        return "\n".join(summary_lines)
    
    def _node_to_todo_item(
        self,
        node: GraphNode,
        dependencies: List[str]
    ) -> TodoItem:
        """将GraphNode转换为TodoItem
        
        Args:
            node: 图节点
            dependencies: 依赖列表
            
        Returns:
            待办项
        """
        props = node.properties
        
        return TodoItem(
            id=props.get("id", ""),
            title=props.get("title", ""),
            description=props.get("description", ""),
            priority=Priority(props.get("priority", "medium")),
            status=TaskStatus(props.get("status", "pending")),
            due_date=datetime.fromisoformat(props["due_date"]) if props.get("due_date") else None,
            dependencies=dependencies or [],
            created_at=datetime.fromisoformat(props["created_at"]) if props.get("created_at") else datetime.now()
        )
