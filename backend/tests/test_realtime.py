"""
GoldSight AI V3.0 - 实时数据 API 测试
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_realtime_all_endpoint():
    """测试实时数据聚合端点返回正确格式"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/realtime/all")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    # 实时数据应包含多个资产类别
    result = data["data"]
    assert isinstance(result, dict)


@pytest.mark.anyio
async def test_realtime_refresh_endpoint():
    """测试缓存刷新端点"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/realtime/refresh")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["code"] == 200


@pytest.mark.anyio
async def test_realtime_response_structure():
    """测试实时数据响应结构"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/realtime/all")

    data = response.json()
    # 验证统一响应格式
    assert "code" in data
    assert "message" in data
    assert "data" in data
