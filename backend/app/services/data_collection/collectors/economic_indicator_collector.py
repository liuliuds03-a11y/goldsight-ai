"""
GoldSight AI V3.0 - 美国 CPI 经济数据指标采集器

数据源：FRED（Federal Reserve Economic Data，美联储经济数据库）
    - CPIAUCSL: 美国城市消费者价格指数（CPI），月度数据
    - CSV 下载地址：https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL
    - 免费、无需 API Key
目标表：economic_indicators
数据频率：月度（FRED 返回全部历史月度数据，取最近 N 条）
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
FRED_CPI_SERIES = {
    "cpi": "CPIAUCSL",        # 城市消费者价格指数（季调）
    "core_cpi": "CPILFESL",   # 核心 CPI（剔除食品和能源）
}


class EconomicIndicatorCollector(BaseCollector):
    """
    美国 CPI 经济数据指标采集器

    通过 FRED 公开 CSV 接口获取 CPI 月度数据，
    同时采集 CPI 和核心 CPI 两个指标。
    """

    @property
    def source_name(self) -> str:
        return "fred"

    @property
    def target_table(self) -> str:
        return "economic_indicators"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 FRED 获取 CPI 数据 CSV 数据

        kwargs:
            indicator: 指标类型（默认 'cpi'，可选 'core_cpi'）
            months: 仅保留最近 N 个月（默认 36，即 3 年）
        """
        indicator = kwargs.get("indicator", "cpi")
        months = kwargs.get("months", 36)
        series_id = FRED_CPI_SERIES.get(indicator, "CPIAUCSL")

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                FRED_CSV_URL, params={"id": series_id}
            )
            resp.raise_for_status()

        csv_text = resp.text
        reader = csv.DictReader(io.StringIO(csv_text))

        results = []
        for row in reader:
            date_str = row.get("observation_date") or row.get("DATE", "")
            value_str = row.get(series_id) or row.get("VALUE", "")

            if not date_str or not value_str:
                continue

            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            if value <= 0:
                continue

            results.append({
                "date": date_str,
                "value": value,
                "indicator": indicator,
            })

        # 仅保留最近 N 条（月度数据）
        results = results[-months:] if len(results) > months else results
        return results

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将 FRED CSV 数据转换为 economic_indicators 表记录"""
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
            indicator_type = item["indicator"]

            # 计算同比变化率（与 12 个月前比较）
            previous_value = None
            if len(records) >= 12:
                previous_value = records[-12]["actual_value"]

            record = {
                "timestamp": ts,
                "indicator_type": indicator_type,
                "period": date_str[:7],  # 如 "2024-01"
                "actual_value": round(value, 4),
                "unit": "index",
            }

            if previous_value is not None and previous_value != 0:
                yoy_change = round(
                    (value - previous_value) / previous_value * 100, 4
                )
                record["previous_value"] = round(previous_value, 4)
                record["revised_value"] = yoy_change  # 复用字段存储同比

            records.append(record)

        return records

    def validate(self, record: Dict[str, Any]) -> bool:
        """验证 CPI 记录"""
        value = record.get("actual_value")
        if value is None or value <= 0:
            return False
        # CPI 在合理范围内（50 ~ 500）
        if value < 50 or value > 500:
            return False
        return True


# 自动注册
CollectorRegistry.get_instance().register(EconomicIndicatorCollector)
