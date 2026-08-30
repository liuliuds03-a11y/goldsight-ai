"""
GoldSight AI V3.0 - 技术指标计算引擎

编排技术指标的完整计算流程：
1. 从 gold_prices 表获取价格数据
2. 对每个时间点计算所有可计算的技术指标
3. 将结果写入 technical_indicators 表

支持数据不足时的优雅降级。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from . import calculations

logger = logging.getLogger(__name__)

# ── 指标配置 ──────────────────────────────────────────────────
# 每个指标定义：名称、类别、最小数据量、计算函数

INDICATOR_CONFIG: List[Dict[str, Any]] = [
    # ── 趋势类 ──
    {
        "name": "sma", "category": "trend",
        "min_data": 5, "func": calculations.calculate_ma,
        "params": {"period": 5}, "period": 5,
    },
    {
        "name": "sma", "category": "trend",
        "min_data": 10, "func": calculations.calculate_ma,
        "params": {"period": 10}, "period": 10,
    },
    {
        "name": "sma", "category": "trend",
        "min_data": 20, "func": calculations.calculate_ma,
        "params": {"period": 20}, "period": 20,
    },
    {
        "name": "sma", "category": "trend",
        "min_data": 60, "func": calculations.calculate_ma,
        "params": {"period": 60}, "period": 60,
    },
    {
        "name": "ema", "category": "trend",
        "min_data": 12, "func": calculations.calculate_ema,
        "params": {"period": 12}, "period": 12,
    },
    {
        "name": "ema", "category": "trend",
        "min_data": 26, "func": calculations.calculate_ema,
        "params": {"period": 26}, "period": 26,
    },
    {
        "name": "macd", "category": "trend",
        "min_data": 26, "func": calculations.calculate_macd,
        "params": {}, "period": 12, "component": "macd",
    },
    {
        "name": "macd_signal", "category": "trend",
        "min_data": 26, "func": calculations.calculate_macd,
        "params": {}, "period": 26, "component": "signal",
    },
    {
        "name": "macd_hist", "category": "trend",
        "min_data": 26, "func": calculations.calculate_macd,
        "params": {}, "period": 9, "component": "hist",
    },
    {
        "name": "adx", "category": "trend",
        "min_data": 30, "func": calculations.calculate_adx,
        "params": {"period": 14}, "period": 14,
    },
    # ── 动量类 ──
    {
        "name": "rsi", "category": "momentum",
        "min_data": 15, "func": calculations.calculate_rsi,
        "params": {"period": 14}, "period": 14,
    },
    {
        "name": "stochastic_k", "category": "momentum",
        "min_data": 16, "func": calculations.calculate_stochastic,
        "params": {"period": 14}, "period": 14, "component": "k",
    },
    {
        "name": "stochastic_d", "category": "momentum",
        "min_data": 16, "func": calculations.calculate_stochastic,
        "params": {"period": 14}, "period": 14, "component": "d",
    },
    {
        "name": "roc", "category": "momentum",
        "min_data": 15, "func": calculations.calculate_roc,
        "params": {"period": 14}, "period": 14,
    },
    # ── 波动类 ──
    {
        "name": "bollinger_upper", "category": "volatility",
        "min_data": 20, "func": calculations.calculate_bollinger_bands,
        "params": {"period": 20, "std_dev": 2.0}, "period": 20,
        "component": "upper",
    },
    {
        "name": "bollinger_mid", "category": "volatility",
        "min_data": 20, "func": calculations.calculate_bollinger_bands,
        "params": {"period": 20, "std_dev": 2.0}, "period": 20,
        "component": "middle",
    },
    {
        "name": "bollinger_lower", "category": "volatility",
        "min_data": 20, "func": calculations.calculate_bollinger_bands,
        "params": {"period": 20, "std_dev": 2.0}, "period": 20,
        "component": "lower",
    },
    {
        "name": "atr", "category": "volatility",
        "min_data": 15, "func": calculations.calculate_atr,
        "params": {"period": 14}, "period": 14,
    },
]


# ── 数据获取 ──────────────────────────────────────────────────


async def fetch_price_data(
    symbol: str = "XAUUSD",
    limit: int = 500,
) -> List[Dict[str, Any]]:
    """
    从 gold_prices 表获取价格数据

    Args:
        symbol: 交易符号，默认 XAUUSD
        limit: 最大返回条数

    Returns:
        按时间升序排列的价格字典列表
        每条包含: timestamp, open, high, low, close
    """
    async with get_db_context() as session:
        sql = text(
            "SELECT timestamp, open, high, low, close "
            "FROM gold_prices "
            "WHERE symbol = :symbol AND quality_status IN ('valid', 'pending') "
            "ORDER BY timestamp ASC "
            "LIMIT :limit"
        )
        result = await session.execute(sql, {
            "symbol": symbol,
            "limit": limit,
        })
        rows = result.fetchall()
        columns = list(result.keys())

        data: List[Dict[str, Any]] = []
        for row in rows:
            record = dict(zip(columns, row))
            # Decimal → float
            for key in ("open", "high", "low", "close"):
                if record.get(key) is not None:
                    record[key] = float(record[key])
            data.append(record)

    return data


# ── 指标计算 ──────────────────────────────────────────────────


def compute_all_indicators(
    price_data: List[Dict[str, Any]],
    index: int,
) -> List[Dict[str, Any]]:
    """
    对某个时间点计算所有可计算的技术指标

    使用 price_data[0:index+1] 作为历史数据窗口，
    数据量不足的指标自动跳过。

    Args:
        price_data: 全部价格数据（按时间升序）
        index: 当前计算的时间点索引

    Returns:
        指标记录列表，每条包含 timestamp 及指标信息
    """
    records: List[Dict[str, Any]] = []
    current = price_data[index]
    timestamp = current["timestamp"]

    # 构造历史数据窗口
    window = price_data[: index + 1]
    closes = np.array([p["close"] for p in window])
    highs = np.array([p["high"] for p in window])
    lows = np.array([p["low"] for p in window])

    for config in INDICATOR_CONFIG:
        min_data = config["min_data"]
        if len(window) < min_data:
            continue

        try:
            # 根据指标类型传入不同参数
            if config["func"] in (
                calculations.calculate_adx,
                calculations.calculate_stochastic,
                calculations.calculate_atr,
            ):
                result = config["func"](
                    highs, lows, closes, **config["params"]
                )
            else:
                result = config["func"](closes, **config["params"])

            if result is None:
                continue

            # 处理复合指标（MACD、Stochastic、Bollinger）
            component = config.get("component")
            if isinstance(result, dict) and component:
                value = result.get(component)
                if value is None:
                    continue
                extra = {
                    k: v for k, v in result.items() if k != component
                }
                records.append({
                    "timestamp": timestamp,
                    "symbol": "XAUUSD",
                    "indicator_name": config["name"],
                    "period": config["period"],
                    "category": config["category"],
                    "value": round(float(value), 6),
                    "extra_data": extra if extra else {},
                })
            elif isinstance(result, dict):
                # 字典结果但无指定分量 → 存储全部
                records.append({
                    "timestamp": timestamp,
                    "symbol": "XAUUSD",
                    "indicator_name": config["name"],
                    "period": config["period"],
                    "category": config["category"],
                    "value": round(float(list(result.values())[0]), 6),
                    "extra_data": result,
                })
            else:
                # 单值指标
                records.append({
                    "timestamp": timestamp,
                    "symbol": "XAUUSD",
                    "indicator_name": config["name"],
                    "period": config["period"],
                    "category": config["category"],
                    "value": round(float(result), 6),
                    "extra_data": {},
                })

        except Exception as e:
            logger.warning(
                f"计算 {config['name']}(period={config['period']}) "
                f"在 index={index} 时失败: {e}"
            )

    return records


# ── 数据存储 ──────────────────────────────────────────────────


async def store_indicators(
    records: List[Dict[str, Any]],
) -> int:
    """
    将指标记录写入 technical_indicators 表

    使用 ON CONFLICT DO UPDATE 实现幂等写入（支持增量更新）。

    Args:
        records: 指标记录列表

    Returns:
        成功写入的记录数量
    """
    if not records:
        return 0

    async with get_db_context() as session:
        sql = text(
            "INSERT INTO technical_indicators "
            "(timestamp, symbol, indicator_name, period, category, "
            "value, extra_data, source, quality_status) "
            "VALUES (:timestamp, :symbol, :indicator_name, :period, "
            ":category, :value, :extra_data, 'technical_engine', 'valid') "
            "ON CONFLICT (timestamp, symbol, indicator_name, period, source) "
            "DO UPDATE SET "
            "value = EXCLUDED.value, "
            "extra_data = EXCLUDED.extra_data, "
            "updated_at = NOW()"
        )

        inserted = 0
        for record in records:
            values = dict(record)
            # extra_data 需要序列化为 JSON 字符串
            values["extra_data"] = json.dumps(values.get("extra_data", {}))

            try:
                result = await session.execute(sql, values)
                if result.rowcount > 0:
                    inserted += 1
            except Exception as e:
                logger.warning(f"写入指标记录失败: {e}")

    return inserted


# ── 主入口 ────────────────────────────────────────────────────


async def run_calculation(
    symbol: str = "XAUUSD",
) -> Dict[str, Any]:
    """
    执行完整的技术指标计算流程

    1. 获取价格数据
    2. 对每个时间点计算所有可计算指标
    3. 批量写入数据库

    Args:
        symbol: 交易符号

    Returns:
        计算结果摘要
    """
    logger.info(f"开始计算技术指标: {symbol}")

    # 1. 获取价格数据
    price_data = await fetch_price_data(symbol)
    total_points = len(price_data)

    if total_points == 0:
        return {
            "status": "no_data",
            "message": f"未找到 {symbol} 的价格数据",
            "indicators_calculated": [],
            "total_records": 0,
        }

    logger.info(f"获取到 {total_points} 条价格数据")

    # 2. 对每个时间点计算指标
    all_records: List[Dict[str, Any]] = []
    for i in range(total_points):
        records = compute_all_indicators(price_data, i)
        all_records.extend(records)

    # 3. 写入数据库
    stored = await store_indicators(all_records)

    # 统计各指标计算情况
    indicator_summary: Dict[str, int] = {}
    for r in all_records:
        name = r["indicator_name"]
        period = r["period"]
        key = f"{name}({period})"
        indicator_summary[key] = indicator_summary.get(key, 0) + 1

    logger.info(
        f"技术指标计算完成: 共 {len(all_records)} 条记录，"
        f"成功写入 {stored} 条"
    )

    return {
        "status": "success",
        "symbol": symbol,
        "price_data_points": total_points,
        "total_records": len(all_records),
        "stored_records": stored,
        "indicators_summary": indicator_summary,
    }
