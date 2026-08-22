"""
GoldSight AI V3.0 - 现货黄金价格采集器

数据源：NBP（波兰国家银行）公开 API
    - 提供每日黄金定价（PLN/克）
    - 通过 Frankfurter API 获取 PLN/USD 汇率进行换算
    - 换算公式：USD/盎司 = PLN/克 × 31.1035 克/盎司 ÷ PLN/USD 汇率
目标表：gold_prices
数据频率：日K（仅收盘价，NBP 不提供 OHLCV）

注意：数据源设计为可替换。当 Yahoo Finance 等数据源可达时，
可无缝替换为提供更完整 OHLCV 数据的采集器。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from ..base_collector import BaseCollector
from ..registry import CollectorRegistry

logger = logging.getLogger(__name__)

# 1 金衡盎司 = 31.1035 克
TROY_OUNCE_GRAMS = 31.1035


class GoldPriceCollector(BaseCollector):
    """
    现货黄金价格采集器

    通过 NBP API 获取黄金定价（PLN/克），
    结合 Frankfurter 汇率转换为 USD/盎司。
    """

    @property
    def source_name(self) -> str:
        return "nbp_frankfurter"

    @property
    def target_table(self) -> str:
        return "gold_prices"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 NBP API 获取黄金价格数据，从 Frankfurter 获取汇率

        kwargs:
            days: 获取最近 N 天数据（默认 5）
        """
        days = kwargs.get("days", 5)

        async with httpx.AsyncClient(timeout=20) as client:
            # 获取黄金价格（PLN/克）
            gold_resp = await client.get(
                f"https://api.nbp.pl/api/cenyzlota/last/{days}/?format=json"
            )
            gold_resp.raise_for_status()
            gold_data = gold_resp.json()

            # 获取 PLN/USD 汇率
            fx_resp = await client.get(
                "https://api.frankfurter.dev/v1/latest?base=USD&symbols=PLN"
            )
            fx_resp.raise_for_status()
            fx_data = fx_resp.json()

        pln_per_usd = fx_data["rates"].get("PLN")
        if pln_per_usd is None or pln_per_usd == 0:
            raise ValueError("无法获取 PLN/USD 汇率")

        # 合并数据
        results = []
        for item in gold_data:
            results.append({
                "date": item["data"],
                "price_pln_gram": float(item["cena"]),
                "pln_per_usd": pln_per_usd,
            })

        return results

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将 NBP 数据转换为 gold_prices 表记录"""
        records = []

        for item in raw_data:
            date_str = item["date"]
            try:
                ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, TypeError):
                continue

            pln_per_gram = item["price_pln_gram"]
            pln_per_usd = item["pln_per_usd"]

            # 转换为 USD/盎司
            usd_per_ounce = round(
                pln_per_gram * TROY_OUNCE_GRAMS / pln_per_usd, 4
            )

            record = {
                "timestamp": ts,
                "price_type": "spot",
                "symbol": "XAUUSD",
                "open": usd_per_ounce,
                "high": usd_per_ounce,
                "low": usd_per_ounce,
                "close": usd_per_ounce,
            }
            records.append(record)

        # 计算涨跌幅（基于相邻记录）
        for i in range(1, len(records)):
            prev_close = records[i - 1]["close"]
            curr_close = records[i]["close"]
            if prev_close and prev_close != 0:
                records[i]["change_value"] = round(
                    curr_close - prev_close, 4
                )
                records[i]["change_pct"] = round(
                    records[i]["change_value"] / prev_close * 100, 4
                )

        return records

    def validate(self, record: Dict[str, Any]) -> bool:
        """验证黄金价格记录"""
        if record.get("close") is None or record["close"] <= 0:
            return False
        return True


# 自动注册
CollectorRegistry.get_instance().register(GoldPriceCollector)
