from typing import Callable
import traceback
import time
import uuid
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.logging import get_logger
# from app.core.monitoring import get_monitor

logger = get_logger(__name__)


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Global exception handler middleware"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except HTTPException:
            # Re-raise HTTP exceptions to be handled by FastAPI
            raise
        except Exception as exc:
            # Log the exception
            logger.error(
                f"Unhandled exception in {request.method} {request.url}",
                extra={
                    "method": request.method,
                    "url": str(request.url),
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                    "traceback": traceback.format_exc()
                },
                exc_info=True
            )
            
            # Return a generic error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "error_id": id(exc),  # Unique error ID for tracking
                    "type": "internal_error"
                }
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced request logging middleware with performance monitoring"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始
        start_time = time.time()
        
        # 获取客户端信息
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(
            f"Request started",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": client_ip,
                "user_agent": user_agent
            }
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(
                f"Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )
            
            # 记录性能指标
            # monitor = get_monitor()
            # monitor.record_request(
            #     method=request.method,
            #     endpoint=request.url.path,
            #     status_code=response.status_code,
            #     duration=process_time
            # )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误
            logger.error(
                f"Request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "error": str(e),
                    "process_time": process_time
                },
                exc_info=True
            )
            
            # 记录错误指标
            # monitor = get_monitor()
            # monitor.record_error(
            #     error_type=type(e).__name__,
            #     component="middleware"
            # )
            
            # 重新抛出异常
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期记录
        if client_ip in self.clients:
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if current_time - timestamp < self.period
            ]
        else:
            self.clients[client_ip] = []
        
        # 检查速率限制
        if len(self.clients[client_ip]) >= self.calls:
            logger.warning(
                f"Rate limit exceeded for client {client_ip}",
                extra={
                    "client_ip": client_ip,
                    "calls": len(self.clients[client_ip]),
                    "limit": self.calls
                }
            )
            
            # 记录速率限制指标
            monitor = get_monitor()
            monitor.record_error(
                error_type="RateLimitExceeded",
                component="middleware"
            )
            
            raise HTTPException(status_code=429, detail="Too Many Requests")
        
        # 记录请求时间
        self.clients[client_ip].append(current_time)
        
        return await call_next(request)