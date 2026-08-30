"""
GoldSight AI V3.0 - 跨市场关联与宏观分析模块

包含：
- market_engine: 跨市场关联分析（黄金 vs 美元/美债/原油/美股/VIX）
- macro_engine: 宏观面分析（通胀/利率/综合评分）
"""

from .market_engine import run_market_analysis
from .macro_engine import run_macro_analysis

__all__ = ["run_market_analysis", "run_macro_analysis"]
