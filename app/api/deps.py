from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import get_db
from app.db.models import User
from app.schemas.auth import TokenPayload

# OAuth2 认证方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    """获取当前用户
    
    Args:
        db: 数据库会话
        token: JWT令牌
    
    Returns:
        当前用户
    
    Raises:
        HTTPException: 认证失败时抛出
    """
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无法验证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户
    user = db.query(User).filter(User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户未激活")
    
    return user


def get_current_active_superuser(current_user: User = Depends(get_current_user)) -> User:
    """获取当前超级用户
    
    Args:
        current_user: 当前用户
    
    Returns:
        当前超级用户
    
    Raises:
        HTTPException: 用户不是超级用户时抛出
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="权限不足"
        )
    return current_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """验证用户
    
    Args:
        db: 数据库会话
        username: 用户名
        password: 密码
    
    Returns:
        验证成功返回用户，否则返回None
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user