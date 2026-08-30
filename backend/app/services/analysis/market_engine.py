"""
GoldSight AI V3.0 - 跨市场关联分析引擎

计算黄金与各市场因素的关联关系：
1. 黄金 vs 美元（DXY）
2. 黄金 vs 美债实际利率
3. 黄金 vs 原油
4. 黄金 vs 美股（S&P 500）
5. 黄金 vs VIX 恐慌指数

最终输出结构化分析结论，存入 analysis_results 表。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context

logger = logging.getLogger(__name__)

# ── 数据获取工具 ──────────────────────────────────────────────


async def _fetch_daily_series(
    sql: str,
    params: dict,
) -> Dict[date, float]:
    """
    执行 SQL 查询，返回 {date: close_price} 字典。
    按日期升序排列。
    """
    async with get_db_context() as session:
        result = await session.execute(text(sql), params)
        rows = result.fetchall()
        columns = list(result.keys())

    series: Dict[date, float] = {}
    for row in rows:
        record = dict(zip(columns, row))
        ts = record["timestamp"]
        close_val = record.get("close") or record.get("yield")
        if ts is not None and close_val is not None:
            d = ts.date() if hasattr(ts, "date") else ts
            series[d] = float(close_val)
    return series


async def _fetch_all_market_data() -> Dict[str, Dict[date, float]]:
    """获取所有市场数据序列，返回 {series_name: {date: close}}"""
    data: Dict[str, Dict[date, float]] = {}

    # 黄金价格
    data["gold"] = await _fetch_daily_series(
        "SELECT timestamp, close FROM gold_prices "
        "WHERE symbol = 'XAUUSD' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # 美元 DXY
    data["usd"] = await _fetch_daily_series(
        "SELECT timestamp, close FROM usd_data "
        "WHERE pair = 'DXY' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # 美债 10Y
    data["treasury_10y"] = await _fetch_daily_series(
        "SELECT timestamp, yield FROM treasury_yields "
        "WHERE maturity = '10Y' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # 美债 2Y
    data["treasury_2y"] = await _fetch_daily_series(
        "SELECT timestamp, yield FROM treasury_yields "
        "WHERE maturity = '2Y' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # 原油 WTI
    data["oil"] = await _fetch_daily_series(
        "SELECT timestamp, close FROM oil_data "
        "WHERE oil_type = 'wti' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # 标普 500
    data["sp500"] = await _fetch_daily_series(
        "SELECT timestamp, close FROM stock_market "
        "WHERE index_symbol = 'SPX' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # VIX
    data["vix"] = await _fetch_daily_series(
        "SELECT timestamp, close FROM stock_market "
        "WHERE index_symbol = 'VIX' AND quality_status IN ('valid', 'pending') "
        "ORDER BY timestamp ASC LIMIT 500",
        {},
    )

    # CPI（月度，用 actual_value）
    async with get_db_context() as session:
        result = await session.execute(
            text(
                "SELECT timestamp, actual_value FROM economic_indicators "
                "WHERE indicator_type = 'cpi' "
                "AND actual_value IS NOT NULL "
                "ORDER BY timestamp ASC LIMIT 100"
            )
        )
        rows = result.fetchall()
        columns = list(result.keys())
    cpi: Dict[date, float] = {}
    for row in rows:
        record = dict(zip(columns, row))
        ts = record["timestamp"]
        val = record["actual_value"]
        if ts is not None and val is not None:
            d = ts.date() if hasattr(ts, "date") else ts
            cpi[d] = float(val)
    data["cpi"] = cpi

    return data


# ── 工具函数 ──────────────────────────────────────────────────


def _align_series(
    primary: Dict[date, float],
    secondary: Dict[date, float],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    按共同日期对齐两个序列，返回 (primary_values, secondary_values)。
    仅保留两个序列都有数据的日期。
    """
    common_dates = sorted(set(primary.keys()) & set(secondary.keys()))
    if not common_dates:
        return np.array([]), np.array([])
    p = np.array([primary[d] for d in common_dates])
    s = np.array([secondary[d] for d in common_dates])
    return p, s


def _rolling_correlation(
    x: np.ndarray,
    y: np.ndarray,
    window: int,
) -> List[Optional[float]]:
    """
    计算滚动相关系数。
    返回与输入等长的列表，前 window-1 个为 None。
    """
    n = len(x)
    result: List[Optional[float]] = [None] * n
    if n < window:
        return result
    for i in range(window - 1, n):
        xw = x[i - window + 1: i + 1]
        yw = y[i - window + 1: i + 1]
        if np.std(xw) == 0 or np.std(yw) == 0:
            result[i] = 0.0
        else:
            result[i] = float(np.corrcoef(xw, yw)[0, 1])
    return result


def _daily_returns(prices: np.ndarray) -> np.ndarray:
    """计算日收益率序列"""
    if len(prices) < 2:
        return np.array([])
    return (prices[1:] - prices[:-1]) / prices[:-1]


def _safe_corrcoef(x: np.ndarray, y: np.ndarray) -> float:
    """安全计算相关系数，数据不足时返回 0"""
    if len(x) < 5 or np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(x, y)[0, 1])


# ── 各因素分析 ────────────────────────────────────────────────


def _analyze_gold_vs_usd(
    data: Dict[str, Dict[date, float]],
) -> Dict[str, Any]:
    """黄金 vs 美元分析"""
    gold_vals, usd_vals = _align_series(data["gold"], data["usd"])
    if len(gold_vals) < 10:
        return {
            "name": "黄金-美元关联",
            "impact": "中性",
            "weight": 0.25,
            "score": 0,
            "evidence": "美元数据不足，无法计算关联分析",
            "correlations": {},
        }

    # 滚动相关系数
    corr_30 = _rolling_correlation(gold_vals, usd_vals, 30)
    corr_60 = _rolling_correlation(gold_vals, usd_vals, 60)
    corr_90 = _rolling_correlation(gold_vals, usd_vals, 90)

    # 取最近有效值
    latest_30 = next((c for c in reversed(corr_30) if c is not None), None)
    latest_60 = next((c for c in reversed(corr_60) if c is not None), None)
    latest_90 = next((c for c in reversed(corr_90) if c is not None), None)

    # 整体相关系数
    overall_corr = _safe_corrcoef(gold_vals, usd_vals)

    # 美元涨跌时黄金的响应
    gold_ret = _daily_returns(gold_vals)
    usd_ret = _daily_returns(usd_vals)
    min_len = min(len(gold_ret), len(usd_ret))
    gold_ret = gold_ret[:min_len]
    usd_ret = usd_ret[:min_len]

    usd_up = usd_ret > 0
    usd_down = usd_ret < 0
    gold_when_usd_up = float(np.mean(gold_ret[usd_up])) if np.any(usd_up) else 0.0
    gold_when_usd_down = float(np.mean(gold_ret[usd_down])) if np.any(usd_down) else 0.0

    # 评分：负相关 → 美元弱 → 利多黄金
    # 典型金/美元相关系数在 -0.5 ~ -0.8
    if latest_30 is not None:
        avg_corr = latest_30
    elif overall_corr != 0:
        avg_corr = overall_corr
    else:
        avg_corr = 0.0

    # 将相关系数映射为黄金评分
    # corr ≈ -0.8 → score = +80（强负相关，美元利空 → 黄金利多）
    # corr ≈ 0 → score = 0
    # corr ≈ +0.8 → score = -80（正相关，异常）
    score = int(np.clip(-avg_corr * 100, -100, 100))

    # 结论
    if score > 15:
        conclusion = "利多"
        impact = "利多"
    elif score < -15:
        conclusion = "利空"
        impact = "利空"
    else:
        conclusion = "中性"
        impact = "中性"

    evidence = (
        f"30日滚动相关系数={latest_30:.3f}" if latest_30 is not None else "30日数据不足"
    )
    evidence += (
        f"，60日={latest_60:.3f}" if latest_60 is not None else ""
    )
    evidence += (
        f"，90日={latest_90:.3f}" if latest_90 is not None else ""
    )
    evidence += (
        f"。美元上涨时黄金平均变动={gold_when_usd_up:.4%}"
        f"，美元下跌时黄金平均变动={gold_when_usd_down:.4%}"
    )

    return {
        "name": "黄金-美元关联",
        "impact": impact,
        "weight": 0.25,
        "score": score,
        "evidence": evidence,
        "correlations": {
            "corr_30d": round(latest_30, 4) if latest_30 is not None else None,
            "corr_60d": round(latest_60, 4) if latest_60 is not None else None,
            "corr_90d": round(latest_90, 4) if latest_90 is not None else None,
            "overall": round(overall_corr, 4),
        },
        "gold_response": {
            "when_usd_up": round(gold_when_usd_up, 6),
            "when_usd_down": round(gold_when_usd_down, 6),
        },
    }


def _analyze_gold_vs_bonds(
    data: Dict[str, Dict[date, float]],
) -> Dict[str, Any]:
    """黄金 vs 美债实际利率分析"""
    gold_vals, ty10_vals = _align_series(data["gold"], data["treasury_10y"])
    _, ty2_vals = _align_series(data["gold"], data["treasury_2y"])

    if len(gold_vals) < 10 or len(ty10_vals) < 10:
        return {
            "name": "黄金-实际利率关联",
            "impact": "中性",
            "weight": 0.25,
            "score": 0,
            "evidence": "美债数据不足，无法计算实际利率分析",
        }

    # 使用 CPI 计算实际利率趋势
    # CPI 是月度数据，取最近值作为通胀参考
    cpi_data = data.get("cpi", {})
    latest_cpi = None
    if cpi_data:
        latest_cpi_date = max(cpi_data.keys())
        latest_cpi = cpi_data[latest_cpi_date]

    # 对齐 10Y 和 2Y
    ty10_common, ty2_common = _align_series(
        data["treasury_10y"], data["treasury_2y"]
    )

    # 收益率曲线利差 (2Y-10Y)
    spread_2_10 = None
    if len(ty10_common) > 0 and len(ty2_common) == len(ty10_common):
        spreads = ty2_common - ty10_common
        spread_2_10 = float(spreads[-1]) if len(spreads) > 0 else None

    # 实际利率近似 = 名义10Y - CPI同比
    # 这里用最近 CPI 作为通胀预期代理
    real_rate_trend = None
    if latest_cpi is not None and len(ty10_vals) > 0:
        real_rate_series = ty10_vals - latest_cpi
        # 取最近 30 天的趋势（斜率）
        if len(real_rate_series) >= 10:
            recent = real_rate_series[-30:] if len(real_rate_series) >= 30 else real_rate_series
            x = np.arange(len(recent))
            slope = np.polyfit(x, recent, 1)[0]
            real_rate_trend = float(slope)

    # 黄金与实际利率的相关系数
    corr_gold_real = 0.0
    if latest_cpi is not None:
        real_rates = ty10_vals - latest_cpi
        corr_gold_real = _safe_corrcoef(gold_vals, real_rates)

    # 黄金与收益率曲线利差的相关性
    corr_gold_spread = 0.0
    if (
        spread_2_10 is not None
        and len(ty10_common) > 10
        and len(ty2_common) == len(ty10_common)
    ):
        spreads_all = ty2_common - ty10_common
        # 对齐黄金与利差
        min_len = min(len(gold_vals), len(spreads_all))
        corr_gold_spread = _safe_corrcoef(
            gold_vals[-min_len:], spreads_all[-min_len:]
        )

    # 评分逻辑
    # 实际利率上升 → 利空黄金；实际利率下降 → 利多黄金
    score = 0
    score_components = []

    if real_rate_trend is not None:
        # 斜率 > 0 表示实际利率上升 → 利空
        rate_score = int(np.clip(-real_rate_trend * 500, -50, 50))
        score_components.append(rate_score)

    # 相关系数：黄金与实际利率通常负相关
    # corr < 0 验证了"实际利率上升黄金承压"
    if corr_gold_real != 0:
        corr_score = int(np.clip(-corr_gold_real * 50, -50, 50))
        score_components.append(corr_score)

    score = int(np.clip(np.mean(score_components) if score_components else 0, -100, 100))

    # 结论
    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    # 收益率曲线倒挂检测
    inversion_status = "正常"
    if spread_2_10 is not None:
        if spread_2_10 < 0:
            inversion_status = "倒挂（2Y < 10Y）"
        elif spread_2_10 > 0:
            inversion_status = "正常（2Y > 10Y）"

    evidence = f"10Y名义收益率最新={float(ty10_vals[-1]):.2f}%"
    if latest_cpi is not None:
        evidence += f"，CPI同比={latest_cpi:.1f}%"
        evidence += f"，实际利率近似={float(ty10_vals[-1]) - latest_cpi:.2f}%"
    if real_rate_trend is not None:
        trend_dir = "上升" if real_rate_trend > 0 else "下降"
        evidence += f"，实际利率趋势{trend_dir}"
    evidence += f"，黄金-实际利率相关系数={corr_gold_real:.3f}"
    evidence += f"，收益率曲线{inversion_status}"
    if spread_2_10 is not None:
        evidence += f"（2Y-10Y利差={spread_2_10:.3f}%）"

    return {
        "name": "黄金-实际利率关联",
        "impact": impact,
        "weight": 0.25,
        "score": score,
        "evidence": evidence,
        "real_rate": {
            "nominal_10y_latest": round(float(ty10_vals[-1]), 4),
            "cpi_yoy": round(latest_cpi, 2) if latest_cpi else None,
            "real_rate_approx": round(float(ty10_vals[-1]) - latest_cpi, 4)
            if latest_cpi
            else None,
            "real_rate_trend_slope": round(real_rate_trend, 6)
            if real_rate_trend
            else None,
        },
        "yield_curve": {
            "spread_2y_10y": round(spread_2_10, 4) if spread_2_10 else None,
            "inversion": inversion_status,
            "corr_gold_spread": round(corr_gold_spread, 4),
        },
        "correlations": {
            "gold_vs_real_rate": round(corr_gold_real, 4),
        },
    }


def _analyze_gold_vs_oil(
    data: Dict[str, Dict[date, float]],
) -> Dict[str, Any]:
    """黄金 vs 原油分析"""
    gold_vals, oil_vals = _align_series(data["gold"], data["oil"])
    if len(gold_vals) < 10 or len(oil_vals) < 10:
        return {
            "name": "黄金-原油关联",
            "impact": "中性",
            "weight": 0.15,
            "score": 0,
            "evidence": "原油数据不足，无法计算关联分析",
        }

    # 滚动相关系数
    corr_30 = _rolling_correlation(gold_vals, oil_vals, 30)
    corr_60 = _rolling_correlation(gold_vals, oil_vals, 60)
    latest_30 = next((c for c in reversed(corr_30) if c is not None), None)
    latest_60 = next((c for c in reversed(corr_60) if c is not None), None)
    overall_corr = _safe_corrcoef(gold_vals, oil_vals)

    # 原油作为通胀先行指标的传导分析
    oil_ret = _daily_returns(oil_vals)
    gold_ret = _daily_returns(gold_vals)
    min_len = min(len(gold_ret), len(oil_ret))
    oil_ret = oil_ret[:min_len]
    gold_ret = gold_ret[:min_len]

    # 原油上涨时黄金表现
    oil_up = oil_ret > 0
    oil_down = oil_ret < 0
    gold_when_oil_up = float(np.mean(gold_ret[oil_up])) if np.any(oil_up) else 0.0
    gold_when_oil_down = float(np.mean(gold_ret[oil_down])) if np.any(oil_down) else 0.0

    # 评分：原油上涨 → 通胀预期 → 利多黄金
    # 正相关 → 利多；负相关 → 利空
    if latest_30 is not None:
        avg_corr = latest_30
    else:
        avg_corr = overall_corr

    score = int(np.clip(avg_corr * 80, -100, 100))

    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    evidence = (
        f"30日滚动相关系数={latest_30:.3f}" if latest_30 is not None else "30日数据不足"
    )
    evidence += f"，60日={latest_60:.3f}" if latest_60 is not None else ""
    evidence += (
        f"。原油上涨时黄金平均变动={gold_when_oil_up:.4%}"
        f"，原油下跌时黄金平均变动={gold_when_oil_down:.4%}"
    )

    return {
        "name": "黄金-原油关联",
        "impact": impact,
        "weight": 0.15,
        "score": score,
        "evidence": evidence,
        "correlations": {
            "corr_30d": round(latest_30, 4) if latest_30 is not None else None,
            "corr_60d": round(latest_60, 4) if latest_60 is not None else None,
            "overall": round(overall_corr, 4),
        },
        "gold_response": {
            "when_oil_up": round(gold_when_oil_up, 6),
            "when_oil_down": round(gold_when_oil_down, 6),
        },
    }


def _analyze_gold_vs_stocks(
    data: Dict[str, Dict[date, float]],
) -> Dict[str, Any]:
    """黄金 vs 美股（S&P 500）分析"""
    gold_vals, spx_vals = _align_series(data["gold"], data["sp500"])
    if len(gold_vals) < 10 or len(spx_vals) < 10:
        return {
            "name": "黄金-美股关联",
            "impact": "中性",
            "weight": 0.15,
            "score": 0,
            "evidence": "美股数据不足，无法计算关联分析",
        }

    # 滚动相关系数
    corr_30 = _rolling_correlation(gold_vals, spx_vals, 30)
    corr_60 = _rolling_correlation(gold_vals, spx_vals, 60)
    latest_30 = next((c for c in reversed(corr_30) if c is not None), None)
    latest_60 = next((c for c in reversed(corr_60) if c is not None), None)
    overall_corr = _safe_corrcoef(gold_vals, spx_vals)

    # 风险偏好分析
    spx_ret = _daily_returns(spx_vals)
    gold_ret = _daily_returns(gold_vals)
    min_len = min(len(gold_ret), len(spx_ret))
    spx_ret = spx_ret[:min_len]
    gold_ret = gold_ret[:min_len]

    spx_up = spx_ret > 0
    spx_down = spx_ret < 0
    gold_when_spx_up = float(np.mean(gold_ret[spx_up])) if np.any(spx_up) else 0.0
    gold_when_spx_down = float(np.mean(gold_ret[spx_down])) if np.any(spx_down) else 0.0

    # 评分：美股下跌 → 风险偏好下降 → 利多黄金
    # 负相关 → 风险规避时黄金受益 → 利多
    if latest_30 is not None:
        avg_corr = latest_30
    else:
        avg_corr = overall_corr

    score = int(np.clip(-avg_corr * 80, -100, 100))

    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    evidence = (
        f"30日滚动相关系数={latest_30:.3f}" if latest_30 is not None else "30日数据不足"
    )
    evidence += f"，60日={latest_60:.3f}" if latest_60 is not None else ""
    evidence += (
        f"。美股上涨时黄金平均变动={gold_when_spx_up:.4%}"
        f"，美股下跌时黄金平均变动={gold_when_spx_down:.4%}"
    )

    return {
        "name": "黄金-美股关联",
        "impact": impact,
        "weight": 0.15,
        "score": score,
        "evidence": evidence,
        "correlations": {
            "corr_30d": round(latest_30, 4) if latest_30 is not None else None,
            "corr_60d": round(latest_60, 4) if latest_60 is not None else None,
            "overall": round(overall_corr, 4),
        },
        "risk_appetite": {
            "when_stock_up": round(gold_when_spx_up, 6),
            "when_stock_down": round(gold_when_spx_down, 6),
        },
    }


def _analyze_gold_vs_vix(
    data: Dict[str, Dict[date, float]],
) -> Dict[str, Any]:
    """黄金 vs VIX 恐慌指数分析"""
    gold_vals, vix_vals = _align_series(data["gold"], data["vix"])
    if len(gold_vals) < 10 or len(vix_vals) < 10:
        return {
            "name": "黄金-VIX恐慌关联",
            "impact": "中性",
            "weight": 0.20,
            "score": 0,
            "evidence": "VIX数据不足，无法计算关联分析",
        }

    # 滚动相关系数
    corr_30 = _rolling_correlation(gold_vals, vix_vals, 30)
    corr_60 = _rolling_correlation(gold_vals, vix_vals, 60)
    latest_30 = next((c for c in reversed(corr_30) if c is not None), None)
    latest_60 = next((c for c in reversed(corr_60) if c is not None), None)
    overall_corr = _safe_corrcoef(gold_vals, vix_vals)

    # VIX 飙升时黄金的避险表现
    vix_ret = _daily_returns(vix_vals)
    gold_ret = _daily_returns(gold_vals)
    min_len = min(len(gold_ret), len(vix_ret))
    vix_ret = vix_ret[:min_len]
    gold_ret = gold_ret[:min_len]

    # VIX 大幅上涨（>2%）时黄金表现
    vix_spike = vix_ret > 0.02
    vix_calm = vix_ret <= 0.02
    gold_when_vix_spike = (
        float(np.mean(gold_ret[vix_spike])) if np.any(vix_spike) else 0.0
    )
    gold_when_vix_calm = (
        float(np.mean(gold_ret[vix_calm])) if np.any(vix_calm) else 0.0
    )

    # VIX 水平分析
    vix_latest = float(vix_vals[-1])
    vix_avg = float(np.mean(vix_vals[-20:])) if len(vix_vals) >= 20 else float(np.mean(vix_vals))
    vix_status = "低波动" if vix_latest < 15 else ("正常" if vix_latest < 25 else "高波动")

    # 评分：VIX 与黄金正相关 → 恐慌时黄金避险需求增加 → 利多
    if latest_30 is not None:
        avg_corr = latest_30
    else:
        avg_corr = overall_corr

    score = int(np.clip(avg_corr * 80, -100, 100))

    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    evidence = (
        f"30日滚动相关系数={latest_30:.3f}" if latest_30 is not None else "30日数据不足"
    )
    evidence += f"，60日={latest_60:.3f}" if latest_60 is not None else ""
    evidence += f"。VIX当前={vix_latest:.1f}（{vix_status}），20日均值={vix_avg:.1f}"
    evidence += (
        f"。VIX飙升时黄金平均变动={gold_when_vix_spike:.4%}"
        f"，VIX平稳时黄金平均变动={gold_when_vix_calm:.4%}"
    )

    return {
        "name": "黄金-VIX恐慌关联",
        "impact": impact,
        "weight": 0.20,
        "score": score,
        "evidence": evidence,
        "correlations": {
            "corr_30d": round(latest_30, 4) if latest_30 is not None else None,
            "corr_60d": round(latest_60, 4) if latest_60 is not None else None,
            "overall": round(overall_corr, 4),
        },
        "vix_status": {
            "latest": round(vix_latest, 2),
            "avg_20d": round(vix_avg, 2),
            "status": vix_status,
        },
        "safe_haven": {
            "when_vix_spike": round(gold_when_vix_spike, 6),
            "when_vix_calm": round(gold_when_vix_calm, 6),
        },
    }


# ── 综合评分 ──────────────────────────────────────────────────


def _compute_overall_score(
    factors: List[Dict[str, Any]],
) -> Tuple[int, float]:
    """
    根据各因素加权计算综合评分和置信度。

    Returns:
        (score, confidence)
    """
    if not factors:
        return 0, 0.0

    total_weight = sum(f["weight"] for f in factors)
    if total_weight == 0:
        return 0, 0.0

    weighted_score = sum(f["score"] * f["weight"] for f in factors) / total_weight
    score = int(np.clip(round(weighted_score), -100, 100))

    # 置信度：基于数据充分程度
    # 有有效评分的因素越多、分数越极端，置信度越高
    valid_factors = [f for f in factors if f["score"] != 0]
    data_coverage = len(valid_factors) / len(factors) if factors else 0

    # 分数一致性（所有因素方向是否一致）
    if valid_factors:
        signs = [1 if f["score"] > 0 else -1 for f in valid_factors]
        consistency = abs(sum(signs)) / len(signs)
    else:
        consistency = 0

    # 综合置信度
    confidence = round(min(0.95, 0.3 + data_coverage * 0.4 + consistency * 0.25), 2)

    return score, confidence


# ── 数据存储 ──────────────────────────────────────────────────


async def _store_analysis_result(result: Dict[str, Any]) -> bool:
    """将分析结果存入 analysis_results 表"""
    async with get_db_context() as session:
        sql = text(
            "INSERT INTO analysis_results "
            "(analysis_type, generated_at, conclusion, confidence, score, "
            "factors, data_range, source, metadata) "
            "VALUES (:analysis_type, :generated_at, :conclusion, :confidence, "
            ":score, :factors, :data_range, :source, :metadata)"
        )
        # generated_at 需要 datetime 对象，不能是字符串
        ts = result["timestamp"]
        if isinstance(ts, str):
            from datetime import datetime as dt
            ts = dt.fromisoformat(ts)
        values = {
            "analysis_type": result["analysis_type"],
            "generated_at": ts,
            "conclusion": result["conclusion"],
            "confidence": result["confidence"],
            "score": result["score"],
            "factors": json.dumps(result["factors"], ensure_ascii=False),
            "data_range": json.dumps(result["data_range"], ensure_ascii=False),
            "source": result["source"],
            "metadata": json.dumps(result.get("metadata", {}), ensure_ascii=False),
        }
        try:
            await session.execute(sql, values)
            logger.info(f"分析结果已存储: {result['analysis_type']}")
            return True
        except Exception as e:
            logger.error(f"存储分析结果失败: {e}")
            return False


# ── 主入口 ────────────────────────────────────────────────────


async def run_market_analysis() -> Dict[str, Any]:
    """
    执行完整的跨市场关联分析

    Returns:
        结构化分析结果字典
    """
    logger.info("开始执行跨市场关联分析...")

    # 1. 获取所有市场数据
    data = await _fetch_all_market_data()

    # 数据统计
    data_counts = {k: len(v) for k, v in data.items()}
    logger.info(f"市场数据获取完成: {data_counts}")

    # 2. 执行各因素分析
    factors_results = []
    metadata: Dict[str, Any] = {}

    # 黄金 vs 美元
    usd_result = _analyze_gold_vs_usd(data)
    factors_results.append(usd_result)
    if "correlations" in usd_result:
        metadata["gold_vs_usd"] = usd_result["correlations"]

    # 黄金 vs 美债
    bond_result = _analyze_gold_vs_bonds(data)
    factors_results.append(bond_result)
    if "correlations" in bond_result:
        metadata["gold_vs_bonds"] = bond_result["correlations"]
    if "real_rate" in bond_result:
        metadata["real_rate"] = bond_result["real_rate"]
    if "yield_curve" in bond_result:
        metadata["yield_curve"] = bond_result["yield_curve"]

    # 黄金 vs 原油
    oil_result = _analyze_gold_vs_oil(data)
    factors_results.append(oil_result)
    if "correlations" in oil_result:
        metadata["gold_vs_oil"] = oil_result["correlations"]

    # 黄金 vs 美股
    stock_result = _analyze_gold_vs_stocks(data)
    factors_results.append(stock_result)
    if "correlations" in stock_result:
        metadata["gold_vs_stocks"] = stock_result["correlations"]

    # 黄金 vs VIX
    vix_result = _analyze_gold_vs_vix(data)
    factors_results.append(vix_result)
    if "correlations" in vix_result:
        metadata["gold_vs_vix"] = vix_result["correlations"]

    # 3. 综合评分
    overall_score, confidence = _compute_overall_score(factors_results)

    # 结论
    if overall_score > 15:
        conclusion = "利多"
    elif overall_score < -15:
        conclusion = "利空"
    else:
        conclusion = "中性"

    # 4. 数据时间范围
    gold_dates = sorted(data["gold"].keys()) if data["gold"] else []
    data_range = {
        "start": gold_dates[0].isoformat() if gold_dates else None,
        "end": gold_dates[-1].isoformat() if gold_dates else None,
    }

    # 5. 构造输出
    now = datetime.utcnow()
    analysis_result = {
        "analysis_type": "market_correlation",
        "timestamp": now.isoformat(),
        "conclusion": conclusion,
        "confidence": confidence,
        "score": overall_score,
        "factors": [
            {
                "name": f["name"],
                "impact": f["impact"],
                "weight": f["weight"],
                "evidence": f["evidence"],
                "score": f["score"],
            }
            for f in factors_results
        ],
        "data_range": data_range,
        "source": "market_macro_agent",
        "metadata": {
            "data_counts": data_counts,
            "detailed_factors": factors_results,
            **metadata,
        },
    }

    # 6. 存储到数据库
    stored = await _store_analysis_result(analysis_result)

    logger.info(
        f"跨市场关联分析完成: 综合评分={overall_score}, "
        f"结论={conclusion}, 置信度={confidence}"
    )

    return analysis_result
