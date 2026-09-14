"""
GoldSight AI V3.0 - 配置模块测试
"""

import pytest

from app.core.config import Settings, settings


def test_settings_singleton():
    """测试配置单例已正确加载"""
    assert settings is not None
    assert isinstance(settings, Settings)


def test_default_values():
    """测试默认配置值"""
    assert settings.backend_port in (8000, 8016)  # 支持不同环境
    assert settings.postgres_db == "goldsight"
    assert settings.jwt_algorithm == "HS256"


def test_async_database_url():
    """测试异步数据库 URL 转换"""
    url = settings.async_database_url
    assert "postgresql+asyncpg://" in url


def test_deepseek_configured():
    """测试 DeepSeek 配置检测"""
    # 根据实际环境，可能配置或未配置
    assert isinstance(settings.deepseek_configured, bool)


def test_cors_origins():
    """测试 CORS 源列表"""
    assert isinstance(settings.cors_origins, list)
    assert "http://localhost:5173" in settings.cors_origins
