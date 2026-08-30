"""
GoldSight AI V3.0 - FastAPI 应用入口

创建 FastAPI 实例，注册中间件、路由、异常处理器。
管理应用生命周期（启动/关闭时的资源初始化与释放）。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_database, close_database
from app.core.redis_client import init_redis, close_redis
from app.core.exceptions import register_exception_handlers
from app.api.router import api_v1_router
from app.services.scheduler.scheduler import start_scheduler, stop_scheduler

# ── 日志配置 ──────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.backend_log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── 应用生命周期管理 ──────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期：启动时初始化资源，关闭时释放资源。
    数据库和 Redis 连接失败时优雅降级，不阻塞启动。
    """
    logger.info("🚀 GoldSight AI V3.0 后端服务启动中...")
    logger.info(f"   环境: {settings.app_env}")
    logger.info(f"   调试模式: {settings.app_debug}")

    # 初始化数据库连接（失败不阻塞）
    await init_database()

    # 初始化 Redis 连接（失败不阻塞）
    await init_redis()

    # DeepSeek 状态
    if settings.deepseek_configured:
        logger.info("✅ DeepSeek API 已配置")
    else:
        logger.warning("⚠️ DeepSeek API Key 未配置，AI 分析功能暂不可用")

    logger.info("✅ GoldSight AI V3.0 后端服务启动完成")

    # 启动定时任务调度器
    await start_scheduler()

    yield  # ── 应用运行中 ──

    # 停止调度器
    await stop_scheduler()

    # 关闭资源
    logger.info("🛑 GoldSight AI V3.0 后端服务关闭中...")
    await close_redis()
    await close_database()
    logger.info("🛑 GoldSight AI V3.0 后端服务已关闭")


# ── 创建 FastAPI 应用 ────────────────────────────────────────

app = FastAPI(
    title="GoldSight AI V3.0",
    description="全球多金属智能监测、分析与预测平台 API",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS 中间件 ───────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册异常处理器 ────────────────────────────────────────────

register_exception_handlers(app)

# ── 注册路由 ──────────────────────────────────────────────────

app.include_router(api_v1_router)


# ── 根路径 ────────────────────────────────────────────────────


@app.get("/", tags=["根路径"])
async def root():
    """根路径 - 服务基本信息"""
    return {
        "name": "GoldSight AI V3.0",
        "description": "全球多金属智能监测、分析与预测平台",
        "version": "3.0.0",
        "docs": "/docs",
    }
