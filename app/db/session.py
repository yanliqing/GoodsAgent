from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# 数据库引擎配置
engine_kwargs = {
    "connect_args": {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
}

# 如果是SQLite，使用StaticPool
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs.update({
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    })
else:
    # 对于其他数据库，配置连接池
    engine_kwargs.update({
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_pre_ping": True,  # 验证连接
        "pool_recycle": 3600,   # 1小时后回收连接
    })

# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

# 添加数据库事件监听器
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """为SQLite设置PRAGMA"""
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

@event.listens_for(engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """连接检出时的日志"""
    logger.debug("Database connection checked out")

@event.listens_for(engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """连接检入时的日志"""
    logger.debug("Database connection checked in")

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """获取数据库会话的上下文管理器
    
    Yields:
        数据库会话
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


class DatabaseManager:
    """数据库管理器"""
    
    @staticmethod
    def health_check() -> bool:
        """数据库健康检查
        
        Returns:
            数据库是否健康
        """
        try:
            with get_db_context() as db:
                db.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    def get_connection_info() -> dict:
        """获取连接池信息
        
        Returns:
            连接池信息
        """
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }