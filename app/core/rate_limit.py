import time
from typing import Dict, Optional
from collections import defaultdict, deque
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """速率限制器"""
    
    def __init__(self, max_requests: int, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, identifier: str) -> bool:
        """检查是否允许请求"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # 清理过期的请求记录
        request_times = self.requests[identifier]
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # 检查是否超过限制
        if len(request_times) >= self.max_requests:
            return False
        
        # 记录当前请求
        request_times.append(now)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """获取剩余请求数"""
        now = time.time()
        window_start = now - self.window_seconds
        
        request_times = self.requests[identifier]
        # 清理过期的请求记录
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        return max(0, self.max_requests - len(request_times))
    
    def get_reset_time(self, identifier: str) -> Optional[float]:
        """获取重置时间"""
        request_times = self.requests[identifier]
        if not request_times:
            return None
        
        return request_times[0] + self.window_seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件"""
    
    def __init__(
        self, 
        app: ASGIApp,
        max_requests: int = None,
        window_seconds: int = 60,
        exempt_paths: list = None
    ):
        super().__init__(app)
        self.rate_limiter = RateLimiter(
            max_requests or settings.RATE_LIMIT_PER_MINUTE,
            window_seconds
        )
        self.exempt_paths = exempt_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否为豁免路径
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # 获取客户端标识符
        identifier = self._get_identifier(request)
        
        # 检查速率限制
        if not self.rate_limiter.is_allowed(identifier):
            remaining = self.rate_limiter.get_remaining_requests(identifier)
            reset_time = self.rate_limiter.get_reset_time(identifier)
            
            logger.warning(
                f"Rate limit exceeded for {identifier}",
                extra={
                    "identifier": identifier,
                    "path": request.url.path,
                    "method": request.method,
                }
            )
            
            headers = {
                "X-RateLimit-Limit": str(self.rate_limiter.max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(reset_time)) if reset_time else "0",
            }
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers=headers
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加速率限制头部
        remaining = self.rate_limiter.get_remaining_requests(identifier)
        reset_time = self.rate_limiter.get_reset_time(identifier)
        
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        if reset_time:
            response.headers["X-RateLimit-Reset"] = str(int(reset_time))
        
        return response
    
    def _get_identifier(self, request: Request) -> str:
        """获取客户端标识符"""
        # 优先使用用户ID（如果已认证）
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"
        
        # 使用IP地址
        client_ip = request.client.host if request.client else "unknown"
        
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            client_ip = real_ip
        
        return f"ip:{client_ip}"


class APIKeyRateLimiter:
    """API密钥速率限制器"""
    
    def __init__(self):
        self.limiters: Dict[str, RateLimiter] = {}
        self.default_limiter = RateLimiter(
            max_requests=settings.RATE_LIMIT_PER_MINUTE,
            window_seconds=60
        )
    
    def add_api_key_limit(self, api_key: str, max_requests: int, window_seconds: int = 60):
        """为特定API密钥添加速率限制"""
        self.limiters[api_key] = RateLimiter(max_requests, window_seconds)
    
    def is_allowed(self, api_key: str) -> bool:
        """检查API密钥是否允许请求"""
        limiter = self.limiters.get(api_key, self.default_limiter)
        return limiter.is_allowed(api_key)
    
    def get_remaining_requests(self, api_key: str) -> int:
        """获取API密钥剩余请求数"""
        limiter = self.limiters.get(api_key, self.default_limiter)
        return limiter.get_remaining_requests(api_key)


# 全局速率限制器实例
api_key_rate_limiter = APIKeyRateLimiter()


def rate_limit(max_requests: int, window_seconds: int = 60):
    """速率限制装饰器"""
    limiter = RateLimiter(max_requests, window_seconds)
    
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            identifier = request.client.host if request.client else "unknown"
            
            if not limiter.is_allowed(identifier):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator