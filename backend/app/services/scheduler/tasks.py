"""
GoldSight AI V3.0 - 定时任务函数

定义 4 个每日定时任务：
1. 数据采集 — 调用所有 8 个采集器拉取最新数据
2. 技术指标计算 — 采集完成后重新计算 13 种指标
3. 市场分析 — 刷新跨市场关联 + 宏观面分析
4. AI 预测 — 生成当日 DeepSeek AI 预测

每个任务：
- 异步执行
- 幂等（重复执行不出错）
- 错误隔离（单个任务失败不影响后续任务）
- 记录执行时间、耗时、状态到 Redis
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict

from app.core.redis_client import get_redis, is_redis_available

logger = logging.getLogger(__name__)

# ── 任务执行记录 ──────────────────────────────────────────────


async def _record_task_result(
    task_name: str,
    status: str,
    elapsed: float,
    error: str | None = None,
) -> None:
    """
    将任务执行记录写入 Redis

    key 格式: scheduler:last_run:{task_name}
    值: JSON 字符串，包含执行时间、耗时、状态
    """
    if not is_redis_available():
        logger.warning(f"Redis 不可用，跳过记录任务 {task_name} 的执行结果")
        return

    redis = get_redis()
    if redis is None:
        return

    record = {
        "task_name": task_name,
        "executed_at": datetime.utcnow().isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "status": status,
    }
    if error:
        record["error"] = str(error)[:500]  # 截断过长的错误信息

    try:
        key = f"scheduler:last_run:{task_name}"
        await redis.set(key, json.dumps(record, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"写入任务执行记录失败 ({task_name}): {e}")


# ── 任务 1: 数据采集 ─────────────────────────────────────────


async def task_data_collection() -> Dict[str, Any]:
    """
    每日数据采集任务

    调用所有 8 个采集器拉取最新数据。
    """
    task_name = "data_collection"
    logger.info("⏰ [定时任务] 开始执行数据采集...")
    start = time.time()

    try:
        from app.services.data_collection import DataPipeline

        pipeline = DataPipeline(max_retries=3, retry_delay=2.0)
        results = await pipeline.run_all()

        # 统计结果
        total = len(results)
        success = sum(1 for r in results if r.get("status") == "success")
        failed = sum(1 for r in results if r.get("status") == "error")

        elapsed = time.time() - start
        status = "success" if failed == 0 else "partial"

        await _record_task_result(task_name, status, elapsed)

        logger.info(
            f"⏰ [定时任务] 数据采集完成: "
            f"总计={total}, 成功={success}, 失败={failed}, "
            f"耗时={elapsed:.1f}s"
        )

        return {
            "task": task_name,
            "status": status,
            "total": total,
            "success": success,
            "failed": failed,
            "elapsed": round(elapsed, 2),
        }

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"⏰ [定时任务] 数据采集失败: {e}")
        await _record_task_result(task_name, "failed", elapsed, str(e))
        return {
            "task": task_name,
            "status": "failed",
            "error": str(e),
            "elapsed": round(elapsed, 2),
        }


# ── 任务 2: 技术指标计算 ─────────────────────────────────────


async def task_technical_indicators() -> Dict[str, Any]:
    """
    每日技术指标计算任务

    采集完成后重新计算所有技术指标。
    """
    task_name = "technical_indicators"
    logger.info("⏰ [定时任务] 开始执行技术指标计算...")
    start = time.time()

    try:
        from app.services.technical_analysis.engine import run_calculation

        result = await run_calculation()

        elapsed = time.time() - start
        status = "success" if result.get("status") in ("success", "no_data") else "failed"

        await _record_task_result(task_name, status, elapsed)

        logger.info(
            f"⏰ [定时任务] 技术指标计算完成: "
            f"状态={result.get('status')}, "
            f"记录数={result.get('total_records', 0)}, "
            f"耗时={elapsed:.1f}s"
        )

        return {
            "task": task_name,
            "status": status,
            "result_summary": {
                "status": result.get("status"),
                "total_records": result.get("total_records", 0),
                "stored_records": result.get("stored_records", 0),
            },
            "elapsed": round(elapsed, 2),
        }

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"⏰ [定时任务] 技术指标计算失败: {e}")
        await _record_task_result(task_name, "failed", elapsed, str(e))
        return {
            "task": task_name,
            "status": "failed",
            "error": str(e),
            "elapsed": round(elapsed, 2),
        }


# ── 任务 3: 市场分析 ─────────────────────────────────────────


async def task_market_analysis() -> Dict[str, Any]:
    """
    每日市场分析任务

    刷新跨市场关联分析 + 宏观面分析。
    """
    task_name = "market_analysis"
    logger.info("⏰ [定时任务] 开始执行市场分析...")
    start = time.time()

    results = {}
    errors = []

    # 3a. 跨市场关联分析
    try:
        from app.services.analysis.market_engine import run_market_analysis

        market_result = await run_market_analysis()
        results["market_correlation"] = {
            "conclusion": market_result.get("conclusion"),
            "score": market_result.get("score"),
            "confidence": market_result.get("confidence"),
        }
    except Exception as e:
        logger.error(f"⏰ [定时任务] 跨市场分析失败: {e}")
        errors.append(f"market_correlation: {e}")

    # 3b. 宏观面分析
    try:
        from app.services.analysis.macro_engine import run_macro_analysis

        macro_result = await run_macro_analysis()
        results["macro"] = {
            "conclusion": macro_result.get("conclusion"),
            "score": macro_result.get("score"),
            "confidence": macro_result.get("confidence"),
        }
    except Exception as e:
        logger.error(f"⏰ [定时任务] 宏观面分析失败: {e}")
        errors.append(f"macro: {e}")

    elapsed = time.time() - start

    # 判断整体状态
    if not errors:
        status = "success"
    elif len(errors) < 2:
        status = "partial"
    else:
        status = "failed"

    error_msg = "; ".join(errors) if errors else None
    await _record_task_result(task_name, status, elapsed, error_msg)

    logger.info(
        f"⏰ [定时任务] 市场分析完成: 状态={status}, "
        f"耗时={elapsed:.1f}s"
    )

    return {
        "task": task_name,
        "status": status,
        "results": results,
        "errors": errors,
        "elapsed": round(elapsed, 2),
    }


# ── 任务 4: AI 预测 ──────────────────────────────────────────


async def task_ai_prediction() -> Dict[str, Any]:
    """
    每日 AI 预测任务

    生成当日 DeepSeek AI 预测。
    """
    task_name = "ai_prediction"
    logger.info("⏰ [定时任务] 开始执行 AI 预测...")
    start = time.time()

    try:
        from app.services.ai.prediction_engine import run_ai_prediction

        result = await run_ai_prediction()

        elapsed = time.time() - start
        is_fallback = result.get("is_fallback", False)
        status = "success" if not is_fallback else "fallback"

        await _record_task_result(task_name, status, elapsed)

        logger.info(
            f"⏰ [定时任务] AI 预测完成: "
            f"方向={result.get('direction')}, "
            f"置信度={result.get('confidence')}, "
            f"{'降级' if is_fallback else '正常'}, "
            f"耗时={elapsed:.1f}s"
        )

        return {
            "task": task_name,
            "status": status,
            "result_summary": {
                "direction": result.get("direction"),
                "confidence": result.get("confidence"),
                "target_price": result.get("target_price"),
                "is_fallback": is_fallback,
            },
            "elapsed": round(elapsed, 2),
        }

    except Exception as e:
        elapsed = time.time() - start
        logger.error(f"⏰ [定时任务] AI 预测失败: {e}")
        await _record_task_result(task_name, "failed", elapsed, str(e))
        return {
            "task": task_name,
            "status": "failed",
            "error": str(e),
            "elapsed": round(elapsed, 2),
        }
