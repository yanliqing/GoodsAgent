from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    """令牌载荷模型"""
    sub: Optional[int] = None


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str