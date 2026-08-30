"""
GoldSight AI V3.0 - 实时数据直连接口

直接从公开 API 获取实时市场数据，不经过 AI，带 Redis 缓存（5 分钟）。
前端刷新按钮优先查缓存，缓存过期才请求外部 API。
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter

from app.core.redis_client import get_redis, is_redis_available
from app.core.response import success

logger = logging.getLogger(__name__)

router = APIRouter()

# 缓存配置
CACHE_TTL = 300  # 5 分钟
CACHE_PREFIX = "realtime:"

# 外部 API 超时
HTTP_TIMEOUT = 15.0


async def _get_cached(key: str) -> Optional[Dict[str, Any]]:
    """从 Redis 获取缓存数据"""
    if not is_redis_available():
        return None
    try:
        r = get_redis()
        data = await r.get(f"{CACHE_PREFIX}{key}")
        if data:
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Redis 缓存读取失败: {e}")
    return None


async def _set_cached(key: str, data: Dict[str, Any]) -> None:
    """写入 Redis 缓存"""
    if not is_redis_available():
        return
    try:
        r = get_redis()
        await r.setex(f"{CACHE_PREFIX}{key}", CACHE_TTL, json.dumps(data, ensure_ascii=False))
    except Exception as e:
        logger.warning(f"Redis 缓存写入失败: {e}")


async def _fetch_gold_price() -> Dict[str, Any]:
    """获取黄金价格 - gold-api.com（免费无需 key）"""
    cached = await _get_cached("gold")
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get("https://api.gold-api.com/price/XAU")
            if r.status_code == 200:
                data = r.json()
                price = data.get("price")
                if price:
                    price = float(price)
                    price_per_gram = round(price / 31.1035, 2)
                    updated = data.get("updatedAt", "")[:10]
                    result = {
                        "symbol": "XAU/USD",
                        "price": round(price, 2),
                        "price_per_gram_pln": None,
                        "price_per_gram_usd": price_per_gram,
                        "pln_usd_rate": None,
                        "date": updated,
                        "source": "gold-api",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "_cached": False,
                    }
                    await _set_cached("gold", result)
                    return result
    except Exception as e:
        logger.error(f"黄金价格获取失败: {e}")
    
    return {"symbol": "XAU/USD", "price": None, "error": "数据获取失败", "source": "gold-api"}


async def _fetch_usd_index() -> Dict[str, Any]:
    """获取美元汇率数据 - Frankfurter API（ECB，免费无需 key）"""
    cached = await _get_cached("usd")
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get("https://api.frankfurter.dev/v1/latest?from=USD&to=EUR,JPY,GBP,CHF,CNY")
            if r.status_code == 200:
                data = r.json()
                result = {
                    "base": "USD",
                    "rates": data.get("rates", {}),
                    "date": data.get("date", ""),
                    "source": "frankfurter_ecb",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "_cached": False,
                }
                await _set_cached("usd", result)
                return result
    except Exception as e:
        logger.error(f"美元数据获取失败: {e}")
    
    return {"base": "USD", "rates": {}, "error": "数据获取失败", "source": "frankfurter"}


async def _fetch_treasury_yield() -> Dict[str, Any]:
    """获取 10Y 美债收益率 - FRED API（免费）"""
    cached = await _get_cached("treasury")
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
            r = await client.get(url)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                # CSV: DATE,VALUE - 取最后有效行
                for line in reversed(lines[1:]):
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] != ".":
                        yield_val = float(parts[1])
                        result = {
                            "symbol": "DGS10",
                            "name": "10-Year Treasury Yield",
                            "value": yield_val,
                            "unit": "%",
                            "date": parts[0],
                            "source": "fred",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "_cached": False,
                        }
                        await _set_cached("treasury", result)
                        return result
    except Exception as e:
        logger.error(f"美债收益率获取失败: {e}")
    
    return {"symbol": "DGS10", "value": None, "error": "数据获取失败", "source": "fred"}


async def _fetch_oil_price() -> Dict[str, Any]:
    """获取 WTI 原油价格 - FRED API"""
    cached = await _get_cached("oil")
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO"
            r = await client.get(url)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                for line in reversed(lines[1:]):
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] != ".":
                        price = float(parts[1])
                        result = {
                            "symbol": "WTI",
                            "name": "Crude Oil WTI",
                            "price": price,
                            "unit": "USD/barrel",
                            "date": parts[0],
                            "source": "fred",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "_cached": False,
                        }
                        await _set_cached("oil", result)
                        return result
    except Exception as e:
        logger.error(f"原油价格获取失败: {e}")
    
    return {"symbol": "WTI", "price": None, "error": "数据获取失败", "source": "fred"}


async def _fetch_stock_index() -> Dict[str, Any]:
    """获取 S&P 500 - FRED API"""
    cached = await _get_cached("stock")
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=SP500"
            r = await client.get(url)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                for line in reversed(lines[1:]):
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] != ".":
                        value = float(parts[1])
                        result = {
                            "symbol": "SPX",
                            "name": "S&P 500",
                            "value": value,
                            "date": parts[0],
                            "source": "fred",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "_cached": False,
                        }
                        await _set_cached("stock", result)
                        return result
    except Exception as e:
        logger.error(f"股指数据获取失败: {e}")
    
    return {"symbol": "SPX", "value": None, "error": "数据获取失败", "source": "fred"}


async def _fetch_fred_series(series_id: str, name: str, cache_key: str) -> Dict[str, Any]:
    """通用 FRED 数据获取函数"""
    cached = await _get_cached(cache_key)
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            r = await client.get(url)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                for line in reversed(lines[1:]):
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] != ".":
                        value = float(parts[1])
                        result = {
                            "symbol": series_id,
                            "name": name,
                            "value": value,
                            "date": parts[0],
                            "source": "fred",
                            "updated_at": datetime.now(timezone.utc).isoformat(),
                            "_cached": False,
                        }
                        await _set_cached(cache_key, result)
                        return result
    except Exception as e:
        logger.error(f"{name} 获取失败: {e}")
    
    return {"symbol": series_id, "name": name, "value": None, "error": "数据获取失败", "source": "fred"}


async def _fetch_fred_history(series_id: str, months: int = 36) -> list:
    """从 FRED 获取历史时间序列数据（用于图表）"""
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            r = await client.get(url)
            if r.status_code == 200:
                lines = r.text.strip().split("\n")
                data = []
                for line in lines[1:]:
                    parts = line.split(",")
                    if len(parts) >= 2 and parts[1] != ".":
                        try:
                            data.append({
                                "date": parts[0],
                                "value": float(parts[1]),
                            })
                        except (ValueError, TypeError):
                            continue
                return data[-months:] if len(data) > months else data
    except Exception as e:
        logger.error(f"FRED 历史数据 {series_id} 获取失败: {e}")
    return []


async def _fetch_fed_funds_rate() -> Dict[str, Any]:
    """联邦基金有效利率"""
    return await _fetch_fred_series("DFF", "Federal Funds Effective Rate", "fed_rate")


async def _fetch_vix() -> Dict[str, Any]:
    """VIX 恐慌指数"""
    return await _fetch_fred_series("VIXCLS", "CBOE Volatility Index (VIX)", "vix")


async def _fetch_copper() -> Dict[str, Any]:
    """铜价 (FRED)"""
    return await _fetch_fred_series("DCOPP", "Copper Price", "copper")


async def _fetch_cpi() -> Dict[str, Any]:
    """CPI 通胀数据"""
    return await _fetch_fred_series("CPIAUCSL", "Consumer Price Index", "cpi")


async def _fetch_treasury_2y() -> Dict[str, Any]:
    """2Y 美债收益率"""
    return await _fetch_fred_series("DGS2", "2-Year Treasury Yield", "treasury_2y")


async def _fetch_treasury_30y() -> Dict[str, Any]:
    """30Y 美债收益率"""
    return await _fetch_fred_series("DGS30", "30-Year Treasury Yield", "treasury_30y")


async def _fetch_treasury_5y() -> Dict[str, Any]:
    """5Y 美债收益率"""
    return await _fetch_fred_series("DGS5", "5-Year Treasury Yield", "treasury_5y")


async def _fetch_nonfarm_payrolls() -> Dict[str, Any]:
    """非农就业人数（千人）"""
    return await _fetch_fred_series("PAYEMS", "Total Nonfarm Payrolls", "nonfarm")


async def _fetch_unemployment_rate() -> Dict[str, Any]:
    """失业率"""
    return await _fetch_fred_series("UNRATE", "Unemployment Rate", "unemployment")


async def _fetch_gdp_growth() -> Dict[str, Any]:
    """实际 GDP 增长率"""
    return await _fetch_fred_series("A191RL1Q225SBEA", "Real GDP Growth Rate", "gdp")


async def _fetch_pmi() -> Dict[str, Any]:
    """ISM 制造业 PMI"""
    return await _fetch_fred_series("MANEMP", "ISM Manufacturing Employment", "pmi")


async def _fetch_ppi() -> Dict[str, Any]:
    """生产者价格指数 PPI"""
    return await _fetch_fred_series("PPIACO", "Producer Price Index", "ppi")


async def _fetch_retail_sales() -> Dict[str, Any]:
    """零售销售"""
    return await _fetch_fred_series("RSAFS", "Retail Sales", "retail")


async def _fetch_real_yield() -> Dict[str, Any]:
    """10Y TIPS 实际收益率"""
    return await _fetch_fred_series("DFII10", "10-Year TIPS Real Yield", "real_yield")


async def _fetch_credit_spread() -> Dict[str, Any]:
    """BAA 信用利差"""
    return await _fetch_fred_series("BAMLC0A4CBBB", "BAA-BBB Credit Spread", "credit_spread")


async def _fetch_dollar_index() -> Dict[str, Any]:
    """贸易加权美元指数"""
    return await _fetch_fred_series("DTWEXBGS", "Trade Weighted USD Index", "dollar_index")


async def _fetch_jobless_claims() -> Dict[str, Any]:
    """初请失业金人数"""
    return await _fetch_fred_series("ICSA", "Initial Jobless Claims", "jobless_claims")


async def _fetch_consumer_sentiment() -> Dict[str, Any]:
    """密歇根消费者信心"""
    return await _fetch_fred_series("UMCSENT", "Consumer Sentiment Index", "consumer_sentiment")


async def _fetch_silver() -> Dict[str, Any]:
    """白银价格 - gold-api.com（免费无需 key）"""
    cached = await _get_cached("silver")
    if cached:
        cached["_cached"] = True
        return cached

    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
            r = await client.get("https://api.gold-api.com/price/XAG")
            if r.status_code == 200:
                data = r.json()
                price = data.get("price")
                if price:
                    price = float(price)
                    price_per_gram = round(price / 31.1035, 2)
                    updated = data.get("updatedAt", "")[:10]
                    result = {
                        "symbol": "XAG/USD",
                        "name": "Silver",
                        "price": round(price, 2),
                        "price_per_gram_pln": None,
                        "price_per_gram_usd": price_per_gram,
                        "date": updated,
                        "source": "gold-api",
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "_cached": False,
                    }
                    await _set_cached("silver", result)
                    return result
    except Exception as e:
        logger.error(f"白银价格获取失败: {e}")
    
    return {"symbol": "XAG/USD", "name": "Silver", "price": None, "error": "数据获取失败", "source": "gold-api"}


# ── API 端点 ──────────────────────────────────────────────────


@router.get("/realtime/gold")
async def get_realtime_gold():
    """实时黄金价格"""
    data = await _fetch_gold_price()
    return success(data=data)


@router.get("/realtime/usd")
async def get_realtime_usd():
    """实时美元汇率"""
    data = await _fetch_usd_index()
    return success(data=data)


@router.get("/realtime/treasury")
async def get_realtime_treasury():
    """实时 10Y 美债收益率"""
    data = await _fetch_treasury_yield()
    return success(data=data)


@router.get("/realtime/oil")
async def get_realtime_oil():
    """实时原油价格"""
    data = await _fetch_oil_price()
    return success(data=data)


@router.get("/realtime/stock")
async def get_realtime_stock():
    """实时 S&P 500"""
    data = await _fetch_stock_index()
    return success(data=data)


@router.get("/realtime/silver")
async def get_realtime_silver():
    """实时白银价格"""
    data = await _fetch_silver()
    return success(data=data)


@router.get("/realtime/fed-rate")
async def get_realtime_fed_rate():
    """联邦基金利率"""
    data = await _fetch_fed_funds_rate()
    return success(data=data)


@router.get("/realtime/vix")
async def get_realtime_vix():
    """VIX 恐慌指数"""
    data = await _fetch_vix()
    return success(data=data)


@router.get("/realtime/copper")
async def get_realtime_copper():
    """铜价"""
    data = await _fetch_copper()
    return success(data=data)


@router.get("/realtime/treasury-curves")
async def get_realtime_treasury_curves():
    """美债收益率曲线 (2Y/10Y/30Y)"""
    import asyncio
    t2y, t10y, t30y = await asyncio.gather(
        _fetch_treasury_2y(),
        _fetch_treasury_yield(),
        _fetch_treasury_30y(),
    )
    return success(data={
        "2Y": t2y,
        "10Y": t10y,
        "30Y": t30y,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/realtime/economic")
async def get_realtime_economic():
    """经济指标汇总 (就业/GDP/PMI/失业率/通胀)"""
    import asyncio
    nonfarm, unemployment, gdp, ppi, retail = await asyncio.gather(
        _fetch_nonfarm_payrolls(),
        _fetch_unemployment_rate(),
        _fetch_gdp_growth(),
        _fetch_ppi(),
        _fetch_retail_sales(),
    )
    return success(data={
        "nonfarm": nonfarm,
        "unemployment": unemployment,
        "gdp": gdp,
        "ppi": ppi,
        "retail": retail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/realtime/economic-history")
async def get_economic_history():
    """经济指标历史趋势数据（最近 36 个月，用于图表展示）"""
    import asyncio

    indicators = {
        "nonfarm": ("PAYEMS", "非农就业", "千人"),
        "unemployment": ("UNRATE", "失业率", "%"),
        "gdp": ("A191RL1Q225SBEA", "GDP增速", "%"),
        "ppi": ("PPIACO", "PPI", "指数"),
        "retail": ("RSAFS", "零售销售", "百万美元"),
    }

    async def _fetch_one(key, series_id, name, unit):
        data = await _fetch_fred_history(series_id, months=36)
        return key, {"name": name, "unit": unit, "data": data}

    tasks = [_fetch_one(k, sid, nm, u) for k, (sid, nm, u) in indicators.items()]
    results = await asyncio.gather(*tasks)

    history = {k: v for k, v in results}
    return success(data=history)


@router.get("/realtime/financial-stress")
async def get_financial_stress():
    """金融压力指标 (VIX/实际收益率/信用利差/美元指数)"""
    import asyncio
    vix, real_yield, credit, dollar = await asyncio.gather(
        _fetch_vix(),
        _fetch_real_yield(),
        _fetch_credit_spread(),
        _fetch_dollar_index(),
    )
    return success(data={
        "vix": vix,
        "real_yield": real_yield,
        "credit_spread": credit,
        "dollar_index": dollar,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/realtime/sentiment")
async def get_sentiment():
    """市场情绪指标 (消费者信心/初请失业金)"""
    import asyncio
    sentiment, claims = await asyncio.gather(
        _fetch_consumer_sentiment(),
        _fetch_jobless_claims(),
    )
    return success(data={
        "consumer_sentiment": sentiment,
        "jobless_claims": claims,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/realtime/all")
async def get_realtime_all():
    """一次获取所有实时数据"""
    import asyncio
    gold, usd, treasury, oil, stock, silver, fed, vix = await asyncio.gather(
        _fetch_gold_price(),
        _fetch_usd_index(),
        _fetch_treasury_yield(),
        _fetch_oil_price(),
        _fetch_stock_index(),
        _fetch_silver(),
        _fetch_fed_funds_rate(),
        _fetch_vix(),
    )
    return success(data={
        "gold": gold,
        "silver": silver,
        "usd": usd,
        "treasury": treasury,
        "oil": oil,
        "stock": stock,
        "fed_rate": fed,
        "vix": vix,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@router.get("/realtime/jobs")
async def get_realtime_jobs():
    """非农就业数据"""
    data = await _fetch_nonfarm_payrolls()
    return success(data=data)


@router.get("/realtime/unemployment")
async def get_realtime_unemployment():
    """失业率"""
    data = await _fetch_unemployment_rate()
    return success(data=data)


@router.get("/realtime/gdp")
async def get_realtime_gdp():
    """GDP 增长率"""
    data = await _fetch_gdp_growth()
    return success(data=data)


@router.post("/realtime/refresh")
async def refresh_realtime():
    """强制刷新所有实时数据（清除缓存）"""
    if is_redis_available():
        try:
            r = get_redis()
            keys = [f"{CACHE_PREFIX}{k}" for k in ["gold", "silver", "usd", "treasury", "treasury_2y", "treasury_5y", "treasury_30y", "oil", "stock", "fed_rate", "vix", "copper", "cpi", "ppi", "nonfarm", "unemployment", "gdp", "retail", "real_yield", "credit_spread", "dollar_index", "jobless_claims", "consumer_sentiment"]]
            await r.delete(*keys)
        except Exception as e:
            logger.warning(f"缓存清除失败: {e}")
    
    # 重新获取
    data = await get_realtime_all()
    return data
