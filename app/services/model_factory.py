"""
模型工厂类，支持多种AI模型提供商
"""
from typing import Any, Dict, Optional
from langchain_core.language_models.base import BaseLanguageModel
from langchain_openai import ChatOpenAI
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ModelConfigurationError, ModelProviderError, APIKeyError

logger = get_logger(__name__)

try:
    from langchain_community.llms import Tongyi
    QWEN_AVAILABLE = True
    logger.info("Qwen模型支持已加载")
except ImportError as e:
    QWEN_AVAILABLE = False
    logger.warning(f"Qwen模型支持不可用: {e}")


class ModelFactory:
    """AI模型工厂类"""
    
    @staticmethod
    def create_model(provider: Optional[str] = None, **kwargs) -> BaseLanguageModel:
        """
        创建AI模型实例
        
        Args:
            provider: 模型提供商 ('openai' 或 'qwen')
            **kwargs: 额外的模型参数
            
        Returns:
            BaseLanguageModel: 模型实例
            
        Raises:
            ModelProviderError: 当提供商不支持时
            ModelConfigurationError: 当配置无效时
            APIKeyError: 当API密钥缺失时
        """
        provider = provider or settings.MODEL_PROVIDER
        logger.info(f"正在创建 {provider} 模型实例")
        
        try:
            if provider == "openai":
                return ModelFactory._create_openai_model(**kwargs)
            elif provider == "qwen":
                return ModelFactory._create_qwen_model(**kwargs)
            else:
                raise ModelProviderError(
                    f"不支持的模型提供商: {provider}",
                    error_code="UNSUPPORTED_PROVIDER",
                    details={"provider": provider, "supported": ["openai", "qwen"]}
                )
        except Exception as e:
            logger.error(f"创建 {provider} 模型失败: {e}")
            raise
    
    @staticmethod
    def _create_openai_model(**kwargs) -> ChatOpenAI:
        """创建OpenAI模型"""
        if not settings.OPENAI_API_KEY:
            raise APIKeyError(
                "OPENAI_API_KEY 未设置",
                error_code="MISSING_OPENAI_KEY"
            )
        
        model_kwargs = {
            "model": kwargs.get("model", settings.OPENAI_MODEL),
            "temperature": kwargs.get("temperature", settings.OPENAI_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", settings.OPENAI_MAX_TOKENS),
            "openai_api_key": settings.OPENAI_API_KEY,
        }
        
        logger.info(f"创建OpenAI模型: {model_kwargs['model']}")
        return ChatOpenAI(**model_kwargs)
    
    @staticmethod
    def _create_qwen_model(**kwargs) -> Any:
        """创建Qwen模型"""
        if not QWEN_AVAILABLE:
            raise ModelConfigurationError(
                "Qwen模型支持不可用。请安装: pip install dashscope langchain-community",
                error_code="QWEN_DEPENDENCIES_MISSING"
            )
        
        if not settings.DASHSCOPE_API_KEY:
            raise APIKeyError(
                "DASHSCOPE_API_KEY 未设置",
                error_code="MISSING_DASHSCOPE_KEY"
            )
        
        # 设置DashScope API密钥
        try:
            import dashscope
            dashscope.api_key = settings.DASHSCOPE_API_KEY
        except ImportError:
            raise ModelConfigurationError(
                "无法导入dashscope模块",
                error_code="DASHSCOPE_IMPORT_ERROR"
            )
        
        model_kwargs = {
            "model_name": kwargs.get("model", settings.QWEN_MODEL),
            "temperature": kwargs.get("temperature", settings.QWEN_TEMPERATURE),
            "max_tokens": kwargs.get("max_tokens", settings.QWEN_MAX_TOKENS),
        }
        
        logger.info(f"创建Qwen模型: {model_kwargs['model_name']}")
        return Tongyi(**model_kwargs)
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """获取可用的模型提供商"""
        providers = {}
        
        # 检查OpenAI
        providers["openai"] = bool(settings.OPENAI_API_KEY)
        
        # 检查Qwen
        providers["qwen"] = QWEN_AVAILABLE and bool(settings.DASHSCOPE_API_KEY)
        
        logger.debug(f"可用的模型提供商: {providers}")
        return providers
    
    @staticmethod
    def validate_provider_config(provider: str) -> bool:
        """验证指定提供商的配置是否有效"""
        provider = provider.lower()
        
        if provider == "openai":
            return bool(settings.OPENAI_API_KEY)
        elif provider == "qwen":
            return QWEN_AVAILABLE and bool(settings.DASHSCOPE_API_KEY)
        else:
            return False
    
    @staticmethod
    def get_model_health() -> Dict[str, Any]:
        """获取模型健康状态"""
        current_provider = settings.MODEL_PROVIDER.lower()
        available_providers = ModelFactory.get_available_providers()
        
        health_status = {
            "current_provider": current_provider,
            "current_provider_healthy": available_providers.get(current_provider, False),
            "available_providers": available_providers,
            "total_available": sum(available_providers.values()),
            "recommendations": []
        }
        
        # 生成建议
        if not health_status["current_provider_healthy"]:
            if available_providers.get("qwen", False):
                health_status["recommendations"].append({
                    "action": "switch_provider",
                    "target": "qwen",
                    "reason": "Qwen模型已配置且可用"
                })
            elif available_providers.get("openai", False):
                health_status["recommendations"].append({
                    "action": "switch_provider", 
                    "target": "openai",
                    "reason": "OpenAI模型已配置且可用"
                })
            else:
                health_status["recommendations"].append({
                    "action": "configure_api_key",
                    "reason": "需要配置至少一个可用的AI模型API密钥"
                })
        
        return health_status


def get_model_info() -> Dict[str, Any]:
    """获取当前模型配置信息"""
    provider = settings.MODEL_PROVIDER.lower()
    
    info = {
        "provider": provider,
        "configured": ModelFactory.validate_provider_config(provider),
        "health": ModelFactory.get_model_health()
    }
    
    if provider == "openai":
        info.update({
            "model": settings.OPENAI_MODEL,
            "temperature": settings.OPENAI_TEMPERATURE,
            "max_tokens": settings.OPENAI_MAX_TOKENS,
            "api_key_configured": bool(settings.OPENAI_API_KEY),
            "api_key_preview": f"sk-...{settings.OPENAI_API_KEY[-4:]}" if settings.OPENAI_API_KEY else None
        })
    elif provider == "qwen":
        info.update({
            "model": settings.QWEN_MODEL,
            "temperature": settings.QWEN_TEMPERATURE,
            "max_tokens": settings.QWEN_MAX_TOKENS,
            "api_key_configured": bool(settings.DASHSCOPE_API_KEY),
            "api_key_preview": f"sk-...{settings.DASHSCOPE_API_KEY[-4:]}" if settings.DASHSCOPE_API_KEY else None
        })
    
    return info