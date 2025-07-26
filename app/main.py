import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import settings
from app.core.middleware import (
    ExceptionHandlerMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# 添加中间件（注意顺序很重要）
# 1. 异常处理中间件（最外层）
app.add_middleware(ExceptionHandlerMiddleware)

# 2. 请求日志中间件
app.add_middleware(RequestLoggingMiddleware)

# 3. CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 设置模板
templates = Jinja2Templates(directory="templates")

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)