"""
GoldSight AI V3.0 - AI 预测 API 端点

提供 AI 智能预测相关接口：
- POST /api/v1/predict/gold    — 触发 AI 黄金价格预测
- GET  /api/v1/predict/gold    — 查询最近的 AI 预测结果
- POST /api/v1/predict/summary — AI 综合摘要（一句话总结当前行情）
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success, error

logger = logging.getLogger(__name__)

router = APIRouter()


# ── 辅助函数 ──────────────────────────────────────────────────


def _parse_prediction_record(record: dict) -> dict:
    """解析数据库返回的预测记录"""
    for key in ("factors", "data_range", "metadata"):
        val = record.get(key)
        if isinstance(val, str):
            try:
                record[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                record[key] = {} if key != "factors" else []
        elif val is None:
            record[key] = {} if key != "factors" else []

    for key in ("generated_at", "collected_at"):
        if isinstance(record.get(key), datetime):
            record[key] = record[key].isoformat()

    for key in ("confidence", "score"):
        if record.get(key) is not None:
            record[key] = float(record[key])

    return record


async def _fetch_latest_predictions(
    db: AsyncSession,
    limit: int = 1,
) -> list:
    """从数据库获取最新的 AI 预测记录"""
    sql = text(
        "SELECT id, analysis_type, generated_at, conclusion, confidence, "
        "score, factors, data_range, source, metadata, collected_at "
        "FROM analysis_results "
        "WHERE analysis_type = 'ai_prediction' "
        "ORDER BY generated_at DESC "
        "LIMIT :limit"
    )
    result = await db.execute(sql, {"limit": limit})
    rows = result.fetchall()
    columns = list(result.keys())
    records = [dict(zip(columns, row)) for row in rows]
    return [_parse_prediction_record(r) for r in records]


# ── POST /predict/gold — 触发 AI 黄金价格预测 ─────────────────


@router.post("/predict/gold")
async def trigger_gold_prediction():
    """
    触发 AI 黄金价格预测

    从数据库读取技术指标、市场分析、宏观分析数据，
    调用 DeepSeek 大模型进行综合分析，输出预测结论。
    """
    from app.services.ai.prediction_engine import run_ai_prediction

    try:
        result = await run_ai_prediction()
        return success(data=result)
    except Exception as e:
        logger.error(f"AI 预测执行失败: {e}")
        return error(message=f"AI 预测执行失败: {e}")


# ── GET /predict/gold — 查询最近的 AI 预测结果 ────────────────


@router.get("/predict/gold")
async def get_gold_predictions(
    limit: int = Query(1, ge=1, le=50, description="返回条数"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询最近的 AI 预测结果

    返回已存储的 AI 预测记录，按时间倒序排列。
    """
    records = await _fetch_latest_predictions(db, limit)

    if not records:
        return success(data={
            "records": [],
            "total": 0,
            "message": "暂无 AI 预测结果，请先触发预测（POST /predict/gold）",
        })

    return success(data={
        "records": records,
        "total": len(records),
    })


# ── POST /predict/summary — AI 综合摘要 ───────────────────────


@router.post("/predict/summary")
async def trigger_ai_summary():
    """
    AI 综合摘要 — 一句话总结当前行情

    基于最新的市场数据和历史分析结果，
    调用 DeepSeek 生成简洁的行情摘要。
    """
    from app.services.ai.prediction_engine import run_ai_summary

    try:
        result = await run_ai_summary()
        return success(data=result)
    except Exception as e:
        logger.error(f"AI 摘要生成失败: {e}")
        return error(message=f"AI 摘要生成失败: {e}")
