"""
GoldSight AI V3.0 - AI 综合预测引擎

从数据库读取技术指标、跨市场分析、宏观分析结果，
构造结构化提示词发给 DeepSeek，获取 JSON 格式的预测结论，
并存入 analysis_results 表（analysis_type = 'ai_prediction'）。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_context
from app.services.ai.deepseek_client import DeepSeekClient, DeepSeekAPIError

logger = logging.getLogger(__name__)

# ── 系统提示词 ────────────────────────────────────────────────

_SYSTEM_PROMPT = """你是 GoldSight AI 平台的专业黄金分析师，拥有 20 年以上的贵金属市场分析经验。

你的职责：
1. 基于提供的技术指标、跨市场关联分析和宏观面数据，对黄金价格做出综合判断
2. 给出明确的方向判断（看涨/看跌/震荡）
3. 提供具体的目标价位、支撑位和阻力位
4. 列出关键风险因素

分析框架：
- 技术面：MA/EMA 趋势、MACD 动能、RSI 超买超卖、布林带波动、ADX 趋势强度
- 跨市场：美元走势（负相关）、美债实际利率（负相关）、原油（通胀传导）、美股（风险偏好）、VIX（恐慌情绪）
- 宏观面：CPI 通胀趋势、美联储利率政策、实际利率走向

输出要求：
你必须以严格的 JSON 格式输出分析结论，不要包含任何其他文字。JSON 格式如下：
{
    "prediction_type": "gold_price",
    "direction": "看涨 或 看跌 或 震荡",
    "confidence": 0.0到1.0之间的数值,
    "target_price": 目标价格数值,
    "time_horizon": "短期(1-5天) 或 中期(1-4周)",
    "reasoning": "详细的分析理由，100-300字",
    "risk_factors": ["风险因素1", "风险因素2", "风险因素3"],
    "key_levels": {
        "support": 支撑位价格,
        "resistance": 阻力位价格
    }
}

注意事项：
- confidence 应基于数据充分程度和信号一致性，通常在 0.5-0.85 之间
- target_price 应基于当前价格和技术分析给出合理预期
- support 和 resistance 应基于关键技术位（如布林带、均线、斐波那契）
- reasoning 中应引用具体的技术指标数值作为依据
- risk_factors 至少列出 2 个，最多 5 个"""


# ── 数据获取 ──────────────────────────────────────────────────


async def _fetch_latest_technical_indicators() -> List[Dict[str, Any]]:
    """获取最新的技术指标数据"""
    async with get_db_context() as session:
        sql = text(
            "SELECT ti.timestamp, ti.indicator_name, ti.period, ti.category, "
            "ti.value, ti.extra_data "
            "FROM technical_indicators ti "
            "INNER JOIN ( "
            "    SELECT indicator_name, period, MAX(timestamp) AS max_ts "
            "    FROM technical_indicators "
            "    WHERE symbol = 'XAUUSD' "
            "    GROUP BY indicator_name, period "
            ") latest ON ti.indicator_name = latest.indicator_name "
            "    AND ti.period = latest.period "
            "    AND ti.timestamp = latest.max_ts "
            "WHERE ti.symbol = 'XAUUSD' "
            "ORDER BY ti.category, ti.indicator_name, ti.period"
        )
        result = await session.execute(sql)
        rows = result.fetchall()
        columns = list(result.keys())

    indicators = []
    for row in rows:
        record = dict(zip(columns, row))
        # 处理 JSONB 字段
        if isinstance(record.get("extra_data"), str):
            try:
                record["extra_data"] = json.loads(record["extra_data"])
            except (json.JSONDecodeError, TypeError):
                record["extra_data"] = {}
        # Decimal → float
        if record.get("value") is not None:
            record["value"] = float(record["value"])
        # datetime → str
        if isinstance(record.get("timestamp"), datetime):
            record["timestamp"] = record["timestamp"].isoformat()
        indicators.append(record)

    return indicators


async def _fetch_latest_analysis(analysis_type: str) -> Optional[Dict[str, Any]]:
    """获取指定类型的最新分析结果"""
    async with get_db_context() as session:
        sql = text(
            "SELECT id, analysis_type, generated_at, conclusion, confidence, "
            "score, factors, data_range, source, metadata "
            "FROM analysis_results "
            "WHERE analysis_type = :analysis_type "
            "ORDER BY generated_at DESC "
            "LIMIT 1"
        )
        result = await session.execute(sql, {"analysis_type": analysis_type})
        row = result.fetchone()
        if not row:
            return None

        columns = list(result.keys())
        record = dict(zip(columns, row))

    # 解析 JSONB 字段
    for key in ("factors", "data_range", "metadata"):
        val = record.get(key)
        if isinstance(val, str):
            try:
                record[key] = json.loads(val)
            except (json.JSONDecodeError, TypeError):
                record[key] = [] if key == "factors" else {}
        elif val is None:
            record[key] = [] if key == "factors" else {}

    # datetime → str
    if isinstance(record.get("generated_at"), datetime):
        record["generated_at"] = record["generated_at"].isoformat()

    # Decimal → float
    for key in ("confidence", "score"):
        if record.get(key) is not None:
            record[key] = float(record[key])

    return record


async def _fetch_latest_gold_price() -> Optional[Dict[str, Any]]:
    """获取最新黄金价格"""
    async with get_db_context() as session:
        sql = text(
            "SELECT timestamp, close, high, low, open, change_pct "
            "FROM gold_prices "
            "WHERE symbol = 'XAUUSD' "
            "AND quality_status IN ('valid', 'pending') "
            "ORDER BY timestamp DESC "
            "LIMIT 1"
        )
        result = await session.execute(sql)
        row = result.fetchone()
        if not row:
            return None

        columns = list(result.keys())
        record = dict(zip(columns, row))

    if isinstance(record.get("timestamp"), datetime):
        record["timestamp"] = record["timestamp"].isoformat()
    for key in ("close", "high", "low", "open", "change_pct"):
        if record.get(key) is not None:
            record[key] = float(record[key])

    return record


# ── 提示词构造 ────────────────────────────────────────────────


def _build_user_message(
    gold_price: Optional[Dict[str, Any]],
    technical_indicators: List[Dict[str, Any]],
    market_analysis: Optional[Dict[str, Any]],
    macro_analysis: Optional[Dict[str, Any]],
) -> str:
    """
    构造发给 DeepSeek 的用户消息

    将所有分析数据整合为结构化的文本上下文。
    """
    sections: List[str] = []

    # 当前黄金价格
    if gold_price:
        sections.append("## 当前黄金价格")
        sections.append(f"- 最新价格: {gold_price.get('close', 'N/A')} 美元/盎司")
        sections.append(f"- 最高价: {gold_price.get('high', 'N/A')}")
        sections.append(f"- 最低价: {gold_price.get('low', 'N/A')}")
        sections.append(f"- 开盘价: {gold_price.get('open', 'N/A')}")
        change_pct = gold_price.get("change_pct")
        if change_pct is not None:
            sections.append(f"- 涨跌幅: {change_pct:.2f}%")
        sections.append(f"- 数据时间: {gold_price.get('timestamp', 'N/A')}")
    else:
        sections.append("## 当前黄金价格\n- 暂无最新价格数据")

    # 技术指标
    if technical_indicators:
        sections.append("\n## 技术指标（最新值）")
        # 按类别分组
        categories: Dict[str, List[Dict]] = {}
        for ind in technical_indicators:
            cat = ind.get("category", "unknown") or "unknown"
            categories.setdefault(str(cat), []).append(ind)

        category_names = {
            "trend": "趋势类",
            "momentum": "动量类",
            "volatility": "波动类",
            "support_resistance": "支撑阻力类",
        }

        for cat_key, cat_name in category_names.items():
            if cat_key in categories:
                sections.append(f"\n### {cat_name}指标")
                for ind in categories[cat_key]:
                    name = ind.get("indicator_name", "unknown")
                    period = ind.get("period", "")
                    value = ind.get("value")
                    value_str = f"{value:.4f}" if value is not None else "N/A"
                    period_str = f"({period})" if period else ""
                    sections.append(f"- {name}{period_str}: {value_str}")

    else:
        sections.append("\n## 技术指标\n- 暂无技术指标数据")

    # 跨市场分析
    if market_analysis:
        sections.append("\n## 跨市场关联分析")
        sections.append(f"- 综合结论: {market_analysis.get('conclusion', 'N/A')}")
        sections.append(f"- 综合评分: {market_analysis.get('score', 'N/A')}")
        sections.append(f"- 置信度: {market_analysis.get('confidence', 'N/A')}")

        factors = market_analysis.get("factors", [])
        if factors:
            sections.append("- 各因素分析:")
            for f in factors:
                name = f.get("name", "")
                impact = f.get("impact", "")
                score = f.get("score", "")
                evidence = f.get("evidence", "")
                sections.append(f"  - {name}: {impact}（评分 {score}）— {evidence}")
    else:
        sections.append("\n## 跨市场关联分析\n- 暂无市场分析数据")

    # 宏观分析
    if macro_analysis:
        sections.append("\n## 宏观面分析")
        sections.append(f"- 综合结论: {macro_analysis.get('conclusion', 'N/A')}")
        sections.append(f"- 综合评分: {macro_analysis.get('score', 'N/A')}")
        sections.append(f"- 置信度: {macro_analysis.get('confidence', 'N/A')}")

        factors = macro_analysis.get("factors", [])
        if factors:
            sections.append("- 各因素分析:")
            for f in factors:
                name = f.get("name", "")
                impact = f.get("impact", "")
                score = f.get("score", "")
                evidence = f.get("evidence", "")
                sections.append(f"  - {name}: {impact}（评分 {score}）— {evidence}")
    else:
        sections.append("\n## 宏观面分析\n- 暂无宏观分析数据")

    # 分析请求
    sections.append(
        "\n## 分析请求\n"
        "请基于以上所有数据，给出你的黄金价格综合预测。"
        "必须严格按照系统提示词中要求的 JSON 格式输出。"
    )

    return "\n".join(sections)


# ── 结果存储 ──────────────────────────────────────────────────


async def _store_prediction_result(result: Dict[str, Any]) -> bool:
    """将 AI 预测结果存入 analysis_results 表"""
    async with get_db_context() as session:
        sql = text(
            "INSERT INTO analysis_results "
            "(analysis_type, generated_at, conclusion, confidence, score, "
            "factors, data_range, source, metadata) "
            "VALUES (:analysis_type, :generated_at, :conclusion, :confidence, "
            ":score, :factors, :data_range, :source, :metadata)"
        )

        ts = result.get("generated_at")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)

        # 方向映射为 conclusion
        direction = result.get("direction", "震荡")
        conclusion = direction  # 看涨/看跌/震荡

        # 置信度
        confidence = float(result.get("confidence", 0.0))
        confidence = max(0.0, min(1.0, confidence))

        # 评分：映射到 -100 ~ +100
        if direction == "看涨":
            score = 50.0 + confidence * 50.0
        elif direction == "看跌":
            score = -(50.0 + confidence * 50.0)
        else:
            score = 0.0
        score = max(-100.0, min(100.0, score))

        # 因素列表
        risk_factors = result.get("risk_factors", [])
        reasoning = result.get("reasoning", "")
        key_levels = result.get("key_levels", {})

        factors = json.dumps([{
            "name": "AI 综合预测",
            "impact": direction,
            "evidence": reasoning,
            "risk_factors": risk_factors,
            "key_levels": key_levels,
        }], ensure_ascii=False)

        data_range = json.dumps({
            "prediction_type": result.get("prediction_type", "gold_price"),
            "time_horizon": result.get("time_horizon", ""),
            "target_price": result.get("target_price"),
        }, ensure_ascii=False)

        metadata = json.dumps({
            "ai_model": result.get("model", "deepseek"),
            "raw_response": result.get("raw_response", {}),
        }, ensure_ascii=False)

        values = {
            "analysis_type": "ai_prediction",
            "generated_at": ts,
            "conclusion": conclusion,
            "confidence": confidence,
            "score": score,
            "factors": factors,
            "data_range": data_range,
            "source": "deepseek_ai",
            "metadata": metadata,
        }

        try:
            await session.execute(sql, values)
            logger.info(f"AI 预测结果已存储: direction={direction}, confidence={confidence}")
            return True
        except Exception as e:
            logger.error(f"存储 AI 预测结果失败: {e}")
            return False


# ── 降级处理 ──────────────────────────────────────────────────


def _build_fallback_result(
    gold_price: Optional[Dict[str, Any]],
    error_message: str,
) -> Dict[str, Any]:
    """
    DeepSeek API 调用失败时的降级结果

    基于最新价格返回一个基础的"数据不足"结论。
    """
    current_price = 0.0
    if gold_price and gold_price.get("close"):
        current_price = float(gold_price["close"])

    now = datetime.utcnow()
    return {
        "prediction_type": "gold_price",
        "direction": "震荡",
        "confidence": 0.1,
        "target_price": current_price,
        "time_horizon": "短期(1-5天)",
        "reasoning": f"AI 模型调用失败，无法进行有效预测。错误信息: {error_message}。"
                     f"当前黄金价格 {current_price:.2f} 美元/盎司。"
                     f"建议等待 AI 服务恢复后重新获取预测。",
        "risk_factors": [
            "AI 模型服务不可用，预测结果不可靠",
            "建议参考技术指标和跨市场分析数据做决策",
        ],
        "key_levels": {
            "support": round(current_price * 0.98, 2) if current_price else 0,
            "resistance": round(current_price * 1.02, 2) if current_price else 0,
        },
        "generated_at": now.isoformat(),
        "model": "fallback",
        "is_fallback": True,
    }


# ── 主入口 ────────────────────────────────────────────────────


async def run_ai_prediction() -> Dict[str, Any]:
    """
    执行 AI 综合预测

    1. 从数据库读取技术指标、市场分析、宏观分析
    2. 构造提示词
    3. 调用 DeepSeek API
    4. 解析 JSON 结果
    5. 存入数据库

    Returns:
        预测结果字典
    """
    logger.info("开始执行 AI 综合预测...")

    # 1. 收集数据
    gold_price = await _fetch_latest_gold_price()
    technical_indicators = await _fetch_latest_technical_indicators()
    market_analysis = await _fetch_latest_analysis("market_correlation")
    macro_analysis = await _fetch_latest_analysis("macro")

    logger.info(
        f"数据收集完成: gold_price={'有' if gold_price else '无'}, "
        f"indicators={len(technical_indicators)} 条, "
        f"market_analysis={'有' if market_analysis else '无'}, "
        f"macro_analysis={'有' if macro_analysis else '无'}"
    )

    # 2. 构造提示词
    user_message = _build_user_message(
        gold_price, technical_indicators, market_analysis, macro_analysis,
    )

    # 3. 调用 DeepSeek
    client = DeepSeekClient()
    now = datetime.utcnow()

    if not client.is_configured():
        logger.warning("DeepSeek API 未配置，返回降级结果")
        fallback = _build_fallback_result(gold_price, "DeepSeek API Key 未配置")
        fallback["generated_at"] = now.isoformat()
        await _store_prediction_result(fallback)
        return fallback

    try:
        ai_result = await client.chat_json(
            system_prompt=_SYSTEM_PROMPT,
            user_message=user_message,
            temperature=0.5,
            max_tokens=2048,
        )
    except DeepSeekAPIError as e:
        logger.error(f"DeepSeek API 调用失败: {e}")
        fallback = _build_fallback_result(gold_price, str(e))
        fallback["generated_at"] = now.isoformat()
        await _store_prediction_result(fallback)
        return fallback
    except Exception as e:
        logger.error(f"AI 预测执行失败: {e}")
        fallback = _build_fallback_result(gold_price, str(e))
        fallback["generated_at"] = now.isoformat()
        await _store_prediction_result(fallback)
        return fallback

    # 4. 校验 AI 返回结果
    if "error" in ai_result and ai_result.get("error") == "JSON 解析失败":
        logger.warning("DeepSeek 返回内容无法解析为 JSON")
        fallback = _build_fallback_result(gold_price, "AI 返回格式异常")
        fallback["generated_at"] = now.isoformat()
        await _store_prediction_result(fallback)
        return fallback

    # 补充元数据
    ai_result.setdefault("prediction_type", "gold_price")
    ai_result.setdefault("direction", "震荡")
    ai_result.setdefault("confidence", 0.5)
    ai_result.setdefault("target_price", 0)
    ai_result.setdefault("time_horizon", "短期(1-5天)")
    ai_result.setdefault("reasoning", "")
    ai_result.setdefault("risk_factors", [])
    ai_result.setdefault("key_levels", {"support": 0, "resistance": 0})
    ai_result["generated_at"] = now.isoformat()
    ai_result["model"] = client.model
    ai_result["is_fallback"] = False
    ai_result["raw_response"] = ai_result.copy()

    # 5. 存入数据库
    stored = await _store_prediction_result(ai_result)

    logger.info(
        f"AI 综合预测完成: direction={ai_result['direction']}, "
        f"confidence={ai_result['confidence']}, "
        f"target_price={ai_result['target_price']}, "
        f"存储={'成功' if stored else '失败'}"
    )

    return ai_result


async def run_ai_summary() -> Dict[str, Any]:
    """
    生成 AI 综合摘要（一句话总结当前行情）

    Returns:
        包含 summary 字段的结果字典
    """
    logger.info("开始生成 AI 综合摘要...")

    # 收集最新分析数据
    gold_price = await _fetch_latest_gold_price()
    market_analysis = await _fetch_latest_analysis("market_correlation")
    macro_analysis = await _fetch_latest_analysis("macro")

    client = DeepSeekClient()
    now = datetime.utcnow()

    if not client.is_configured():
        return {
            "summary": "DeepSeek API 未配置，无法生成 AI 摘要。",
            "generated_at": now.isoformat(),
            "is_fallback": True,
        }

    # 构造简要上下文
    context_parts = []
    if gold_price:
        price = gold_price.get("close", "N/A")
        change = gold_price.get("change_pct", "N/A")
        context_parts.append(f"当前黄金价格 {price} 美元，涨跌幅 {change}%")

    if market_analysis:
        context_parts.append(
            f"跨市场分析结论: {market_analysis.get('conclusion', 'N/A')}，"
            f"评分 {market_analysis.get('score', 'N/A')}"
        )

    if macro_analysis:
        context_parts.append(
            f"宏观面分析结论: {macro_analysis.get('conclusion', 'N/A')}，"
            f"评分 {macro_analysis.get('score', 'N/A')}"
        )

    context = "；".join(context_parts) if context_parts else "暂无最新数据"

    summary_prompt = (
        "请用一句话（不超过 80 字）简洁总结当前黄金市场行情和短期展望。"
        "要求专业、精炼、有观点。"
    )

    try:
        summary_text = await client.chat_text(
            system_prompt="你是 GoldSight AI 平台的专业黄金分析师。请用简洁的中文回答问题。",
            user_message=f"{context}\n\n{summary_prompt}",
            temperature=0.7,
            max_tokens=256,
        )
        summary_text = summary_text.strip().strip('"').strip("'")
    except Exception as e:
        logger.error(f"AI 摘要生成失败: {e}")
        return {
            "summary": f"AI 摘要生成失败: {e}",
            "generated_at": now.isoformat(),
            "is_fallback": True,
        }

    result = {
        "summary": summary_text,
        "context": context,
        "generated_at": now.isoformat(),
        "model": client.model,
        "is_fallback": False,
    }

    logger.info(f"AI 综合摘要生成完成: {summary_text[:50]}...")
    return result
