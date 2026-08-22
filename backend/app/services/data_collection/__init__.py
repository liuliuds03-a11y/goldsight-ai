"""
GoldSight AI V3.0 - 数据采集模块

通用数据采集框架，包含：
- BaseCollector: 采集器抽象基类
- CollectorRegistry: 采集器注册中心（开闭原则）
- DataPipeline: 采集 → 清洗 → 验证 → 入库流水线

已注册的采集器：
- GoldPriceCollector: 现货黄金价格（yfinance GC=F）
- UsdDataCollector: 美元指数（yfinance ^DXY）
- TreasuryYieldCollector: 美国 10Y 国债收益率（yfinance ^TNX）
"""

from .base_collector import BaseCollector
from .registry import CollectorRegistry
from .pipeline import DataPipeline

# 导入采集器模块以触发自动注册
from .collectors.gold_price_collector import GoldPriceCollector
from .collectors.usd_data_collector import UsdDataCollector
from .collectors.treasury_yield_collector import TreasuryYieldCollector

__all__ = [
    "BaseCollector",
    "CollectorRegistry",
    "DataPipeline",
    "GoldPriceCollector",
    "UsdDataCollector",
    "TreasuryYieldCollector",
]
