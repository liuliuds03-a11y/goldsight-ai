"""
GoldSight AI V3.0 - 宏观面分析引擎

分析宏观经济因素对黄金的影响：
1. 通胀分析（CPI 趋势、实际利率）
2. 利率环境分析（10Y 趋势、收益率曲线倒挂）
3. 美元因素
4. 综合宏观评分（-100 ~ +100）

最终输出结构化分析结论，存入 analysis_results 表。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import text

from app.core.database import get_db_context

logger = logging.getLogger(__name__)

# ── 数据获取 ──────────────────────────────────────────────────


async def _fetch_cpi_data() -> List[Dict[str, Any]]:
    """获取 CPI 数据（月度）"""
    async with get_db_context() as session:
        result = await session.execute(
            text(
                "SELECT timestamp, actual_value, previous_value, period "
                "FROM economic_indicators "
                "WHERE indicator_type = 'cpi' "
                "AND actual_value IS NOT NULL "
                "ORDER BY timestamp ASC LIMIT 100"
            )
        )
        rows = result.fetchall()
        columns = list(result.keys())

    data: List[Dict[str, Any]] = []
    for row in rows:
        record = dict(zip(columns, row))
        ts = record["timestamp"]
        data.append({
            "timestamp": ts.date() if hasattr(ts, "date") else ts,
            "value": float(record["actual_value"]),
            "previous": float(record["previous_value"]) if record["previous_value"] else None,
            "period": record["period"],
        })
    return data


async def _fetch_treasury_data() -> Dict[str, List[Dict[str, Any]]]:
    """获取美债收益率数据"""
    async with get_db_context() as session:
        result = await session.execute(
            text(
                "SELECT timestamp, maturity, yield "
                "FROM treasury_yields "
                "WHERE maturity IN ('2Y', '10Y') "
                "AND quality_status IN ('valid', 'pending') "
                "ORDER BY timestamp ASC LIMIT 1000"
            )
        )
        rows = result.fetchall()
        columns = list(result.keys())

    ty_2y: List[Dict[str, Any]] = []
    ty_10y: List[Dict[str, Any]] = []
    for row in rows:
        record = dict(zip(columns, row))
        ts = record["timestamp"]
        entry = {
            "timestamp": ts.date() if hasattr(ts, "date") else ts,
            "yield": float(record["yield"]),
        }
        if record["maturity"] == "2Y":
            ty_2y.append(entry)
        elif record["maturity"] == "10Y":
            ty_10y.append(entry)

    return {"2Y": ty_2y, "10Y": ty_10y}


async def _fetch_usd_data() -> List[Dict[str, Any]]:
    """获取美元 DXY 数据"""
    async with get_db_context() as session:
        result = await session.execute(
            text(
                "SELECT timestamp, close, change_pct "
                "FROM usd_data "
                "WHERE pair = 'DXY' AND quality_status IN ('valid', 'pending') "
                "ORDER BY timestamp ASC LIMIT 500"
            )
        )
        rows = result.fetchall()
        columns = list(result.keys())

    data: List[Dict[str, Any]] = []
    for row in rows:
        record = dict(zip(columns, row))
        ts = record["timestamp"]
        data.append({
            "timestamp": ts.date() if hasattr(ts, "date") else ts,
            "close": float(record["close"]),
            "change_pct": float(record["change_pct"]) if record["change_pct"] else None,
        })
    return data


# ── 通胀分析 ──────────────────────────────────────────────────


def _analyze_inflation(
    cpi_data: List[Dict[str, Any]],
    treasury_10y: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    通胀分析

    分析 CPI 趋势、实际利率，判断通胀环境对黄金的影响。
    """
    if not cpi_data:
        return {
            "name": "通胀分析",
            "impact": "中性",
            "weight": 0.35,
            "score": 0,
            "evidence": "CPI 数据不足，无法进行通胀分析",
            "details": {},
        }

    # CPI 趋势
    cpi_values = np.array([d["value"] for d in cpi_data])
    cpi_latest = float(cpi_values[-1])
    cpi_3m_ago = float(cpi_values[-3]) if len(cpi_values) >= 3 else cpi_latest
    cpi_6m_ago = float(cpi_values[-6]) if len(cpi_values) >= 6 else cpi_latest
    cpi_12m_ago = float(cpi_values[-12]) if len(cpi_values) >= 12 else cpi_latest

    # CPI 趋势方向
    cpi_trend_3m = cpi_latest - cpi_3m_ago
    cpi_trend_6m = cpi_latest - cpi_6m_ago
    cpi_trend_12m = cpi_latest - cpi_12m_ago

    # 实际利率 = 名义10Y - CPI同比
    real_rate = None
    if treasury_10y and cpi_latest:
        latest_10y = treasury_10y[-1]["yield"]
        real_rate = latest_10y - cpi_latest

    # 实际利率趋势
    real_rate_trend = None
    if treasury_10y and len(treasury_10y) >= 10 and cpi_latest:
        real_rates = [d["yield"] - cpi_latest for d in treasury_10y[-30:]]
        if len(real_rates) >= 5:
            x = np.arange(len(real_rates))
            real_rate_trend = float(np.polyfit(x, real_rates, 1)[0])

    # 评分逻辑
    score = 0
    score_parts = []

    # CPI 水平评分
    if cpi_latest > 4.0:
        cpi_score = 60  # 高通胀，强烈利多黄金
    elif cpi_latest > 3.0:
        cpi_score = 40  # 中高通胀
    elif cpi_latest > 2.0:
        cpi_score = 15  # 温和通胀
    elif cpi_latest > 1.0:
        cpi_score = -10  # 低通胀
    else:
        cpi_score = -30  # 通缩风险
    score_parts.append(("CPI水平", cpi_score))

    # CPI 趋势评分
    if cpi_trend_3m > 0.3:
        trend_score = 30  # 通胀加速
    elif cpi_trend_3m > 0:
        trend_score = 15  # 通胀温和上升
    elif cpi_trend_3m > -0.3:
        trend_score = -10  # 通胀温和下降
    else:
        trend_score = -25  # 通胀快速下降
    score_parts.append(("CPI趋势", trend_score))

    # 实际利率评分
    if real_rate is not None:
        if real_rate < -2:
            rr_score = 50  # 深度负实际利率，强烈利多
        elif real_rate < 0:
            rr_score = 30  # 负实际利率
        elif real_rate < 1:
            rr_score = 0  # 低正实际利率
        elif real_rate < 2:
            rr_score = -20  # 中正实际利率
        else:
            rr_score = -40  # 高正实际利率
        score_parts.append(("实际利率", rr_score))

    # 综合评分
    if score_parts:
        score = int(np.clip(
            np.mean([s for _, s in score_parts]), -100, 100
        ))

    # 结论
    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    # 构造证据
    evidence = f"CPI同比={cpi_latest:.1f}%"
    evidence += f"，3月变化={cpi_trend_3m:+.2f}个百分点"
    if real_rate is not None:
        evidence += f"，实际利率≈{real_rate:.2f}%"
    if real_rate_trend is not None:
        trend_dir = "上升" if real_rate_trend > 0 else "下降"
        evidence += f"（{trend_dir}中）"

    return {
        "name": "通胀分析",
        "impact": impact,
        "weight": 0.35,
        "score": score,
        "evidence": evidence,
        "details": {
            "cpi_latest": round(cpi_latest, 2),
            "cpi_3m_ago": round(cpi_3m_ago, 2),
            "cpi_6m_ago": round(cpi_6m_ago, 2),
            "cpi_12m_ago": round(cpi_12m_ago, 2),
            "cpi_trend_3m": round(cpi_trend_3m, 2),
            "cpi_trend_6m": round(cpi_trend_6m, 2),
            "real_rate": round(real_rate, 4) if real_rate is not None else None,
            "real_rate_trend": round(real_rate_trend, 6)
            if real_rate_trend is not None
            else None,
            "score_breakdown": [
                {"factor": name, "score": s} for name, s in score_parts
            ],
        },
    }


# ── 利率环境分析 ──────────────────────────────────────────────


def _analyze_rate_environment(
    treasury_2y: List[Dict[str, Any]],
    treasury_10y: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    利率环境分析

    分析 10Y 美债趋势、2Y-10Y 利差（收益率曲线倒挂检测），
    判断利率环境对黄金的影响。
    """
    if not treasury_10y:
        return {
            "name": "利率环境分析",
            "impact": "中性",
            "weight": 0.35,
            "score": 0,
            "evidence": "美债数据不足，无法进行利率环境分析",
            "details": {},
        }

    # 10Y 趋势
    ty10_values = np.array([d["yield"] for d in treasury_10y])
    ty10_latest = float(ty10_values[-1])
    ty10_30d_ago = float(ty10_values[-22]) if len(ty10_values) >= 22 else float(ty10_values[0])
    ty10_90d_ago = float(ty10_values[-66]) if len(ty10_values) >= 66 else float(ty10_values[0])

    # 10Y 趋势方向和幅度
    ty10_trend_30d = ty10_latest - ty10_30d_ago
    ty10_trend_90d = ty10_latest - ty10_90d_ago

    # 2Y-10Y 利差（收益率曲线）
    spread_series: List[Tuple[date, float]] = []
    if treasury_2y and treasury_10y:
        ty2_by_date = {d["timestamp"]: d["yield"] for d in treasury_2y}
        ty10_by_date = {d["timestamp"]: d["yield"] for d in treasury_10y}
        common_dates = sorted(set(ty2_by_date.keys()) & set(ty10_by_date.keys()))
        for d in common_dates:
            spread = ty10_by_date[d] - ty2_by_date[d]
            spread_series.append((d, spread))

    latest_spread = spread_series[-1][1] if spread_series else None
    avg_spread_30d = None
    if spread_series:
        recent_spreads = [s for _, s in spread_series[-22:]]
        avg_spread_30d = float(np.mean(recent_spreads)) if recent_spreads else None

    # 收益率曲线倒挂检测
    inversion_detected = False
    inversion_depth = None
    if latest_spread is not None:
        # 传统倒挂：2Y > 10Y（利差为负）
        if latest_spread < 0:
            inversion_detected = True
            inversion_depth = latest_spread

    # 评分逻辑
    score = 0
    score_parts = []

    # 10Y 趋势评分
    # 收益率下降 → 利多黄金；收益率上升 → 利空黄金
    if ty10_trend_30d < -0.2:
        trend_score = 35  # 收益率显著下降
    elif ty10_trend_30d < -0.05:
        trend_score = 15  # 收益率小幅下降
    elif ty10_trend_30d < 0.05:
        trend_score = 0  # 收益率稳定
    elif ty10_trend_30d < 0.2:
        trend_score = -15  # 收益率小幅上升
    else:
        trend_score = -35  # 收益率显著上升
    score_parts.append(("10Y趋势", trend_score))

    # 10Y 水平评分
    if ty10_latest < 3.0:
        level_score = 30  # 低利率环境
    elif ty10_latest < 4.0:
        level_score = 10  # 中等利率
    elif ty10_latest < 5.0:
        level_score = -10  # 较高利率
    else:
        level_score = -25  # 高利率环境
    score_parts.append(("10Y水平", level_score))

    # 收益率曲线评分
    if latest_spread is not None:
        if latest_spread < -0.5:
            curve_score = 40  # 深度倒挂，强烈利多（衰退预期）
        elif latest_spread < 0:
            curve_score = 25  # 轻度倒挂
        elif latest_spread < 0.5:
            curve_score = 5  # 平坦
        elif latest_spread < 1.5:
            curve_score = -5  # 正常
        else:
            curve_score = -15  # 陡峭（经济过热）
        score_parts.append(("收益率曲线", curve_score))

    # 综合评分
    if score_parts:
        score = int(np.clip(
            np.mean([s for _, s in score_parts]), -100, 100
        ))

    # 结论
    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    # 证据
    evidence = f"10Y美债收益率={ty10_latest:.2f}%"
    evidence += f"，30日变化={ty10_trend_30d:+.2f}个百分点"
    if latest_spread is not None:
        evidence += f"，2Y-10Y利差={latest_spread:.3f}%"
        if inversion_detected:
            evidence += f"（倒挂{inversion_depth:.3f}%）"
        else:
            evidence += "（正常）"

    return {
        "name": "利率环境分析",
        "impact": impact,
        "weight": 0.35,
        "score": score,
        "evidence": evidence,
        "details": {
            "treasury_10y_latest": round(ty10_latest, 4),
            "treasury_10y_30d_change": round(ty10_trend_30d, 4),
            "treasury_10y_90d_change": round(ty10_trend_90d, 4),
            "spread_2y_10y": round(latest_spread, 4) if latest_spread else None,
            "avg_spread_30d": round(avg_spread_30d, 4) if avg_spread_30d else None,
            "inversion_detected": inversion_detected,
            "inversion_depth": round(inversion_depth, 4) if inversion_depth else None,
            "score_breakdown": [
                {"factor": name, "score": s} for name, s in score_parts
            ],
        },
    }


# ── 美元因素分析 ──────────────────────────────────────────────


def _analyze_usd_factor(
    usd_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    美元因素分析

    分析美元走势对黄金的影响。
    """
    if not usd_data or len(usd_data) < 10:
        return {
            "name": "美元因素分析",
            "impact": "中性",
            "weight": 0.30,
            "score": 0,
            "evidence": "美元数据不足，无法进行分析",
            "details": {},
        }

    dxy_values = np.array([d["close"] for d in usd_data])
    dxy_latest = float(dxy_values[-1])
    dxy_30d_ago = float(dxy_values[-22]) if len(dxy_values) >= 22 else float(dxy_values[0])
    dxy_90d_ago = float(dxy_values[-66]) if len(dxy_values) >= 66 else float(dxy_values[0])

    # 美元趋势
    dxy_trend_30d = (dxy_latest - dxy_30d_ago) / dxy_30d_ago * 100
    dxy_trend_90d = (dxy_latest - dxy_90d_ago) / dxy_90d_ago * 100

    # 评分：美元走弱 → 利多黄金
    score = 0
    score_parts = []

    # 30日趋势评分
    if dxy_trend_30d < -3:
        trend_score = 40  # 美元大幅走弱
    elif dxy_trend_30d < -1:
        trend_score = 20  # 美元小幅走弱
    elif dxy_trend_30d < 1:
        trend_score = 0  # 美元稳定
    elif dxy_trend_30d < 3:
        trend_score = -20  # 美元小幅走强
    else:
        trend_score = -40  # 美元大幅走强
    score_parts.append(("美元30日趋势", trend_score))

    # 90日趋势评分
    if dxy_trend_90d < -5:
        trend_score_90 = 35
    elif dxy_trend_90d < -2:
        trend_score_90 = 15
    elif dxy_trend_90d < 2:
        trend_score_90 = 0
    elif dxy_trend_90d < 5:
        trend_score_90 = -15
    else:
        trend_score_90 = -30
    score_parts.append(("美元90日趋势", trend_score_90))

    score = int(np.clip(
        np.mean([s for _, s in score_parts]), -100, 100
    ))

    if score > 15:
        impact = "利多"
    elif score < -15:
        impact = "利空"
    else:
        impact = "中性"

    trend_dir = "走弱" if dxy_trend_30d < 0 else "走强"
    evidence = (
        f"DXY={dxy_latest:.2f}，30日{trend_dir}{abs(dxy_trend_30d):.1f}%"
        f"，90日变化{dxy_trend_90d:+.1f}%"
    )

    return {
        "name": "美元因素分析",
        "impact": impact,
        "weight": 0.30,
        "score": score,
        "evidence": evidence,
        "details": {
            "dxy_latest": round(dxy_latest, 2),
            "dxy_30d_change_pct": round(dxy_trend_30d, 2),
            "dxy_90d_change_pct": round(dxy_trend_90d, 2),
            "score_breakdown": [
                {"factor": name, "score": s} for name, s in score_parts
            ],
        },
    }


# ── 综合宏观评分 ──────────────────────────────────────────────


def _compute_macro_score(
    factors: List[Dict[str, Any]],
) -> Tuple[int, float]:
    """
    综合通胀、利率、美元因素，计算宏观面对黄金的利多/利空评分。

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

    # 置信度
    valid_factors = [f for f in factors if f["score"] != 0]
    data_coverage = len(valid_factors) / len(factors) if factors else 0

    if valid_factors:
        signs = [1 if f["score"] > 0 else -1 for f in valid_factors]
        consistency = abs(sum(signs)) / len(signs)
    else:
        consistency = 0

    confidence = round(min(0.95, 0.3 + data_coverage * 0.4 + consistency * 0.25), 2)

    return score, confidence


# ── 数据存储 ──────────────────────────────────────────────────


async def _store_analysis_result(result: Dict[str, Any]) -> bool:
    """将宏观分析结果存入 analysis_results 表"""
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
            logger.info(f"宏观分析结果已存储: {result['analysis_type']}")
            return True
        except Exception as e:
            logger.error(f"存储宏观分析结果失败: {e}")
            return False


# ── 主入口 ────────────────────────────────────────────────────


async def run_macro_analysis() -> Dict[str, Any]:
    """
    执行完整的宏观面分析

    Returns:
        结构化分析结果字典
    """
    logger.info("开始执行宏观面分析...")

    # 1. 获取数据
    cpi_data = await _fetch_cpi_data()
    treasury_data = await _fetch_treasury_data()
    usd_data = await _fetch_usd_data()

    logger.info(
        f"宏观数据获取完成: CPI={len(cpi_data)}条, "
        f"10Y美债={len(treasury_data['10Y'])}条, "
        f"2Y美债={len(treasury_data['2Y'])}条, "
        f"DXY={len(usd_data)}条"
    )

    # 2. 执行各因素分析
    factors_results = []

    # 通胀分析
    inflation_result = _analyze_inflation(cpi_data, treasury_data["10Y"])
    factors_results.append(inflation_result)

    # 利率环境分析
    rate_result = _analyze_rate_environment(
        treasury_data["2Y"], treasury_data["10Y"]
    )
    factors_results.append(rate_result)

    # 美元因素分析
    usd_result = _analyze_usd_factor(usd_data)
    factors_results.append(usd_result)

    # 3. 综合宏观评分
    overall_score, confidence = _compute_macro_score(factors_results)

    # 结论
    if overall_score > 15:
        conclusion = "利多"
    elif overall_score < -15:
        conclusion = "利空"
    else:
        conclusion = "中性"

    # 4. 数据时间范围
    all_dates = []
    if cpi_data:
        all_dates.extend([d["timestamp"] for d in cpi_data])
    if treasury_data["10Y"]:
        all_dates.extend([d["timestamp"] for d in treasury_data["10Y"]])
    if usd_data:
        all_dates.extend([d["timestamp"] for d in usd_data])

    data_range = {}
    if all_dates:
        data_range = {
            "start": min(all_dates).isoformat(),
            "end": max(all_dates).isoformat(),
        }

    # 5. 构造输出
    now = datetime.utcnow()
    analysis_result = {
        "analysis_type": "macro",
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
            "data_counts": {
                "cpi": len(cpi_data),
                "treasury_10y": len(treasury_data["10Y"]),
                "treasury_2y": len(treasury_data["2Y"]),
                "usd_dxy": len(usd_data),
            },
            "detailed_factors": factors_results,
        },
    }

    # 6. 存储到数据库
    stored = await _store_analysis_result(analysis_result)

    logger.info(
        f"宏观面分析完成: 综合评分={overall_score}, "
        f"结论={conclusion}, 置信度={confidence}"
    )

    return analysis_result
