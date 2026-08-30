"""
GoldSight AI V3.0 - 调度器核心模块

使用 APScheduler AsyncIOScheduler 注册 4 个定时任务：
1. 数据采集 — 每天 02:00
2. 技术指标计算 — 每天 02:30
3. 市场分析 — 每天 03:00
4. AI 预测 — 每天 08:00

调度器随 FastAPI 应用生命周期启动/停止。
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.services.scheduler.tasks import (
    task_data_collection,
    task_technical_indicators,
    task_market_analysis,
    task_ai_prediction,
)

logger = logging.getLogger(__name__)

# ── 全局调度器实例 ────────────────────────────────────────────

_scheduler: Optional[AsyncIOScheduler] = None

# 任务定义：名称、执行函数、cron 表达式
TASK_DEFINITIONS = [
    {
        "id": "data_collection",
        "name": "数据采集",
        "func": task_data_collection,
        "trigger": CronTrigger(hour=2, minute=0),
        "description": "调用所有 8 个采集器拉取最新数据",
    },
    {
        "id": "technical_indicators",
        "name": "技术指标计算",
        "func": task_technical_indicators,
        "trigger": CronTrigger(hour=2, minute=30),
        "description": "采集完成后重新计算 13 种技术指标",
    },
    {
        "id": "market_analysis",
        "name": "市场分析",
        "func": task_market_analysis,
        "trigger": CronTrigger(hour=3, minute=0),
        "description": "刷新跨市场关联 + 宏观面分析",
    },
    {
        "id": "ai_prediction",
        "name": "AI 预测",
        "func": task_ai_prediction,
        "trigger": CronTrigger(hour=8, minute=0),
        "description": "生成当日 DeepSeek AI 预测",
    },
]


# ── 调度器管理 ────────────────────────────────────────────────


def create_scheduler() -> AsyncIOScheduler:
    """
    创建并配置 AsyncIOScheduler

    注册所有定时任务，但不启动。
    """
    global _scheduler

    scheduler = AsyncIOScheduler(
        timezone="Asia/Shanghai",
        job_defaults={
            "coalesce": True,       # 合并错过的执行
            "max_instances": 1,     # 同一任务最多 1 个实例
            "misfire_grace_time": 3600,  # 错过 1 小时内仍执行
        },
    )

    for task_def in TASK_DEFINITIONS:
        scheduler.add_job(
            func=task_def["func"],
            trigger=task_def["trigger"],
            id=task_def["id"],
            name=task_def["name"],
            replace_existing=True,
        )
        logger.info(
            f"📅 注册定时任务: {task_def['name']} — "
            f"{task_def['description']}"
        )

    _scheduler = scheduler
    return scheduler


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """获取全局调度器实例"""
    return _scheduler


async def start_scheduler() -> AsyncIOScheduler:
    """
    启动调度器

    在 FastAPI lifespan 的 startup 阶段调用。
    """
    global _scheduler

    if _scheduler is None:
        _scheduler = create_scheduler()

    if not _scheduler.running:
        _scheduler.start()
        logger.info("✅ 定时任务调度器已启动")
    else:
        logger.warning("调度器已在运行中，跳过启动")

    return _scheduler


async def stop_scheduler() -> None:
    """
    停止调度器

    在 FastAPI lifespan 的 shutdown 阶段调用。
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("🛑 定时任务调度器已停止")
    else:
        logger.info("调度器未运行或已停止，跳过")


# ── 状态查询 ──────────────────────────────────────────────────


async def get_scheduler_status() -> Dict[str, Any]:
    """
    获取调度器完整状态信息

    包含：
    - 调度器是否运行中
    - 每个任务的下次执行时间、上次执行时间
    - 每个任务的上次执行结果（从 Redis 读取）
    """
    import json
    from app.core.redis_client import get_redis, is_redis_available

    scheduler = get_scheduler()
    is_running = scheduler.running if scheduler else False

    tasks_status: List[Dict[str, Any]] = []

    for task_def in TASK_DEFINITIONS:
        task_id = task_def["id"]
        task_info: Dict[str, Any] = {
            "id": task_id,
            "name": task_def["name"],
            "description": task_def["description"],
            "next_run_time": None,
            "last_run": None,
        }

        # 从 APScheduler 获取下次执行时间
        if scheduler and is_running:
            try:
                job = scheduler.get_job(task_id)
                if job and job.next_run_time:
                    task_info["next_run_time"] = job.next_run_time.isoformat()
            except Exception:
                pass

        # 从 Redis 获取上次执行结果
        if is_redis_available():
            redis = get_redis()
            if redis:
                try:
                    key = f"scheduler:last_run:{task_id}"
                    raw = await redis.get(key)
                    if raw:
                        task_info["last_run"] = json.loads(raw)
                except Exception:
                    pass

        tasks_status.append(task_info)

    return {
        "scheduler_running": is_running,
        "timezone": "Asia/Shanghai",
        "tasks": tasks_status,
    }
