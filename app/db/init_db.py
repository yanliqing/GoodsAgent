import logging
from sqlalchemy.exc import IntegrityError

from app.core.security import get_password_hash
from app.db.base_model import Base
from app.db.session import engine, SessionLocal
from app.db.models import User, ChatSession, ChatMessage, Product

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    # 创建初始超级用户
    db = SessionLocal()
    try:
        # 检查是否已存在超级用户
        user = db.query(User).filter(User.is_superuser == True).first()
        if not user:
            user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin"),
                is_superuser=True,
            )
            db.add(user)
            db.commit()
            logger.info("Created initial superuser")
    except IntegrityError:
        db.rollback()
        logger.warning("Superuser already exists")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Creating initial data")
    init_db()
    logger.info("Initial data created")