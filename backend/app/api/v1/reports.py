"""
GoldSight AI V3.0 - 每日报告生成接口

自动聚合实时数据、分析结果、AI 预测，生成结构化每日报告。
不调用 DeepSeek，纯数据聚合，Redis 缓存 24 小时。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.redis_client import get_redis, is_redis_available
from app.core.response import success, error
from app.api.v1.realtime import (
    _fetch_gold_price,
    _fetch_usd_index,
    _fetch_treasury_yield,
    _fetch_oil_price,
    _fetch_stock_index,
    _fetch_silver,
    _fetch_fed_funds_rate,
    _fetch_vix,
)

logger = logging.getLogger(__name__)

router = APIRouter()

REPORT_CACHE_TTL = 86400  # 24 小时
REPORT_CACHE_KEY = "daily_report:"


async def _get_cached_report(date_str: str) -> Optional[Dict[str, Any]]:
    """从 Redis 获取缓存的报告"""
    if not is_redis_available():
        return None
    try:
        r = get_redis()
        data = await r.get(f"{REPORT_CACHE_KEY}{date_str}")
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"报告缓存读取失败: {e}")
    return None


async def _set_cached_report(date_str: str, data: Dict[str, Any]) -> None:
    """缓存报告到 Redis"""
    if not is_redis_available():
        return
    try:
        r = get_redis()
        await r.setex(
            f"{REPORT_CACHE_KEY}{date_str}",
            REPORT_CACHE_TTL,
            json.dumps(data, ensure_ascii=False, default=str),
        )
    except Exception as e:
        logger.warning(f"报告缓存写入失败: {e}")


async def _get_latest_analysis(db: AsyncSession, analysis_type: str) -> Optional[Dict]:
    """获取最新分析结果"""
    sql = text(
        "SELECT analysis_type, generated_at, conclusion, confidence, score, factors "
        "FROM analysis_results "
        "WHERE analysis_type = :type "
        "ORDER BY generated_at DESC LIMIT 1"
    )
    result = await db.execute(sql, {"type": analysis_type})
    row = result.fetchone()
    if row:
        columns = list(result.keys())
        record = dict(zip(columns, row))
        # 解析 JSON 字段
        for key in ("factors",):
            val = record.get(key)
            if isinstance(val, str):
                try:
                    record[key] = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    record[key] = []
        for key in ("generated_at",):
            if isinstance(record.get(key), datetime):
                record[key] = record[key].isoformat()
        for key in ("confidence", "score"):
            if record.get(key) is not None:
                record[key] = float(record[key])
        return record
    return None


@router.get("/reports/daily")
async def generate_daily_report(
    date: Optional[str] = Query(None, description="报告日期 YYYY-MM-DD，默认今天"),
    db: AsyncSession = Depends(get_db),
):
    """
    生成每日市场报告

    聚合以下数据：
    - 实时行情：黄金/白银/美元/美债/原油/股指
    - 宏观指标：联邦基金利率/VIX
    - 分析结论：跨市场分析/宏观分析/AI 预测
    """
    import asyncio
    
    today = date or datetime.now().strftime("%Y-%m-%d")
    
    # 检查缓存
    cached = await _get_cached_report(today)
    if cached:
        return success(data={**cached, "_cached": True})

    try:
        # 并行获取所有实时数据
        gold, silver, usd, treasury, oil, stock, fed_rate, vix = await asyncio.gather(
            _fetch_gold_price(),
            _fetch_silver(),
            _fetch_usd_index(),
            _fetch_treasury_yield(),
            _fetch_oil_price(),
            _fetch_stock_index(),
            _fetch_fed_funds_rate(),
            _fetch_vix(),
        )

        # 获取分析结论
        market_analysis = await _get_latest_analysis(db, "market_correlation")
        macro_analysis = await _get_latest_analysis(db, "macro")
        ai_prediction = await _get_latest_analysis(db, "ai_prediction")

        # 构建报告
        report = {
            "date": today,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "market_snapshot": {
                "gold": {
                    "price": gold.get("price"),
                    "unit": "USD/oz",
                    "date": gold.get("date"),
                    "source": gold.get("source"),
                },
                "silver": {
                    "price": silver.get("price"),
                    "unit": "USD/oz",
                    "date": silver.get("date"),
                    "source": silver.get("source"),
                },
                "gold_silver_ratio": None,
                "usd_rates": usd.get("rates", {}),
                "treasury_10y": {
                    "value": treasury.get("value"),
                    "unit": "%",
                    "date": treasury.get("date"),
                },
                "wti_oil": {
                    "price": oil.get("price"),
                    "unit": "USD/barrel",
                    "date": oil.get("date"),
                },
                "sp500": {
                    "value": stock.get("value"),
                    "date": stock.get("date"),
                },
                "fed_rate": {
                    "value": fed_rate.get("value"),
                    "unit": "%",
                    "date": fed_rate.get("date"),
                },
                "vix": {
                    "value": vix.get("value"),
                    "date": vix.get("date"),
                },
            },
            "analysis_summary": {
                "market": {
                    "conclusion": market_analysis.get("conclusion") if market_analysis else None,
                    "score": market_analysis.get("score") if market_analysis else None,
                    "confidence": market_analysis.get("confidence") if market_analysis else None,
                },
                "macro": {
                    "conclusion": macro_analysis.get("conclusion") if macro_analysis else None,
                    "score": macro_analysis.get("score") if macro_analysis else None,
                    "confidence": macro_analysis.get("confidence") if macro_analysis else None,
                },
                "ai_prediction": {
                    "conclusion": ai_prediction.get("conclusion") if ai_prediction else None,
                    "score": ai_prediction.get("score") if ai_prediction else None,
                    "confidence": ai_prediction.get("confidence") if ai_prediction else None,
                },
            },
            "_cached": False,
        }

        # 计算金银比
        if gold.get("price") and silver.get("price") and silver["price"] > 0:
            report["market_snapshot"]["gold_silver_ratio"] = round(
                gold["price"] / silver["price"], 1
            )

        # 缓存报告
        await _set_cached_report(today, report)

        return success(data=report)

    except Exception as e:
        logger.error(f"每日报告生成失败: {e}")
        return error(message=f"每日报告生成失败: {e}")


@router.get("/reports/history")
async def get_report_history(
    limit: int = Query(7, ge=1, le=30, description="返回天数"),
    db: AsyncSession = Depends(get_db),
):
    """获取历史报告列表"""
    if not is_redis_available():
        return success(data={"reports": [], "message": "Redis 不可用"})
    
    try:
        r = get_redis()
        # 扫描最近的报告缓存
        reports = []
        from datetime import timedelta
        for i in range(limit):
            d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            data = await r.get(f"{REPORT_CACHE_KEY}{d}")
            if data:
                report = json.loads(data)
                reports.append({
                    "date": d,
                    "gold_price": report.get("market_snapshot", {}).get("gold", {}).get("price"),
                    "ai_conclusion": report.get("analysis_summary", {}).get("ai_prediction", {}).get("conclusion"),
                    "generated_at": report.get("generated_at"),
                })
        return success(data={"reports": reports, "total": len(reports)})
    except Exception as e:
        logger.error(f"历史报告查询失败: {e}")
        return error(message=f"历史报告查询失败: {e}")
