"""
GoldSight AI V3.0 - 美元指数采集器

数据源：Frankfurter API（欧洲央行汇率数据）
    - 提供每日 EUR/USD 等主要货币对汇率
    - EUR/USD 是美元指数（DXY）的核心成分（权重 57.6%）
    - 将 EUR/USD 汇率记录到 usd_data 表
目标表：usd_data
数据频率：日度

注意：当 Yahoo Finance 等数据源可达时，
可替换为提供完整 DXY 指数的采集器。
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx

from ..base_collector import BaseCollector
from ..registry import CollectorRegistry

logger = logging.getLogger(__name__)


class UsdDataCollector(BaseCollector):
    """
    美元数据采集器

    通过 Frankfurter API 获取 EUR/USD 日度汇率数据。
    Frankfurter 底层数据来自欧洲央行（ECB）。
    """

    @property
    def source_name(self) -> str:
        return "frankfurter_ecb"

    @property
    def target_table(self) -> str:
        return "usd_data"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 Frankfurter API 获取 EUR/USD 历史汇率

        kwargs:
            days: 获取最近 N 天数据（默认 5）
        """
        days = kwargs.get("days", 120)

        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days + 5)  # 多取几天确保有足够交易日

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f"https://api.frankfurter.dev/v1/{start_date.isoformat()}..{end_date.isoformat()}"
                f"?base=EUR&symbols=USD"
            )
            resp.raise_for_status()
            data = resp.json()

        # 解析时间序列数据
        rates = data.get("rates", {})
        results = []
        for date_str, rate_dict in sorted(rates.items()):
            usd_per_eur = rate_dict.get("USD")
            if usd_per_eur is not None:
                results.append({
                    "date": date_str,
                    "eur_usd": float(usd_per_eur),
                })

        return results

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将汇率数据转换为 usd_data 表记录"""
        records = []

        for item in raw_data:
            date_str = item["date"]
            try:
                ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, TypeError):
                continue

            eur_usd = item["eur_usd"]

            record = {
                "timestamp": ts,
                "pair": "EURUSD",
                "open": round(eur_usd, 6),
                "high": round(eur_usd, 6),
                "low": round(eur_usd, 6),
                "close": round(eur_usd, 6),
            }
            records.append(record)

        # 计算涨跌幅
        for i in range(1, len(records)):
            prev_close = records[i - 1]["close"]
            curr_close = records[i]["close"]
            if prev_close and prev_close != 0:
                records[i]["change_value"] = round(
                    curr_close - prev_close, 6
                )
                records[i]["change_pct"] = round(
                    records[i]["change_value"] / prev_close * 100, 4
                )

        return records

    def validate(self, record: Dict[str, Any]) -> bool:
        """验证美元数据记录"""
        if record.get("close") is None or record["close"] <= 0:
            return False
        return True


# 自动注册
CollectorRegistry.get_instance().register(UsdDataCollector)
