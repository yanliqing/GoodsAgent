import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db, DatabaseManager
from app.schemas.responses import HealthCheckResponse, success_response
from app.core.logging import get_logger
from app.services.model_factory import get_model_info, ModelFactory
from app.core.monitoring import get_monitor

logger = get_logger(__name__)
router = APIRouter()

# 应用启动时间
app_start_time = time.time()


async def check_database_health() -> bool:
    """检查数据库健康状态"""
    try:
        return DatabaseManager.health_check()
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_openai_health() -> bool:
    """检查OpenAI服务健康状态"""
    if not settings.OPENAI_API_KEY:
        return False
    
    try:
        # 这里可以添加实际的OpenAI API调用测试
        # 为了避免频繁调用，可以使用简单的配置检查
        return bool(settings.OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"OpenAI health check failed: {e}")
        return False


async def check_cache_health() -> bool:
    """检查缓存服务健康状态"""
    try:
        from app.core.cache import cache_manager
        # 简单的缓存测试
        test_key = "health_check_test"
        await cache_manager.set(test_key, "test_value", 10)
        result = await cache_manager.get(test_key)
        await cache_manager.delete(test_key)
        return result == "test_value"
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return False


def get_system_info() -> Dict[str, Any]:
    """获取系统信息"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": disk.percent,
            "disk_free_gb": round(disk.free / (1024**3), 2),
        }
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {}


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    健康检查端点
    
    返回应用程序和各个服务的健康状态
    """
    uptime = time.time() - app_start_time
    
    # 检查各个服务的健康状态
    services = {
        "database": await check_database_health(),
        "openai": await check_openai_health(),
        "cache": await check_cache_health(),
    }
    
    # 确定整体状态
    overall_status = "healthy" if all(services.values()) else "unhealthy"
    
    return HealthCheckResponse(
        status=overall_status,
        version=settings.VERSION,
        services=services,
        uptime=uptime
    )


@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    详细健康检查端点
    
    返回详细的系统和服务信息
    """
    uptime = time.time() - app_start_time
    
    # 基础服务检查
    services = {
        "database": await check_database_health(),
        "openai": await check_openai_health(),
        "cache": await check_cache_health(),
    }
    
    # 数据库连接池信息
    db_info = {}
    try:
        db_info = DatabaseManager.get_connection_info()
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
    
    # 系统信息
    system_info = get_system_info()
    
    # 配置信息（敏感信息已脱敏）
    config_info = {
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "database_url": "***" if settings.DATABASE_URL else None,
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "taobao_configured": bool(settings.TAOBAO_APP_KEY and settings.TAOBAO_APP_SECRET),
    }
    
    # AI模型信息
    model_info = get_model_info()
    
    overall_status = "healthy" if all(services.values()) else "unhealthy"
    
    return success_response({
        "status": overall_status,
        "version": settings.VERSION,
        "uptime": uptime,
        "services": services,
        "database": db_info,
        "system": system_info,
        "config": config_info,
        "model": model_info,
        "timestamp": time.time()
    })


@router.get("/health/database")
async def database_health_check():
    """数据库专用健康检查"""
    is_healthy = await check_database_health()
    
    if not is_healthy:
        return {
            "status": "unhealthy",
            "message": "Database connection failed"
        }
    
    try:
        db_info = DatabaseManager.get_connection_info()
        return success_response({
            "status": "healthy",
            "connection_pool": db_info
        })
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database info retrieval failed: {str(e)}"
        }


@router.get("/health/services")
async def services_health_check():
    """外部服务健康检查"""
    services = {
        "openai": await check_openai_health(),
        "cache": await check_cache_health(),
    }
    
    overall_status = "healthy" if all(services.values()) else "partial"
    
    return success_response({
        "status": overall_status,
        "services": services
    })


@router.get("/health/model")
async def model_health_check():
    """AI模型配置和健康检查"""
    model_info = get_model_info()
    available_providers = ModelFactory.get_available_providers()
    
    # 检查当前配置的模型是否可用
    current_provider = settings.MODEL_PROVIDER
    is_current_valid = ModelFactory.validate_provider_config(current_provider)
    
    status = "healthy" if is_current_valid else "unhealthy"
    
    return success_response({
        "status": status,
        "current_provider": current_provider,
        "current_provider_valid": is_current_valid,
        "available_providers": available_providers,
        "model_info": model_info,
        "recommendations": _get_model_recommendations(available_providers, current_provider)
    })


def _get_model_recommendations(available_providers: Dict[str, bool], current_provider: str) -> Dict[str, str]:
    """获取模型配置建议"""
    recommendations = {}
    
    if not available_providers.get(current_provider, False):
        if available_providers.get("qwen", False):
            recommendations["switch_to"] = "qwen"
            recommendations["reason"] = "Qwen模型已配置且可用，建议切换以避免OpenAI配额限制"
        elif available_providers.get("openai", False):
            recommendations["switch_to"] = "openai"
            recommendations["reason"] = "OpenAI模型已配置且可用"
        else:
            recommendations["action"] = "configure_api_key"
            recommendations["reason"] = "需要配置至少一个可用的AI模型API密钥"
    
    return recommendations


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """获取应用指标"""
    monitor = get_monitor()
    return monitor.export_metrics()


@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """获取系统指标"""
    monitor = get_monitor()
    return monitor.get_system_metrics()


@router.get("/performance")
async def get_performance_status() -> Dict[str, Any]:
    """获取性能状态"""
    monitor = get_monitor()
    health_status = monitor.get_health_status()
    metrics_summary = monitor.metrics.get_metrics_summary()
    
    return {
        "status": health_status["status"],
        "health_checks": health_status["checks"],
        "uptime": health_status["uptime"],
        "request_metrics": {
            "total_requests": sum(
                count for name, count in metrics_summary["counters"].items()
                if "http_requests_total" in name
            ),
            "error_count": sum(
                count for name, count in metrics_summary["counters"].items()
                if "errors_total" in name
            ),
            "avg_response_time": None  # 可以从直方图计算
        },
        "timestamp": time.time()
    }