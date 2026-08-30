"""
GoldSight AI V3.0 - VIX 波动率指数采集器

数据源：FRED（Federal Reserve Economic Data，美联储经济数据库）
    - VIXCLS: CBOE 波动率指数（VIX）
    - CSV 下载地址：https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS
    - 免费、无需 API Key
目标表：stock_market
数据频率：日度（工作日）

说明：VIX 是衡量 S&P 500 期权隐含波动率的指标，常被称为"恐慌指数"。
VIX 走高通常意味着市场恐慌情绪上升，对黄金价格有正向影响。
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx

from ..base_collector import BaseCollector
from ..registry import CollectorRegistry

logger = logging.getLogger(__name__)

FRED_CSV_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
FRED_VIX_SERIES = "VIXCLS"


class VixCollector(BaseCollector):
    """
    VIX 波动率指数采集器

    通过 FRED 公开 CSV 接口获取 VIX 日度数据。
    """

    @property
    def source_name(self) -> str:
        return "fred"

    @property
    def target_table(self) -> str:
        return "stock_market"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 FRED 获取 VIX 指数 CSV 数据

        kwargs:
            days: 仅保留最近 N 天（默认 120）
        """
        days = kwargs.get("days", 120)

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                FRED_CSV_URL, params={"id": FRED_VIX_SERIES}
            )
            resp.raise_for_status()

        csv_text = resp.text
        reader = csv.DictReader(io.StringIO(csv_text))

        results = []
        for row in reader:
            date_str = row.get("observation_date") or row.get("DATE", "")
            value_str = row.get(FRED_VIX_SERIES) or row.get("VALUE", "")

            if not date_str or not value_str:
                continue

            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            if value < 0:
                continue

            results.append({
                "date": date_str,
                "value": value,
            })

        # 仅保留最近 N 条
        results = results[-days:] if len(results) > days else results
        return results

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将 FRED CSV 数据转换为 stock_market 表记录"""
        records = []

        for item in raw_data:
            date_str = item["date"]
            try:
                ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, TypeError):
                continue

            value = item["value"]

            record = {
                "timestamp": ts,
                "index_symbol": "VIX",
                "open": round(value, 4),
                "high": round(value, 4),
                "low": round(value, 4),
                "close": round(value, 4),
            }
            records.append(record)

        # 计算涨跌幅
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
        """验证 VIX 记录"""
        close = record.get("close")
        if close is None or close < 0:
            return False
        # VIX 在合理范围内（0 ~ 100）
        if close > 100:
            return False
        return True


# 自动注册
CollectorRegistry.get_instance().register(VixCollector)
