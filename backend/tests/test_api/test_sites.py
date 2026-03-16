"""
站点管理API测试
"""
import pytest
from fastapi.testclient import TestClient


def test_create_site(client: TestClient, auth_headers):
    """
    测试创建站点
    """
    site_data = {
        "name": "测试站点2",
        "code": "TEST002",
        "longitude": 121.5,
        "latitude": 31.2,
        "altitude": 10,
        "region": "上海",
        "description": "另一个测试站点"
    }

    response = client.post(
        "/api/v1/sites/",
        json=site_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["name"] == site_data["name"]
    assert data["data"]["code"] == site_data["code"]


def test_get_sites(client: TestClient, auth_headers, test_site):
    """
    测试获取站点列表
    """
    response = client.get(
        "/api/v1/sites/",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]["items"]) > 0


def test_get_site_detail(client: TestClient, auth_headers, test_site):
    """
    测试获取站点详情
    """
    response = client.get(
        f"/api/v1/sites/{test_site.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["id"] == test_site.id
    assert data["data"]["name"] == test_site.name


def test_update_site(client: TestClient, auth_headers, test_site):
    """
    测试更新站点
    """
    update_data = {
        "name": "更新后的站点",
        "description": "已更新"
    }

    response = client.put(
        f"/api/v1/sites/{test_site.id}",
        json=update_data,
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["name"] == update_data["name"]


def test_delete_site(client: TestClient, auth_headers, test_site):
    """
    测试删除站点
    """
    response = client.delete(
        f"/api/v1/sites/{test_site.id}",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200

    # 验证删除
    get_response = client.get(
        f"/api/v1/sites/{test_site.id}",
        headers=auth_headers
    )
    assert get_response.status_code == 404


def test_search_sites_by_name(client: TestClient, auth_headers, test_site):
    """
    测试按名称搜索站点
    """
    response = client.get(
        "/api/v1/sites/?name=测试",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]["items"]) > 0


def test_search_sites_by_region(client: TestClient, auth_headers, test_site):
    """
    测试按区域搜索站点
    """
    response = client.get(
        "/api/v1/sites/?region=北京",
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]["items"]) > 0
