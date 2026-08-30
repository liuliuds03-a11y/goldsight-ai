"""
GoldSight AI V3.0 - 调度器状态 API

提供调度器状态查询和手动触发接口。
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter

from app.core.response import success, error
from app.services.scheduler.scheduler import (
    get_scheduler_status,
    get_scheduler,
)
from app.services.scheduler.tasks import (
    task_data_collection,
    task_technical_indicators,
    task_market_analysis,
    task_ai_prediction,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler")

# 任务函数映射
_TASK_FUNCTIONS = {
    "data_collection": task_data_collection,
    "technical_indicators": task_technical_indicators,
    "market_analysis": task_market_analysis,
    "ai_prediction": task_ai_prediction,
}


@router.get("/status", summary="查看调度器状态")
async def scheduler_status() -> Dict[str, Any]:
    """
    查看调度器状态

    返回：
    - 调度器是否运行中
    - 4 个定时任务的下次执行时间
    - 每个任务的上次执行结果
    """
    status = await get_scheduler_status()
    return success(data=status, message="调度器状态查询成功")


@router.post("/trigger/{task_name}", summary="手动触发指定任务")
async def trigger_task(task_name: str) -> Dict[str, Any]:
    """
    手动触发指定定时任务

    支持的任务：data_collection, technical_indicators, market_analysis, ai_prediction
    """
    task_func = _TASK_FUNCTIONS.get(task_name)
    if not task_func:
        return error(
            message=f"未知任务: {task_name}，"
                    f"可选: {', '.join(_TASK_FUNCTIONS.keys())}"
        )

    logger.info(f"手动触发任务: {task_name}")
    result = await task_func()

    return success(data=result, message=f"任务 {task_name} 执行完成")
