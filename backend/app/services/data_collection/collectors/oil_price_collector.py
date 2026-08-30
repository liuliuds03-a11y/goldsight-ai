"""
GoldSight AI V3.0 - 原油价格采集器

数据源：FRED（Federal Reserve Economic Data，美联储经济数据库）
    - DCOILWTICO: WTI 原油现货价格（美元/桶）
    - CSV 下载地址：https://fred.stlouisfed.org/graph/fredgraph.csv?id=DCOILWTICO
    - 免费、无需 API Key
目标表：oil_data
数据频率：日度（工作日）
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
FRED_OIL_SERIES = {
    "WTI": "DCOILWTICO",   # WTI 原油现货价格
}


class OilPriceCollector(BaseCollector):
    """
    WTI 原油价格采集器

    通过 FRED 公开 CSV 接口获取 WTI 原油日度价格数据。
    """

    @property
    def source_name(self) -> str:
        return "fred"

    @property
    def target_table(self) -> str:
        return "oil_data"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 FRED 获取 WTI 原油价格 CSV 数据

        kwargs:
            oil_type: 原油类型（默认 'WTI'）
            days: 仅保留最近 N 天（默认 120）
        """
        oil_type = kwargs.get("oil_type", "WTI")
        days = kwargs.get("days", 120)
        series_id = FRED_OIL_SERIES.get(oil_type, "DCOILWTICO")

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                FRED_CSV_URL, params={"id": series_id}
            )
            resp.raise_for_status()

        csv_text = resp.text
        reader = csv.DictReader(io.StringIO(csv_text))

        results = []
        for row in reader:
            # 兼容 FRED 两种 CSV 格式
            date_str = row.get("observation_date") or row.get("DATE", "")
            value_str = row.get(series_id) or row.get("VALUE", "")

            if not date_str or not value_str:
                continue

            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            # FRED 对缺失数据可能返回 '.'
            if value <= 0:
                continue

            results.append({
                "date": date_str,
                "price": value,
                "oil_type": oil_type.lower(),
            })

        # 仅保留最近 N 条
        results = results[-days:] if len(results) > days else results
        return results

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将 FRED CSV 数据转换为 oil_data 表记录"""
        records = []

        for item in raw_data:
            date_str = item["date"]
            try:
                ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, TypeError):
                continue

            price = item["price"]

            record = {
                "timestamp": ts,
                "oil_type": item["oil_type"],
                "open": round(price, 2),
                "high": round(price, 2),
                "low": round(price, 2),
                "close": round(price, 2),
            }
            records.append(record)

        # 计算涨跌幅
        for i in range(1, len(records)):
            prev_close = records[i - 1]["close"]
            curr_close = records[i]["close"]
            if prev_close and prev_close != 0:
                records[i]["change_value"] = round(
                    curr_close - prev_close, 2
                )
                records[i]["change_pct"] = round(
                    records[i]["change_value"] / prev_close * 100, 4
                )

        return records

    def validate(self, record: Dict[str, Any]) -> bool:
        """验证原油价格记录"""
        close = record.get("close")
        if close is None or close <= 0:
            return False
        # WTI 原油价格在合理范围内（$1 ~ $300）
        if close < 1 or close > 300:
            return False
        return True


# 自动注册
CollectorRegistry.get_instance().register(OilPriceCollector)
