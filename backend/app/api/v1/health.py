"""
GoldSight AI V3.0 - 健康检查端点

GET /api/v1/health — 返回服务状态及依赖组件可用性。
"""

from fastapi import APIRouter

from app.core.response import success
from app.core.database import is_db_available
from app.core.redis_client import is_redis_available

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    健康检查接口
    返回服务状态、数据库和 Redis 连接状态。
    即使数据库或 Redis 不可用，服务仍返回 HTTP 200。
    """
    data = {
        "status": "ok",
        "service": "goldsight-backend",
        "components": {
            "database": "connected" if is_db_available() else "disconnected",
            "redis": "connected" if is_redis_available() else "disconnected",
        },
    }
    return success(data=data, message="服务运行正常")
