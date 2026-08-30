"""
GoldSight AI V3.0 - 美国 2 年期国债收益率采集器

数据源：FRED（Federal Reserve Economic Data，美联储经济数据库）
    - DGS2: 美国 2 年期国债恒定到期收益率
    - CSV 下载地址：https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS2
    - 免费、无需 API Key
目标表：treasury_yields
数据频率：日度

说明：与现有 10Y 国债收益率采集器配合，提供收益率曲线数据。
2Y-10Y 利差（收益率曲线倒挂）是重要的经济衰退信号，对黄金价格有显著影响。
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
FRED_SERIES = {
    "2Y": "DGS2",    # 2 年期国债收益率
}


class TreasuryYield2YCollector(BaseCollector):
    """
    美国 2 年期国债收益率采集器

    通过 FRED 公开 CSV 接口获取 2 年期国债收益率数据。
    """

    @property
    def source_name(self) -> str:
        return "fred"

    @property
    def target_table(self) -> str:
        return "treasury_yields"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 FRED 获取 2 年期国债收益率 CSV 数据

        kwargs:
            maturity: 期限（默认 '2Y'）
            days: 仅保留最近 N 天（默认 120）
        """
        maturity = kwargs.get("maturity", "2Y")
        days = kwargs.get("days", 120)
        series_id = FRED_SERIES.get(maturity, "DGS2")

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            resp = await client.get(
                FRED_CSV_URL, params={"id": series_id}
            )
            resp.raise_for_status()

        csv_text = resp.text
        reader = csv.DictReader(io.StringIO(csv_text))

        results = []
        for row in reader:
            date_str = row.get("observation_date", "")
            value_str = row.get(series_id, "")

            if not date_str or not value_str:
                continue

            try:
                value = float(value_str)
            except (ValueError, TypeError):
                continue

            results.append({
                "date": date_str,
                "yield": value,
                "maturity": maturity,
            })

        # 仅保留最近 N 条
        results = results[-days:] if len(results) > days else results
        return results

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将 FRED CSV 数据转换为 treasury_yields 表记录"""
        records = []

        for item in raw_data:
            date_str = item["date"]
            try:
                ts = datetime.strptime(date_str, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc
                )
            except (ValueError, TypeError):
                continue

            yield_value = item["yield"]

            record = {
                "timestamp": ts,
                "maturity": item["maturity"],
                "yield": round(yield_value, 4),
            }
            records.append(record)

        return records

    def validate(self, record: Dict[str, Any]) -> bool:
        """验证国债收益率记录"""
        y = record.get("yield")
        if y is None:
            return False
        # 收益率在合理范围内（-10% ~ 20%）
        if y < -10 or y > 20:
            return False
        return True


# 自动注册
CollectorRegistry.get_instance().register(TreasuryYield2YCollector)
