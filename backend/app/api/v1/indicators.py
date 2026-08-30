"""
GoldSight AI V3.0 - 技术指标 API 端点

提供技术指标的触发计算和查询接口：
- POST /api/v1/indicators/calculate — 手动触发指标计算
- GET  /api/v1/indicators            — 查询已计算的指标
"""

from __future__ import annotations

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


# ── 触发指标计算 ──────────────────────────────────────────────


@router.post("/indicators/calculate")
async def trigger_calculation(
    symbol: str = Query("XAUUSD", description="交易符号"),
):
    """
    手动触发技术指标计算

    从 gold_prices 表读取价格数据，计算所有技术指标，
    结果写入 technical_indicators 表。
    """
    from app.services.technical_analysis.engine import run_calculation

    result = await run_calculation(symbol=symbol)
    return success(data=result)


# ── 查询技术指标 ──────────────────────────────────────────────


@router.get("/indicators")
async def get_indicators(
    symbol: Optional[str] = Query(None, description="交易符号"),
    indicator: Optional[str] = Query(None, description="指标名称"),
    category: Optional[str] = Query(
        None, description="指标类别: trend/momentum/volatility"
    ),
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(100, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: AsyncSession = Depends(get_db),
):
    """
    查询已计算的技术指标数据

    支持按交易符号、指标名称、类别、日期范围进行过滤。
    """
    conditions: list = []
    params: dict = {"limit": limit, "offset": offset}

    if symbol:
        conditions.append("symbol = :symbol")
        params["symbol"] = symbol
    if indicator:
        conditions.append("indicator_name = :indicator")
        params["indicator"] = indicator
    if category:
        conditions.append("category = :category")
        params["category"] = category
    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # 查询数据
    query_sql = text(
        f"SELECT id, timestamp, symbol, indicator_name, period, "
        f"category, value, extra_data, source, collected_at, quality_status "
        f"FROM technical_indicators {where_clause} "
        f"ORDER BY timestamp DESC, indicator_name, period "
        f"LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = list(result.keys())
    records = [dict(zip(columns, row)) for row in rows]

    # 查询总数
    count_sql = text(
        f"SELECT COUNT(*) FROM technical_indicators {where_clause}"
    )
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    # 类型转换
    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        if r.get("value") is not None:
            r["value"] = float(r["value"])
        # extra_data 已经是 dict（asyncpg 自动解析 JSONB）
        if hasattr(r.get("extra_data"), "__class__") and not isinstance(
            r.get("extra_data"), (dict, list)
        ):
            r["extra_data"] = {}

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })
