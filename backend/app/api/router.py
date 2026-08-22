"""
GoldSight AI V3.0 - API v1 路由汇总

所有 v1 版本端点在此注册。
"""

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.data import router as data_router

# v1 主路由
api_v1_router = APIRouter(prefix="/api/v1")

# 注册各模块路由
api_v1_router.include_router(health_router, tags=["健康检查"])
api_v1_router.include_router(data_router, tags=["数据采集"])
