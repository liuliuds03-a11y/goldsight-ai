"""
GoldSight AI V3.0 - 数据采集器集合

每个采集器独立实现，导入时自动注册到 CollectorRegistry。
新增数据源只需在此目录添加新文件并继承 BaseCollector。
"""

from .gold_price_collector import GoldPriceCollector
from .usd_data_collector import UsdDataCollector
from .treasury_yield_collector import TreasuryYieldCollector

__all__ = [
    "GoldPriceCollector",
    "UsdDataCollector",
    "TreasuryYieldCollector",
]
