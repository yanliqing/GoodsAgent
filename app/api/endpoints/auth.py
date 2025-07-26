from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import authenticate_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash
from app.db.models import User
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import UserCreate, User as UserSchema

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    """用户登录
    
    Args:
        db: 数据库会话
        form_data: 表单数据，包含用户名和密码
    
    Returns:
        JWT令牌
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/json", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)) -> Any:
    """使用JSON格式登录
    
    Args:
        login_data: 登录数据
        db: 数据库会话
    
    Returns:
        JWT令牌
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserSchema)
async def register(user_data: UserCreate, db: Session = Depends(get_db)) -> Any:
    """用户注册
    
    Args:
        user_data: 用户数据
        db: 数据库会话
    
    Returns:
        注册的用户
    """
    # 检查用户名是否已存在
    user = db.query(User).filter(User.username == user_data.username).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )
    
    # 检查邮箱是否已存在
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在",
        )
    
    # 创建新用户
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user