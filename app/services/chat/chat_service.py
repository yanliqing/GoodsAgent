from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import ChatSession, ChatMessage, User
from app.schemas.chat import MessageCreate, SessionCreate, ChatRequest, ChatResponse
from app.services.agent import TaobaoAgent


class ChatService:
    """聊天服务，管理用户会话和消息"""
    
    def __init__(self, db: Session):
        """初始化聊天服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.agents = {}  # 会话ID -> 智能体实例
    
    def get_or_create_session(self, user_id: int, session_id: Optional[int] = None) -> ChatSession:
        """获取或创建聊天会话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID，如果提供则获取现有会话，否则创建新会话
        
        Returns:
            聊天会话
        """
        if session_id:
            # 获取现有会话
            session = self.db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
                ChatSession.is_active == True
            ).first()
            
            if session:
                return session
        
        # 创建新会话
        session_create = SessionCreate(user_id=user_id)
        new_session = ChatSession(**session_create.dict())
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        
        return new_session
    
    def get_user_sessions(self, user_id: int) -> List[ChatSession]:
        """获取用户的所有聊天会话
        
        Args:
            user_id: 用户ID
        
        Returns:
            聊天会话列表
        """
        return self.db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).order_by(ChatSession.created_at.desc()).all()
    
    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        """获取会话的所有消息
        
        Args:
            session_id: 会话ID
        
        Returns:
            消息列表
        """
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
    
    def delete_session(self, session_id: int, user_id: int) -> bool:
        """删除用户的聊天会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
        
        Returns:
            是否删除成功
        """
        # 查找会话
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).first()
        
        if not session:
            return False
        
        # 软删除：将 is_active 设置为 False
        session.is_active = False
        
        # 清理对应的智能体实例
        if session_id in self.agents:
            del self.agents[session_id]
        
        self.db.commit()
        return True
    
    def hard_delete_session(self, session_id: int, user_id: int) -> bool:
        """硬删除用户的聊天会话（包括所有消息）
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
        
        Returns:
            是否删除成功
        """
        # 查找会话
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            return False
        
        # 删除所有相关消息
        self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()
        
        # 删除会话
        self.db.delete(session)
        
        # 清理对应的智能体实例
        if session_id in self.agents:
            del self.agents[session_id]
        
        self.db.commit()
        return True
    
    def save_message(self, message_create: MessageCreate) -> ChatMessage:
        """保存消息
        
        Args:
            message_create: 消息创建模型
        
        Returns:
            保存的消息
        """
        # 将 metadata 映射到 extra_data
        message_data = message_create.dict()
        metadata = message_data.pop('metadata', None)
        
        message = ChatMessage(
            session_id=message_data['session_id'],
            role=message_data['role'],
            content=message_data['content'],
            message_type=message_data['message_type'],
            extra_data=metadata  # 将 metadata 存储到 extra_data 字段
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def _get_agent(self, session_id: int) -> TaobaoAgent:
        """获取或创建智能体实例
        
        Args:
            session_id: 会话ID
        
        Returns:
            智能体实例
        """
        if session_id not in self.agents:
            self.agents[session_id] = TaobaoAgent(session_id=session_id)
        
        return self.agents[session_id]
    
    async def process_chat(self, user_id: int, chat_request: ChatRequest) -> ChatResponse:
        """处理聊天请求
        
        Args:
            user_id: 用户ID
            chat_request: 聊天请求
        
        Returns:
            聊天响应
        """
        # 获取或创建会话
        session = self.get_or_create_session(user_id, chat_request.session_id)
        
        # 保存用户消息
        user_message = MessageCreate(
            session_id=session.id,
            role="user",
            content=chat_request.message,
            message_type=chat_request.message_type,
            metadata=chat_request.metadata
        )
        self.save_message(user_message)
        
        # 获取智能体实例
        agent = self._get_agent(session.id)
        
        # 处理消息
        response = await agent.process_message(
            message=chat_request.message,
            message_type=chat_request.message_type,
            metadata=chat_request.metadata
        )
        
        # 保存助手消息
        assistant_message = MessageCreate(
            session_id=session.id,
            role="assistant",
            content=response["message"],
            message_type=response["message_type"],
            metadata=response["metadata"]
        )
        self.save_message(assistant_message)
        
        # 返回响应
        return ChatResponse(
            session_id=session.id,
            message=response["message"],
            message_type=response["message_type"],
            metadata=response["metadata"]
        )