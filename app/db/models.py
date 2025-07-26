from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship

from app.db.base_model import Base


class User(Base):
    """用户模型"""
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # 关联的聊天会话
    chat_sessions = relationship("ChatSession", back_populates="user")
    

class ChatSession(Base):
    """聊天会话模型"""
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    title = Column(String(100), default="新会话")
    is_active = Column(Boolean, default=True)
    
    # 关联
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """聊天消息模型"""
    session_id = Column(Integer, ForeignKey("chatsession.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, image, product
    extra_data = Column(JSON, nullable=True)  # 存储额外信息，如商品数据、图片URL等
    
    # 关联
    session = relationship("ChatSession", back_populates="messages")


class Product(Base):
    """商品模型，用于缓存淘宝商品信息"""
    item_id = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    price = Column(String(20), nullable=False)
    original_price = Column(String(20), nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    detail_url = Column(String(500), nullable=True)
    category = Column(String(100), nullable=True)
    shop_name = Column(String(100), nullable=True)
    rating = Column(String(10), nullable=True)
    sales = Column(String(50), nullable=True)
    extra_data = Column(JSON, nullable=True)  # 存储其他商品信息