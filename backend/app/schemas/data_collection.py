"""
GoldSight AI V3.0 - 数据采集相关 Pydantic 模型

用于 API 请求参数和响应格式。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── 请求参数 ──────────────────────────────────────────────────


class DataQueryParams(BaseModel):
    """数据查询通用参数"""
    start_date: Optional[datetime] = Field(
        None, description="起始日期（ISO 格式）"
    )
    end_date: Optional[datetime] = Field(
        None, description="结束日期（ISO 格式）"
    )
    limit: int = Field(50, ge=1, le=1000, description="返回条数上限")
    offset: int = Field(0, ge=0, description="偏移量")
    source: Optional[str] = Field(None, description="按数据源过滤")


# ── 响应模型 ──────────────────────────────────────────────────


class GoldPriceRecord(BaseModel):
    """黄金价格记录"""
    id: int
    timestamp: datetime
    price_type: str
    symbol: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    change_value: Optional[float] = None
    change_pct: Optional[float] = None
    volume: Optional[int] = None
    source: str
    collected_at: datetime
    quality_status: str


class UsdDataRecord(BaseModel):
    """美元数据记录"""
    id: int
    timestamp: datetime
    pair: str
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    change_value: Optional[float] = None
    change_pct: Optional[float] = None
    source: str
    collected_at: datetime
    quality_status: str


class TreasuryYieldRecord(BaseModel):
    """国债收益率记录"""
    id: int
    timestamp: datetime
    maturity: str
    yield_value: Optional[float] = Field(None, alias="yield")
    real_yield: Optional[float] = None
    spread_to_10y: Optional[float] = None
    source: str
    collected_at: datetime
    quality_status: str

    class Config:
        populate_by_name = True


class CollectorStatus(BaseModel):
    """采集器状态信息"""
    name: str
    source: str
    target_table: str
    status: str


class CollectionResult(BaseModel):
    """采集执行结果"""
    collector: str
    source: str
    target_table: str
    status: str
    records_fetched: int
    records_cleaned: int
    records_valid: int
    records_stored: int
    errors: List[str] = []
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
