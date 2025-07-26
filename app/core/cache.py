import json
import pickle
from typing import Any, Optional, Union, Callable
from functools import wraps
import hashlib
from datetime import datetime, timedelta

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheBackend:
    """缓存后端基类"""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """内存缓存实现"""
    
    def __init__(self):
        self._cache = {}
        self._expiry = {}
    
    async def get(self, key: str) -> Optional[Any]:
        if key in self._expiry and datetime.now() > self._expiry[key]:
            await self.delete(key)
            return None
        return self._cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        self._cache[key] = value
        if ttl:
            self._expiry[key] = datetime.now() + timedelta(seconds=ttl)
        return True
    
    async def delete(self, key: str) -> bool:
        self._cache.pop(key, None)
        self._expiry.pop(key, None)
        return True
    
    async def exists(self, key: str) -> bool:
        if key in self._expiry and datetime.now() > self._expiry[key]:
            await self.delete(key)
            return False
        return key in self._cache


class RedisCache(CacheBackend):
    """Redis缓存实现"""
    
    def __init__(self, redis_url: str):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not available. Install with: pip install redis")
        
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
    
    async def get(self, key: str) -> Optional[Any]:
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        try:
            data = pickle.dumps(value)
            if ttl:
                return self.redis_client.setex(key, ttl, data)
            else:
                return self.redis_client.set(key, data)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


class CacheManager:
    """缓存管理器"""
    
    def __init__(self):
        self.backend = self._create_backend()
    
    def _create_backend(self) -> CacheBackend:
        """创建缓存后端"""
        if REDIS_AVAILABLE and settings.REDIS_URL:
            try:
                return RedisCache(settings.REDIS_URL)
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Falling back to memory cache.")
        
        logger.info("Using memory cache backend")
        return MemoryCache()
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        return await self.backend.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        ttl = ttl or settings.CACHE_TTL
        return await self.backend.set(key, value, ttl)
    
    async def delete(self, key: str) -> bool:
        """删除缓存"""
        return await self.backend.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        return await self.backend.exists(key)


# 全局缓存管理器
cache_manager = CacheManager()


def cache(ttl: int = None, key_prefix: str = "cache"):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache_manager._generate_key(
                f"{key_prefix}:{func.__name__}", 
                *args, 
                **kwargs
            )
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # 执行函数
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # 缓存结果
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache set for key: {cache_key}")
            
            return result
        return wrapper
    return decorator


# 缓存工具函数
async def cache_user_session(user_id: int, session_data: dict, ttl: int = 3600):
    """缓存用户会话"""
    key = f"user_session:{user_id}"
    await cache_manager.set(key, session_data, ttl)


async def get_cached_user_session(user_id: int) -> Optional[dict]:
    """获取缓存的用户会话"""
    key = f"user_session:{user_id}"
    return await cache_manager.get(key)


async def invalidate_user_cache(user_id: int):
    """清除用户相关缓存"""
    patterns = [
        f"user_session:{user_id}",
        f"user_data:{user_id}",
        f"user_sessions:{user_id}",
    ]
    
    for pattern in patterns:
        await cache_manager.delete(pattern)