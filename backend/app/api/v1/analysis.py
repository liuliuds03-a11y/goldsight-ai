"""
GoldSight AI V3.0 - 市场分析 API 端点

提供跨市场关联分析和宏观面分析的触发与查询接口：
- POST /api/v1/analysis/market  — 触发跨市场分析
- POST /api/v1/analysis/macro   — 触发宏观分析
- GET  /api/v1/analysis/market  — 查询最近的市场分析结果
- GET  /api/v1/analysis/macro   — 查询最近的宏观分析结果
- GET  /api/v1/analysis/summary — 综合摘要（市场+宏观合并）
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


def _parse_analysis_record(record: dict) -> dict:
    """解析数据库返回的分析记录"""
    # JSONB 字段可能已经是 dict/list（asyncpg 自动解析）
    for key in ("factors", "data_range", "metadata"):
        val = record.get(key)
        if isinstance(val, str):
            try:
                record[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                record[key] = {} if key != "factors" else []
        elif val is None:
            record[key] = {} if key != "factors" else []

    # datetime 转 ISO
    for key in ("generated_at", "collected_at", "timestamp"):
        if isinstance(record.get(key), datetime):
            record[key] = record[key].isoformat()

    # Decimal 转 float
    for key in ("confidence", "score"):
        if record.get(key) is not None:
            record[key] = float(record[key])

    return record


async def _fetch_latest_analysis(
    db: AsyncSession,
    analysis_type: str,
    limit: int = 1,
) -> list:
    """从数据库获取最新的分析记录"""
    sql = text(
        "SELECT id, analysis_type, generated_at, conclusion, confidence, "
        "score, factors, data_range, source, metadata, collected_at "
        "FROM analysis_results "
        "WHERE analysis_type = :analysis_type "
        "ORDER BY generated_at DESC "
        "LIMIT :limit"
    )
    result = await db.execute(sql, {
        "analysis_type": analysis_type,
        "limit": limit,
    })
    rows = result.fetchall()
    columns = list(result.keys())
    records = [dict(zip(columns, row)) for row in rows]
    return [_parse_analysis_record(r) for r in records]


# ── POST /analysis/market — 触发跨市场分析 ────────────────────


@router.post("/analysis/market")
async def trigger_market_analysis():
    """
    触发跨市场关联分析

    从数据库读取黄金、美元、美债、原油、美股、VIX 数据，
    计算各市场因素与黄金的关联关系，输出结构化分析结论。
    """
    from app.services.analysis.market_engine import run_market_analysis

    try:
        result = await run_market_analysis()
        return success(data=result)
    except Exception as e:
        logger.error(f"跨市场分析执行失败: {e}")
        return error(message=f"跨市场分析执行失败: {e}")


# ── POST /analysis/macro — 触发宏观分析 ───────────────────────


@router.post("/analysis/macro")
async def trigger_macro_analysis():
    """
    触发宏观面分析

    从数据库读取 CPI、美债收益率、美元数据，
    分析通胀、利率、美元因素对黄金的综合影响。
    """
    from app.services.analysis.macro_engine import run_macro_analysis

    try:
        result = await run_macro_analysis()
        return success(data=result)
    except Exception as e:
        logger.error(f"宏观分析执行失败: {e}")
        return error(message=f"宏观分析执行失败: {e}")


# ── GET /analysis/market — 查询最近的市场分析结果 ─────────────


@router.get("/analysis/market")
async def get_market_analysis(
    limit: int = Query(1, ge=1, le=50, description="返回条数"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询最近的跨市场关联分析结果

    返回已存储的分析记录，按时间倒序排列。
    """
    records = await _fetch_latest_analysis(db, "market_correlation", limit)

    if not records:
        return success(data={
            "records": [],
            "total": 0,
            "message": "暂无市场分析结果，请先触发分析（POST /analysis/market）",
        })

    return success(data={
        "records": records,
        "total": len(records),
    })


# ── GET /analysis/macro — 查询最近的宏观分析结果 ─────────────


@router.get("/analysis/macro")
async def get_macro_analysis(
    limit: int = Query(1, ge=1, le=50, description="返回条数"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询最近的宏观面分析结果

    返回已存储的分析记录，按时间倒序排列。
    """
    records = await _fetch_latest_analysis(db, "macro", limit)

    if not records:
        return success(data={
            "records": [],
            "total": 0,
            "message": "暂无宏观分析结果，请先触发分析（POST /analysis/macro）",
        })

    return success(data={
        "records": records,
        "total": len(records),
    })


# ── GET /analysis/summary — 综合摘要 ─────────────────────────


@router.get("/analysis/summary")
async def get_analysis_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    综合摘要 — 合并市场分析与宏观分析的最新结果

    返回两部分分析的综合结论，给出统一的评分和判断。
    """
    # 获取最新的市场分析和宏观分析
    market_records = await _fetch_latest_analysis(db, "market_correlation", 1)
    macro_records = await _fetch_latest_analysis(db, "macro", 1)

    market_analysis = market_records[0] if market_records else None
    macro_analysis = macro_records[0] if macro_records else None

    # 综合评分（市场分析权重 50%，宏观分析权重 50%）
    scores = []
    if market_analysis:
        scores.append(market_analysis["score"] * 0.5)
    if macro_analysis:
        scores.append(macro_analysis["score"] * 0.5)

    overall_score = int(round(sum(scores))) if scores else 0
    overall_score = max(-100, min(100, overall_score))

    # 综合结论
    if overall_score > 15:
        overall_conclusion = "利多"
    elif overall_score < -15:
        overall_conclusion = "利空"
    else:
        overall_conclusion = "中性"

    # 综合置信度
    confidences = []
    if market_analysis:
        confidences.append(market_analysis["confidence"])
    if macro_analysis:
        confidences.append(macro_analysis["confidence"])
    overall_confidence = round(
        sum(confidences) / len(confidences), 2
    ) if confidences else 0.0

    return success(data={
        "timestamp": datetime.utcnow().isoformat(),
        "market_analysis": market_analysis,
        "macro_analysis": macro_analysis,
        "overall_conclusion": overall_conclusion,
        "overall_score": overall_score,
        "overall_confidence": overall_confidence,
    })
