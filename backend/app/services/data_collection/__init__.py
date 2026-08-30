"""
GoldSight AI V3.0 - 数据采集模块

通用数据采集框架，包含：
- BaseCollector: 采集器抽象基类
- CollectorRegistry: 采集器注册中心（开闭原则）
- DataPipeline: 采集 → 清洗 → 验证 → 入库流水线

已注册的采集器：
- GoldPriceCollector: 现货黄金价格（NBP + Frankfurter）
- UsdDataCollector: 美元指数 EUR/USD（Frankfurter/ECB）
- TreasuryYieldCollector: 美国 10Y 国债收益率（FRED）
- TreasuryYield2YCollector: 美国 2Y 国债收益率（FRED）
- OilPriceCollector: WTI 原油价格（FRED）
- StockMarketCollector: S&P 500 指数（FRED）
- EconomicIndicatorCollector: 美国 CPI 指标（FRED）
- VixCollector: VIX 波动率指数（FRED）
"""

from .base_collector import BaseCollector
from .registry import CollectorRegistry
from .pipeline import DataPipeline

# 导入采集器模块以触发自动注册
from .collectors.gold_price_collector import GoldPriceCollector
from .collectors.usd_data_collector import UsdDataCollector
from .collectors.treasury_yield_collector import TreasuryYieldCollector
from .collectors.treasury_yield_2y_collector import TreasuryYield2YCollector
from .collectors.oil_price_collector import OilPriceCollector
from .collectors.stock_market_collector import StockMarketCollector
from .collectors.economic_indicator_collector import EconomicIndicatorCollector
from .collectors.vix_collector import VixCollector

__all__ = [
    "BaseCollector",
    "CollectorRegistry",
    "DataPipeline",
    "GoldPriceCollector",
    "UsdDataCollector",
    "TreasuryYieldCollector",
    "TreasuryYield2YCollector",
    "OilPriceCollector",
    "StockMarketCollector",
    "EconomicIndicatorCollector",
    "VixCollector",
]
