import pytest
import asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base_model import Base
from app.db.session import get_db
from app.core.config import settings


# 测试数据库配置
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """测试数据库会话"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 清理表
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """创建测试客户端"""
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    """测试用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def test_chat_data():
    """测试聊天数据"""
    return {
        "message": "Hello, this is a test message",
        "session_id": None
    }


class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_user(db: Session, **kwargs):
        """创建测试用户"""
        from app.db.models import User
        from app.core.security import get_password_hash
        
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "hashed_password": get_password_hash("testpassword123"),
            "is_active": True,
            "is_superuser": False,
            **kwargs
        }
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def create_chat_session(db: Session, user_id: int, **kwargs):
        """创建测试聊天会话"""
        from app.db.models import ChatSession
        
        session_data = {
            "user_id": user_id,
            "title": "Test Session",
            "is_active": True,
            **kwargs
        }
        
        session = ChatSession(**session_data)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    
    @staticmethod
    def create_chat_message(db: Session, session_id: int, **kwargs):
        """创建测试聊天消息"""
        from app.db.models import ChatMessage
        
        message_data = {
            "session_id": session_id,
            "role": "user",
            "content": "Test message",
            **kwargs
        }
        
        message = ChatMessage(**message_data)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message


@pytest.fixture
def test_factory():
    """测试数据工厂实例"""
    return TestDataFactory()


# 异步测试支持
@pytest.fixture
async def async_client() -> AsyncGenerator[TestClient, None]:
    """异步测试客户端"""
    from httpx import AsyncClient
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Mock 工具
class MockOpenAI:
    """Mock OpenAI 客户端"""
    
    def __init__(self):
        self.chat = MockChatCompletion()


class MockChatCompletion:
    """Mock ChatCompletion"""
    
    def create(self, **kwargs):
        """Mock create 方法"""
        return {
            "choices": [{
                "message": {
                    "content": "This is a mock response from OpenAI"
                }
            }]
        }


@pytest.fixture
def mock_openai(monkeypatch):
    """Mock OpenAI 客户端"""
    mock_client = MockOpenAI()
    monkeypatch.setattr("app.services.agent.openai_client", mock_client)
    return mock_client


# 测试配置
@pytest.fixture(autouse=True)
def test_settings(monkeypatch):
    """测试环境配置"""
    monkeypatch.setattr(settings, "ENVIRONMENT", "testing")
    monkeypatch.setattr(settings, "DATABASE_URL", SQLALCHEMY_DATABASE_URL)
    monkeypatch.setattr(settings, "JWT_SECRET", "test-secret-key-for-testing-only")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(settings, "TAOBAO_APP_KEY", "test-taobao-key")
    monkeypatch.setattr(settings, "TAOBAO_APP_SECRET", "test-taobao-secret")