"""
待办管理服务 - 管理用户的待办事项

遵循架构规范：
- 通过CapabilityFactory获取所有能力
- 不直接使用Foundation层组件
"""

from typing import List, Optional
from loguru import logger

from ame.capability.factory import CapabilityFactory
from ame.foundation.algorithm import TodoItem, SortedTodoList


class WorkTodoService:
    """待办管理服务
    
    遵循架构规范：
    - 通过CapabilityFactory获取所有能力
    - 不直接使用Foundation层组件
    """
    
    def __init__(
        self,
        capability_factory: CapabilityFactory,
        llm_api_key: str,
        llm_model: str = "gpt-3.5-turbo",
        llm_base_url: Optional[str] = None,
        graph_host: str = "localhost",
        graph_port: int = 6379,
        graph_name: str = "work_graph",
        graph_password: Optional[str] = None
    ):
        """初始化
        
        Args:
            capability_factory: 能力工厂
            llm_api_key: LLM API密钥
            llm_model: LLM模型名称
            llm_base_url: LLM API基础URL
            graph_host: 图数据库主机
            graph_port: 图数据库端口
            graph_name: 图名称
            graph_password: 图数据库密码
        """
        self.factory = capability_factory
        
        # 通过工厂创建能力
        self.todo_manager = self.factory.create_todo_manager(
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
            graph_host=graph_host,
            graph_port=graph_port,
            graph_name=graph_name,
            graph_password=graph_password,
            cache_key="work_todo_manager"
        )
        
        logger.info("WorkTodoService初始化完成")
    
    async def generate_todos(
        self,
        user_id: str,
        new_info: str,
        project_name: Optional[str] = None
    ) -> SortedTodoList:
        """生成新待办
        
        Args:
            user_id: 用户ID
            new_info: 用户提供的新信息
            project_name: 项目名称（可选）
            
        Returns:
            排序后的待办列表
        """
        logger.info(f"用户 {user_id} 生成待办，项目: {project_name or '无'}")
        
        try:
            sorted_list = await self.todo_manager.generate_and_sort(
                user_id=user_id,
                new_info=new_info,
                project_name=project_name
            )
            
            logger.info(f"待办生成成功，共 {len(sorted_list.sorted_todos)} 个任务")
            return sorted_list
            
        except Exception as e:
            logger.error(f"生成待办失败: {e}")
            raise
    
    async def update_todo_status(
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
        logger.info(f"用户 {user_id} 更新任务 {task_id} 状态为 {new_status}")
        
        try:
            success = await self.todo_manager.update_status(
                user_id=user_id,
                task_id=task_id,
                new_status=new_status
            )
            
            if success:
                logger.info(f"任务状态更新成功")
            else:
                logger.warning(f"任务状态更新失败")
            
            return success
            
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            raise
    
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
        logger.info(f"用户 {user_id} 查询活跃待办，项目: {project_name or '全部'}")
        
        try:
            sorted_list = await self.todo_manager.get_active_todos(
                user_id=user_id,
                project_name=project_name
            )
            
            logger.info(f"查询到 {len(sorted_list.sorted_todos)} 个活跃待办")
            return sorted_list
            
        except Exception as e:
            logger.error(f"查询活跃待办失败: {e}")
            raise
    
    async def get_todos_by_priority(
        self,
        user_id: str,
        priority: str,
        project_name: Optional[str] = None
    ) -> List[TodoItem]:
        """按优先级获取待办
        
        Args:
            user_id: 用户ID
            priority: 优先级（high/medium/low）
            project_name: 项目名称（可选）
            
        Returns:
            待办列表
        """
        logger.info(f"用户 {user_id} 查询 {priority} 优先级待办")
        
        try:
            sorted_list = await self.get_active_todos(
                user_id=user_id,
                project_name=project_name
            )
            
            # 从分组中获取指定优先级的待办
            priority_todos = sorted_list.groups.get(priority, [])
            
            logger.info(f"查询到 {len(priority_todos)} 个 {priority} 优先级待办")
            return priority_todos
            
        except Exception as e:
            logger.error(f"按优先级查询待办失败: {e}")
            raise
    
    async def get_blocked_todos(
        self,
        user_id: str,
        project_name: Optional[str] = None
    ) -> List[TodoItem]:
        """获取被阻塞的待办
        
        Args:
            user_id: 用户ID
            project_name: 项目名称（可选）
            
        Returns:
            被阻塞的待办列表
        """
        logger.info(f"用户 {user_id} 查询被阻塞的待办")
        
        try:
            sorted_list = await self.get_active_todos(
                user_id=user_id,
                project_name=project_name
            )
            
            blocked_todos = sorted_list.blocked_todos
            
            logger.info(f"查询到 {len(blocked_todos)} 个被阻塞的待办")
            return blocked_todos
            
        except Exception as e:
            logger.error(f"查询被阻塞待办失败: {e}")
            raise
