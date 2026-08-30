"""
GoldSight AI V3.0 - 美国经济数据指标采集器（多指标）

数据源：FRED（Federal Reserve Economic Data，美联储经济数据库）
    免费、无需 API Key，CSV 格式直接下载。

支持指标：
    - cpi: 城市消费者价格指数 CPIAUCSL（月度）
    - core_cpi: 核心 CPI（剔除食品和能源）CPILFESL（月度）
    - unemployment: 失业率 UNRATE（月度，%）
    - nonfarm: 非农就业人数 PAYEMS（月度，千人）
    - gdp: 实际 GDP 增长率 A191RL1Q225SBEA（季度，%）
    - ppi: 生产者价格指数 PPIACO（月度）
    - retail: 零售销售 RSAFS（月度，百万美元）

目标表：economic_indicators
数据频率：月度/季度
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

# 所有支持的 FRED 经济指标系列
FRED_ECONOMIC_SERIES = {
    "cpi": {
        "series_id": "CPIAUCSL",
        "name": "消费者价格指数",
        "unit": "index",
        "valid_range": (50, 500),
    },
    "core_cpi": {
        "series_id": "CPILFESL",
        "name": "核心CPI",
        "unit": "index",
        "valid_range": (50, 500),
    },
    "unemployment": {
        "series_id": "UNRATE",
        "name": "失业率",
        "unit": "%",
        "valid_range": (0, 30),
    },
    "nonfarm": {
        "series_id": "PAYEMS",
        "name": "非农就业",
        "unit": "千人",
        "valid_range": (50000, 300000),
    },
    "gdp": {
        "series_id": "A191RL1Q225SBEA",
        "name": "GDP增速",
        "unit": "%",
        "valid_range": (-50, 50),
    },
    "ppi": {
        "series_id": "PPIACO",
        "name": "生产者价格指数",
        "unit": "index",
        "valid_range": (50, 500),
    },
    "retail": {
        "series_id": "RSAFS",
        "name": "零售销售",
        "unit": "百万美元",
        "valid_range": (10000, 1000000),
    },
}


class EconomicIndicatorCollector(BaseCollector):
    """
    美国经济指标采集器（多指标）

    通过 FRED 公开 CSV 接口获取多种宏观经济指标的月度/季度数据，
    一次采集遍历所有指标类型，存入 economic_indicators 表。
    """

    @property
    def source_name(self) -> str:
        return "fred"

    @property
    def target_table(self) -> str:
        return "economic_indicators"

    async def fetch(self, **kwargs) -> List[Dict[str, Any]]:
        """
        从 FRED 获取所有经济指标的 CSV 数据

        kwargs:
            months: 仅保留最近 N 个月（默认 36，即 3 年）
        """
        months = kwargs.get("months", 36)
        results: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            for indicator_type, config in FRED_ECONOMIC_SERIES.items():
                series_id = config["series_id"]
                try:
                    resp = await client.get(
                        FRED_CSV_URL, params={"id": series_id}
                    )
                    resp.raise_for_status()

                    reader = csv.DictReader(io.StringIO(resp.text))
                    count = 0
                    for row in reader:
                        date_str = row.get("observation_date") or row.get("DATE", "")
                        value_str = row.get(series_id) or row.get("VALUE", "")

                        if not date_str or not value_str:
                            continue

                        try:
                            value = float(value_str)
                        except (ValueError, TypeError):
                            continue

                        # GDP 等指标可能为负值，不能简单跳过 value <= 0
                        if indicator_type in ("gdp",):
                            pass  # 允许负增长
                        elif value <= 0:
                            continue

                        results.append({
                            "date": date_str,
                            "value": value,
                            "indicator": indicator_type,
                        })
                        count += 1

                    logger.info(f"FRED {indicator_type} ({series_id}): 获取 {count} 条")

                except Exception as e:
                    logger.error(f"FRED {indicator_type} ({series_id}) 获取失败: {e}")

        # 按指标类型分组，每组只保留最近 months 条
        grouped: Dict[str, List[Dict]] = {}
        for r in results:
            grouped.setdefault(r["indicator"], []).append(r)
        trimmed: List[Dict[str, Any]] = []
        for ind, items in grouped.items():
            trimmed.extend(items[-months:])
        return trimmed

    def clean(self, raw_data: List[Any]) -> List[Dict[str, Any]]:
        """将 FRED CSV 数据转换为 economic_indicators 表记录"""
        records: List[Dict[str, Any]] = []
        # 按指标类型分别追踪，用于计算同比变化率
        by_type: Dict[str, List[Dict[str, Any]]] = {}

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
            config = FRED_ECONOMIC_SERIES.get(indicator_type, {})

            type_records = by_type.setdefault(indicator_type, [])

            # 计算同比变化率（与 12 个月前比较）
            previous_value = None
            if len(type_records) >= 12:
                previous_value = type_records[-12]["actual_value"]

            record = {
                "timestamp": ts,
                "indicator_type": indicator_type,
                "period": date_str[:7],  # 如 "2024-01"
                "actual_value": round(value, 4),
                "unit": config.get("unit", "index"),
            }

            if previous_value is not None and previous_value != 0:
                yoy_change = round(
                    (value - previous_value) / abs(previous_value) * 100, 4
                )
                record["previous_value"] = round(previous_value, 4)
                record["revised_value"] = yoy_change  # 复用字段存储同比

            type_records.append(record)
            records.append(record)

        return records

    def validate(self, record: Dict[str, Any]) -> bool:
        """验证经济指标记录（按指标类型设定合理范围）"""
        value = record.get("actual_value")
        if value is None:
            return False
        indicator_type = record.get("indicator_type", "")
        config = FRED_ECONOMIC_SERIES.get(indicator_type, {})
        low, high = config.get("valid_range", (0, 999999))
        return low <= value <= high


# 自动注册
CollectorRegistry.get_instance().register(EconomicIndicatorCollector)
