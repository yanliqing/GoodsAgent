from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.models import User, ChatSession, ChatMessage
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    Session as SessionSchema,
    Message as MessageSchema,
    ImageSearchRequest,
)
from app.services.chat import ChatService

router = APIRouter()


@router.post("/send", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """发送聊天消息
    
    Args:
        chat_request: 聊天请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        聊天响应
    """
    chat_service = ChatService(db)
    response = await chat_service.process_chat(current_user.id, chat_request)
    return response


@router.post("/image-search", response_model=ChatResponse)
async def image_search(
    search_request: ImageSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """图片搜索
    
    Args:
        search_request: 图片搜索请求
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        聊天响应
    """
    # 创建聊天请求
    chat_request = ChatRequest(
        session_id=search_request.session_id,
        message=search_request.message or "请帮我找一下这张图片中的商品",
        message_type="image",
        metadata={"image_data": search_request.image_data}
    )
    
    # 处理请求
    chat_service = ChatService(db)
    response = await chat_service.process_chat(current_user.id, chat_request)
    return response


@router.get("/sessions", response_model=List[SessionSchema])
async def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取用户的所有聊天会话
    
    Args:
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        聊天会话列表
    """
    chat_service = ChatService(db)
    sessions = chat_service.get_user_sessions(current_user.id)
    
    # 手动转换 ORM 对象为 Pydantic 模型
    return [SessionSchema.from_orm(session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=SessionSchema)
async def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取指定的聊天会话
    
    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        聊天会话
    """
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 手动转换 ORM 对象为 Pydantic 模型
    return SessionSchema.from_orm(session)


@router.get("/sessions/{session_id}/messages", response_model=List[MessageSchema])
async def get_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取会话的所有消息
    
    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        消息列表
    """
    # 验证会话是否属于当前用户
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    
    # 获取消息
    chat_service = ChatService(db)
    messages = chat_service.get_session_messages(session_id)
    
    # 手动转换 ORM 对象为 Pydantic 模型
    return [MessageSchema.from_orm(message) for message in messages]


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    hard_delete: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """删除聊天会话
    
    Args:
        session_id: 会话ID
        hard_delete: 是否硬删除（完全删除数据），默认为软删除
        db: 数据库会话
        current_user: 当前用户
    
    Returns:
        删除结果
    """
    chat_service = ChatService(db)
    
    if hard_delete:
        success = chat_service.hard_delete_session(session_id, current_user.id)
    else:
        success = chat_service.delete_session(session_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在或已被删除"
        )
    
    return {
        "success": True,
        "message": "会话删除成功",
        "session_id": session_id,
        "hard_delete": hard_delete
    }