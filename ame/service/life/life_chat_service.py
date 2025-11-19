"""
LifeChatService - 生活对话服务

提供智能对话能力，支持意图识别、上下文检索、个性化回复、记忆提取。

服务特性：
- ✓ 对话：支持多轮对话，Session管理
- ✓ 持久化：对话结束后提取记忆存入图谱
- 核心能力：意图识别 + 上下文检索 + 对话生成 + 记忆提取
"""

from typing import Dict, List, Optional, AsyncIterator
from loguru import logger
from datetime import datetime
import uuid

from ame.capability.factory import CapabilityFactory
from ame.foundation.nlp import IntentType


class SessionManager:
    """Session管理器"""
    
    def __init__(self):
        """初始化"""
        self._sessions: Dict[str, Dict] = {}
    
    def create_session(self, user_id: str) -> str:
        """创建新Session
        
        Args:
            user_id: 用户ID
            
        Returns:
            Session ID
        """
        session_id = f"session_{user_id}_{uuid.uuid4().hex[:8]}"
        self._sessions[session_id] = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        logger.debug(f"创建Session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """获取Session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session数据，不存在返回None
        """
        return self._sessions.get(session_id)
    
    def update_session(self, session_id: str, message: Dict[str, str]):
        """更新Session，添加消息
        
        Args:
            session_id: Session ID
            message: 消息对象
        """
        if session_id in self._sessions:
            self._sessions[session_id]["messages"].append(message)
            self._sessions[session_id]["last_activity"] = datetime.now()
    
    def close_session(self, session_id: str) -> Optional[Dict]:
        """关闭Session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session数据，不存在返回None
        """
        return self._sessions.pop(session_id, None)
    
    def list_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """列出Sessions
        
        Args:
            user_id: 用户ID（可选，用于过滤）
            
        Returns:
            Session ID列表
        """
        if user_id:
            return [
                sid for sid, session in self._sessions.items()
                if session["user_id"] == user_id
            ]
        return list(self._sessions.keys())


class LifeChatService:
    """生活对话服务
    
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
        graph_name: str = "life_graph",
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
        self.session_manager = SessionManager()
        
        # 通过工厂创建LLM和图存储
        self.llm_caller = self.factory.create_llm_caller(
            api_key=llm_api_key,
            model=llm_model,
            base_url=llm_base_url,
            cache_key="life_llm"
        )
        
        self.graph_store = self.factory.create_graph_store(
            host=graph_host,
            port=graph_port,
            graph_name=graph_name,
            password=graph_password,
            cache_key="life_graph"
        )
        
        # 创建Life能力包
        self.capabilities = self.factory.create_life_capability_package(
            llm_caller=self.llm_caller,
            graph_store=self.graph_store,
            cache_prefix="life_service"
        )
        
        logger.info("LifeChatService初始化完成")
    
    async def start_session(self, user_id: str = "default_user") -> str:
        """开始新的对话Session
        
        Args:
            user_id: 用户ID
            
        Returns:
            Session ID
        """
        session_id = self.session_manager.create_session(user_id)
        logger.info(f"开始新Session: {session_id}")
        return session_id
    
    async def chat(
        self,
        session_id: str,
        user_input: str,
        stream: bool = False
    ):
        """对话（完整输出或流式输出）
        
        Args:
            session_id: Session ID
            user_input: 用户输入
            stream: 是否流式输出
            
        Returns:
            如果stream=False，返回字符串回复
            如果stream=True，返回AsyncIterator[str]
        """
        # 1. 获取Session
        session = self.session_manager.get_session(session_id)
        if not session:
            error_msg = f"Session {session_id} 不存在"
            logger.error(error_msg)
            if stream:
                async def error_stream():
                    yield error_msg
                return error_stream()
            return error_msg
        
        try:
            # 2. 意图识别
            intent_result = await self.capabilities["intent_recognizer"].recognize(
                user_input,
                use_llm=True
            )
            logger.debug(f"识别意图: {intent_result.intent.value}, 置信度: {intent_result.confidence}")
            
            # 3. 上下文检索
            contexts = await self.capabilities["context_retriever"].retrieve_by_intent(
                intent=intent_result.intent,
                limit=5
            )
            logger.debug(f"检索到 {len(contexts)} 条上下文")
            
            # 4. 生成回复
            conversation_history = session["messages"]
            
            if stream:
                # 流式生成
                response_stream = self.capabilities["dialogue_generator"].generate_stream(
                    user_input=user_input,
                    intent=intent_result.intent,
                    contexts=contexts,
                    conversation_history=conversation_history
                )
                
                # 收集完整回复用于保存
                full_response = ""
                async def collected_stream():
                    nonlocal full_response
                    async for chunk in response_stream:
                        full_response += chunk
                        yield chunk
                    
                    # 流式输出完成后保存消息
                    self._save_messages(session_id, user_input, full_response)
                
                return collected_stream()
            else:
                # 完整生成
                response = await self.capabilities["dialogue_generator"].generate(
                    user_input=user_input,
                    intent=intent_result.intent,
                    contexts=contexts,
                    conversation_history=conversation_history
                )
                
                # 保存消息
                self._save_messages(session_id, user_input, response)
                
                return response
                
        except Exception as e:
            logger.error(f"对话处理失败: {e}")
            error_msg = "抱歉，处理您的消息时出现错误。"
            if stream:
                async def error_stream():
                    yield error_msg
                return error_stream()
            return error_msg
    
    def _save_messages(self, session_id: str, user_input: str, assistant_response: str):
        """保存消息到Session
        
        Args:
            session_id: Session ID
            user_input: 用户输入
            assistant_response: 助手回复
        """
        self.session_manager.update_session(
            session_id,
            {"role": "user", "content": user_input}
        )
        self.session_manager.update_session(
            session_id,
            {"role": "assistant", "content": assistant_response}
        )
    
    async def end_session(self, session_id: str, extract_memory: bool = True) -> Dict:
        """结束Session
        
        Args:
            session_id: Session ID
            extract_memory: 是否提取记忆
            
        Returns:
            结束结果（包含记忆提取统计）
        """
        session = self.session_manager.close_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} 不存在")
            return {"error": "Session不存在"}
        
        logger.info(f"结束Session: {session_id}")
        
        result = {
            "session_id": session_id,
            "message_count": len(session["messages"]),
            "duration": (datetime.now() - session["created_at"]).total_seconds()
        }
        
        # 提取记忆（可选）
        if extract_memory and session["messages"]:
            try:
                memory_result = await self.capabilities["memory_extractor"].extract_and_save(
                    session_id=session_id,
                    messages=session["messages"],
                    extract_entities=True,
                    analyze_emotions=True
                )
                result["memory"] = memory_result
                logger.info(f"记忆提取完成: {memory_result}")
            except Exception as e:
                logger.error(f"记忆提取失败: {e}")
                result["memory_error"] = str(e)
        
        return result
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """获取Session信息
        
        Args:
            session_id: Session ID
            
        Returns:
            Session信息
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            return None
        
        return {
            "session_id": session["session_id"],
            "user_id": session["user_id"],
            "message_count": len(session["messages"]),
            "created_at": session["created_at"],
            "last_activity": session["last_activity"]
        }
    
    def list_active_sessions(self, user_id: Optional[str] = None) -> List[str]:
        """列出活跃的Sessions
        
        Args:
            user_id: 用户ID（可选）
            
        Returns:
            Session ID列表
        """
        return self.session_manager.list_sessions(user_id=user_id)
