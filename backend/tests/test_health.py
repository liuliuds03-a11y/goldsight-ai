"""
GoldSight AI V3.0 - 健康检查 API 测试
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_health_endpoint():
    """测试健康检查端点返回正确格式"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "服务运行正常"
    assert data["data"]["status"] == "ok"
    assert data["data"]["service"] == "goldsight-backend"
    assert "database" in data["data"]["components"]
    assert "redis" in data["data"]["components"]


@pytest.mark.anyio
async def test_root_endpoint():
    """测试根路径返回服务信息"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "GoldSight AI V3.0"
    assert data["version"] == "3.0.0"


@pytest.mark.anyio
async def test_health_response_structure():
    """测试健康检查响应结构完整性"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    data = response.json()
    # 验证统一响应格式
    assert "code" in data
    assert "message" in data
    assert "data" in data
    # 验证业务数据结构
    assert "status" in data["data"]
    assert "service" in data["data"]
    assert "components" in data["data"]


@pytest.mark.anyio
async def test_nonexistent_route_returns_404():
    """测试不存在的路由返回 404"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/nonexistent")

    assert response.status_code == 404
