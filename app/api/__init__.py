from fastapi import APIRouter

from app.api.endpoints import auth, chat, product, health

api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(chat.router, prefix="/chat", tags=["聊天"])
api_router.include_router(product.router, prefix="/product", tags=["商品"])
api_router.include_router(health.router, prefix="/health", tags=["健康检查"])