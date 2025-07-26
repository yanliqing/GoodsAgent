"""
自定义异常类
"""
from typing import Any, Dict, Optional


class BaseAppException(Exception):
    """应用基础异常类"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ModelConfigurationError(BaseAppException):
    """模型配置错误"""
    pass


class ModelProviderError(BaseAppException):
    """模型提供商错误"""
    pass


class APIKeyError(BaseAppException):
    """API密钥错误"""
    pass


class TaobaoAPIError(BaseAppException):
    """淘宝API错误"""
    pass


class ChatServiceError(BaseAppException):
    """聊天服务错误"""
    pass


class DatabaseError(BaseAppException):
    """数据库错误"""
    pass


class ValidationError(BaseAppException):
    """验证错误"""
    pass


class AuthenticationError(BaseAppException):
    """认证错误"""
    pass


class AuthorizationError(BaseAppException):
    """授权错误"""
    pass


class RateLimitError(BaseAppException):
    """速率限制错误"""
    pass