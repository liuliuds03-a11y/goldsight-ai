"""
GoldSight AI V3.0 - 新闻聚合 API 测试
"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.anyio
async def test_news_endpoint_default():
    """测试新闻端点默认参数"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/news/feed")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "data" in data
    news_data = data["data"]
    assert "articles" in news_data
    assert isinstance(news_data["articles"], list)


@pytest.mark.anyio
async def test_news_endpoint_with_category():
    """测试新闻分类筛选"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/news/feed?category=黄金")

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    news_data = data["data"]
    assert "articles" in news_data
    # 分类筛选后，文章数量应 <= 全部数量
    assert len(news_data["articles"]) <= 50


@pytest.mark.anyio
async def test_news_endpoint_with_limit():
    """测试新闻数量限制"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/news/feed?limit=5")

    assert response.status_code == 200
    data = response.json()
    news_data = data["data"]
    # 限制为 5 条
    assert len(news_data["articles"]) <= 5


@pytest.mark.anyio
async def test_news_response_structure():
    """测试新闻响应结构"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/news/feed")

    data = response.json()
    news_data = data["data"]
    # 验证必要字段
    assert "articles" in news_data
    assert "total" in news_data
    # 如果有文章，验证文章结构
    if news_data["articles"]:
        article = news_data["articles"][0]
        assert "title" in article
        assert "source" in article
        assert "link" in article
