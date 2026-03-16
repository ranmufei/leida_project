"""
测试配置文件
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from typing import Generator

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

# 测试数据库URL
TEST_DATABASE_URL = "sqlite:///./test.db"

# 创建测试引擎
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# 创建测试会话
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def db() -> Generator:
    """
    创建测试数据库会话
    """
    # 创建所有表
    Base.metadata.create_all(bind=test_engine)

    # 创建会话
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # 清理所有表
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db) -> Generator:
    """
    创建测试客户端
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db):
    """
    创建测试用户
    """
    from app.models.user import User
    from app.core.security import get_password_hash

    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def test_token(client, test_user):
    """
    获取测试Token
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )

    return response.json()["data"]["access_token"]


@pytest.fixture
def auth_headers(test_token):
    """
    获取认证头
    """
    return {"Authorization": f"Bearer {test_token}"}


@pytest.fixture
def test_site(db):
    """
    创建测试站点
    """
    from app.models.site import Site

    site = Site(
        name="测试站点",
        code="TEST001",
        longitude=116.4,
        latitude=39.9,
        altitude=50,
        region="北京",
        description="用于测试的站点"
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    return site
