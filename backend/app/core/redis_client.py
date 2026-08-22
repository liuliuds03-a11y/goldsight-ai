"""
GoldSight AI V3.0 - Redis 连接模块

使用 redis.asyncio 异步客户端连接 Redis。
当 Redis 不可用时优雅降级，不阻塞应用启动。
"""

import logging
from typing import Optional

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Redis 客户端实例 ──────────────────────────────────────────

redis_client: Optional[aioredis.Redis] = None
_redis_available: bool = False


async def init_redis() -> bool:
    """
    初始化 Redis 连接（应用启动时调用）
    连接失败时优雅降级，不阻塞启动
    """
    global redis_client, _redis_available
    try:
        redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        # 验证连接
        await redis_client.ping()
        _redis_available = True
        logger.info("✅ Redis 连接成功")
        return True
    except Exception as e:
        redis_client = None
        _redis_available = False
        logger.warning(
            f"⚠️ Redis 连接失败，应用将在无缓存模式下运行: {e}"
        )
        return False


async def close_redis() -> None:
    """关闭 Redis 连接"""
    global redis_client, _redis_available
    if redis_client:
        await redis_client.close()
        redis_client = None
    _redis_available = False
    logger.info("Redis 连接已关闭")


async def check_redis_connection() -> bool:
    """检查 Redis 连接是否可用"""
    global _redis_available
    if redis_client is None:
        _redis_available = False
        return False
    try:
        await redis_client.ping()
        _redis_available = True
        return True
    except Exception:
        _redis_available = False
        return False


def is_redis_available() -> bool:
    """同步方法：返回 Redis 当前是否可用"""
    return _redis_available and redis_client is not None


def get_redis() -> Optional[aioredis.Redis]:
    """获取 Redis 客户端实例（可能为 None）"""
    return redis_client
