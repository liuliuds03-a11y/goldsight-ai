"""
GoldSight AI V3.0 - 数据库连接模块

使用 SQLAlchemy 2.0 异步引擎连接 PostgreSQL。
当 Docker/PostgreSQL 不可用时优雅降级，不阻塞应用启动。
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── 异步引擎与会话工厂 ────────────────────────────────────────

engine = create_async_engine(
    settings.async_database_url,
    echo=settings.app_debug,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 数据库可用性状态
_db_available: Optional[bool] = None


async def check_database_connection() -> bool:
    """检查数据库连接是否可用"""
    global _db_available
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        _db_available = True
        logger.info("数据库连接正常")
        return True
    except Exception as e:
        _db_available = False
        logger.warning(f"数据库连接不可用: {e}")
        return False


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 的 Depends()
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    数据库会话上下文管理器
    用于非 API 层（如 service 层）手动获取会话
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_database() -> bool:
    """
    初始化数据库连接（应用启动时调用）
    连接失败时优雅降级，不阻塞启动
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        _db_available = True
        logger.info("✅ PostgreSQL 数据库连接成功")
        return True
    except Exception as e:
        _db_available = False
        logger.warning(
            f"⚠️ PostgreSQL 数据库连接失败，应用将在无数据库模式下运行: {e}"
        )
        return False


async def close_database() -> None:
    """关闭数据库引擎"""
    await engine.dispose()
    logger.info("PostgreSQL 数据库连接已关闭")


def is_db_available() -> bool:
    """同步方法：返回数据库当前是否可用"""
    return _db_available is True
