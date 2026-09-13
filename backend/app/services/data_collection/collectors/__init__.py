"""
GoldSight AI V3.0 - 数据采集器集合

每个采集器独立实现，导入时自动注册到 CollectorRegistry。
新增数据源只需在此目录添加新文件并继承 BaseCollector。
"""

from .gold_price_collector import GoldPriceCollector
from .usd_data_collector import UsdDataCollector
from .treasury_yield_collector import TreasuryYieldCollector
from .treasury_yield_2y_collector import TreasuryYield2YCollector
from .oil_price_collector import OilPriceCollector
from .stock_market_collector import StockMarketCollector
from .economic_indicator_collector import EconomicIndicatorCollector
from .vix_collector import VixCollector
from .silver_price_collector import SilverPriceCollector

__all__ = [
    "GoldPriceCollector",
    "UsdDataCollector",
    "TreasuryYieldCollector",
    "TreasuryYield2YCollector",
    "OilPriceCollector",
    "StockMarketCollector",
    "EconomicIndicatorCollector",
    "VixCollector",
    "SilverPriceCollector",
]
