"""
GoldSight AI V3.0 - 数据采集 API 端点

提供已采集数据的查询接口和采集器管理接口：
- GET /api/v1/data/gold-prices     — 查询黄金价格数据
- GET /api/v1/data/usd             — 查询美元数据
- GET /api/v1/data/treasury-yields — 查询国债收益率
- GET /api/v1/data/oil             — 查询原油价格数据
- GET /api/v1/data/stock-market    — 查询美股/指数数据
- GET /api/v1/data/precious-metals — 查询贵金属数据
- GET /api/v1/data/economic        — 查询经济指标数据
- GET /api/v1/data/stats           — 各表数据统计概览
- GET /api/v1/data/collectors      — 列出已注册采集器
- POST /api/v1/data/collect/{name} — 手动触发采集
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.response import success

logger = logging.getLogger(__name__)

router = APIRouter()


# ── 黄金价格查询 ──────────────────────────────────────────────


@router.get("/data/gold-prices")
async def get_gold_prices(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的黄金价格数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    # 查询数据
    query_sql = text(
        f"SELECT id, timestamp, price_type, symbol, "
        f"open, high, low, close, change_value, change_pct, "
        f"volume, source, collected_at, quality_status "
        f"FROM gold_prices {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    # 查询总数
    count_sql = text(
        f"SELECT COUNT(*) FROM gold_prices {where_clause}"
    )
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    # 转换 datetime 为 ISO 字符串
    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        # Decimal 转 float
        for key in ("open", "high", "low", "close", "change_value", "change_pct"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 美元数据查询 ──────────────────────────────────────────────


@router.get("/data/usd")
async def get_usd_data(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    pair: Optional[str] = Query(None, description="货币对（如 DXY）"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的美元数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if pair:
        conditions.append("pair = :pair")
        params["pair"] = pair
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query_sql = text(
        f"SELECT id, timestamp, pair, "
        f"open, high, low, close, change_value, change_pct, "
        f"source, collected_at, quality_status "
        f"FROM usd_data {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    count_sql = text(f"SELECT COUNT(*) FROM usd_data {where_clause}")
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        for key in ("open", "high", "low", "close", "change_value", "change_pct"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 国债收益率查询 ────────────────────────────────────────────


@router.get("/data/treasury-yields")
async def get_treasury_yields(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    maturity: Optional[str] = Query(None, description="期限（如 10Y）"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的国债收益率数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if maturity:
        conditions.append("maturity = :maturity")
        params["maturity"] = maturity
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query_sql = text(
        f"SELECT id, timestamp, maturity, "
        f"yield, real_yield, spread_to_10y, "
        f"source, collected_at, quality_status "
        f"FROM treasury_yields {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    count_sql = text(
        f"SELECT COUNT(*) FROM treasury_yields {where_clause}"
    )
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        for key in ("yield", "real_yield", "spread_to_10y"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 原油数据查询 ──────────────────────────────────────────────


@router.get("/data/oil")
async def get_oil_data(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    oil_type: Optional[str] = Query(None, description="原油类型（如 wti）"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的原油价格数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if oil_type:
        conditions.append("oil_type = :oil_type")
        params["oil_type"] = oil_type
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query_sql = text(
        f"SELECT id, timestamp, oil_type, "
        f"open, high, low, close, change_value, change_pct, "
        f"source, collected_at, quality_status "
        f"FROM oil_data {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    count_sql = text(f"SELECT COUNT(*) FROM oil_data {where_clause}")
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        for key in ("open", "high", "low", "close", "change_value", "change_pct"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 美股/指数数据查询 ────────────────────────────────────────────


@router.get("/data/stock-market")
async def get_stock_market_data(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    index_symbol: Optional[str] = Query(None, description="指数符号（如 SPX, VIX）"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的美股/指数数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if index_symbol:
        conditions.append("index_symbol = :index_symbol")
        params["index_symbol"] = index_symbol
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query_sql = text(
        f"SELECT id, timestamp, index_symbol, "
        f"open, high, low, close, change_value, change_pct, "
        f"source, collected_at, quality_status "
        f"FROM stock_market {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    count_sql = text(f"SELECT COUNT(*) FROM stock_market {where_clause}")
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        for key in ("open", "high", "low", "close", "change_value", "change_pct"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 贵金属数据查询 ────────────────────────────────────────────


@router.get("/data/precious-metals")
async def get_precious_metals_data(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    metal: Optional[str] = Query(None, description="金属类型（如 silver）"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的贵金属数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if metal:
        conditions.append("metal = :metal")
        params["metal"] = metal
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query_sql = text(
        f"SELECT id, timestamp, metal, symbol, "
        f"open, high, low, close, change_value, change_pct, "
        f"source, collected_at, quality_status "
        f"FROM precious_metals {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    count_sql = text(f"SELECT COUNT(*) FROM precious_metals {where_clause}")
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        for key in ("open", "high", "low", "close", "change_value", "change_pct"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 经济指标数据查询 ────────────────────────────────────────────


@router.get("/data/economic")
async def get_economic_data(
    start_date: Optional[datetime] = Query(None, description="起始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    indicator_type: Optional[str] = Query(None, description="指标类型（如 cpi）"),
    limit: int = Query(50, ge=1, le=1000, description="返回条数"),
    offset: int = Query(0, ge=0, description="偏移量"),
    source: Optional[str] = Query(None, description="数据源过滤"),
    db: AsyncSession = Depends(get_db),
):
    """查询已采集的经济指标数据"""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if start_date:
        conditions.append("timestamp >= :start_date")
        params["start_date"] = start_date
    if end_date:
        conditions.append("timestamp <= :end_date")
        params["end_date"] = end_date
    if indicator_type:
        conditions.append("indicator_type = :indicator_type")
        params["indicator_type"] = indicator_type
    if source:
        conditions.append("source = :source")
        params["source"] = source

    where_clause = ""
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    query_sql = text(
        f"SELECT id, timestamp, indicator_type, period, "
        f"actual_value, revised_value, consensus, previous_value, unit, "
        f"source, collected_at, quality_status "
        f"FROM economic_indicators {where_clause} "
        f"ORDER BY timestamp DESC LIMIT :limit OFFSET :offset"
    )
    result = await db.execute(query_sql, params)
    rows = result.fetchall()
    columns = result.keys()
    records = [dict(zip(columns, row)) for row in rows]

    count_sql = text(f"SELECT COUNT(*) FROM economic_indicators {where_clause}")
    count_result = await db.execute(count_sql, params)
    total = count_result.scalar()

    for r in records:
        for key in ("timestamp", "collected_at"):
            if isinstance(r.get(key), datetime):
                r[key] = r[key].isoformat()
        for key in ("actual_value", "revised_value", "consensus", "previous_value"):
            if r.get(key) is not None:
                r[key] = float(r[key])

    return success(data={
        "records": records,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


# ── 数据统计概览 ──────────────────────────────────────────────


@router.get("/data/stats")
async def get_data_stats(
    db: AsyncSession = Depends(get_db),
):
    """获取各数据表的记录统计"""
    tables = [
        "gold_prices", "usd_data", "treasury_yields",
        "oil_data", "stock_market", "precious_metals",
        "economic_indicators", "technical_indicators",
    ]
    stats = {}
    for table in tables:
        try:
            sql = text(f"SELECT COUNT(*) FROM {table}")
            result = await db.execute(sql)
            count = result.scalar()
            stats[table] = count
        except Exception as e:
            stats[table] = f"error: {e}"

    return success(data={"table_counts": stats})


# ── 采集器管理 ────────────────────────────────────────────────


@router.get("/data/collectors")
async def list_collectors():
    """列出所有已注册的数据采集器"""
    from app.services.data_collection import CollectorRegistry

    registry = CollectorRegistry.get_instance()
    collectors = []
    for name in registry.list_names():
        collector = registry.get(name)
        if collector:
            collectors.append({
                "name": name,
                "source": collector.source_name,
                "target_table": collector.target_table,
            })
    return success(data={"collectors": collectors})


@router.post("/data/collect/{collector_name}")
async def trigger_collection(collector_name: str):
    """手动触发指定采集器执行数据采集"""
    from app.services.data_collection import DataPipeline

    pipeline = DataPipeline(max_retries=2, retry_delay=1.0)
    result = await pipeline.run(collector_name)
    return success(data=result)
