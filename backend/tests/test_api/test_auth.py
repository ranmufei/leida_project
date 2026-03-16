"""
认证API测试
"""
import pytest
from fastapi.testclient import TestClient


def test_login_success(client: TestClient, test_user):
    """
    测试成功登录
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "testpass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user):
    """
    测试错误密码登录
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert data["code"] == 401
    assert "detail" in data


def test_login_nonexistent_user(client: TestClient):
    """
    测试不存在的用户登录
    """
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "nonexistent",
            "password": "password123"
        }
    )

    assert response.status_code == 401


def test_logout(client: TestClient, auth_headers):
    """
    测试登出
    """
    response = client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
