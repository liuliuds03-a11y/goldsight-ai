"""
GoldSight AI V3.0 - 分析模块 Pydantic 模型

用于跨市场关联分析和宏观面分析的请求/响应格式。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── 分析因素 ──────────────────────────────────────────────────


class AnalysisFactor(BaseModel):
    """单个分析因素"""
    name: str = Field(..., description="因素名称")
    impact: str = Field(..., description="影响方向: 利多/利空/中性")
    weight: float = Field(..., ge=0.0, le=1.0, description="权重")
    evidence: str = Field(..., description="依据说明")
    score: int = Field(..., ge=-100, le=100, description="因素评分")


class AnalysisDataRange(BaseModel):
    """分析数据时间范围"""
    start: Optional[str] = Field(None, description="起始日期")
    end: Optional[str] = Field(None, description="结束日期")


# ── 分析结果 ──────────────────────────────────────────────────


class AnalysisResult(BaseModel):
    """分析结果"""
    analysis_type: str = Field(
        ..., description="分析类型: market_correlation / macro"
    )
    timestamp: str = Field(..., description="分析时间")
    conclusion: str = Field(..., description="结论: 利多/利空/中性")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    score: int = Field(..., ge=-100, le=100, description="综合评分")
    factors: List[AnalysisFactor] = Field(default=[], description="各因素分析")
    data_range: AnalysisDataRange = Field(..., description="数据时间范围")
    source: str = Field(default="market_macro_agent", description="分析来源")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="附加信息")


# ── 综合摘要 ──────────────────────────────────────────────────


class AnalysisSummary(BaseModel):
    """综合摘要（市场+宏观合并）"""
    timestamp: str = Field(..., description="摘要生成时间")
    market_analysis: Optional[AnalysisResult] = Field(
        None, description="跨市场关联分析结果"
    )
    macro_analysis: Optional[AnalysisResult] = Field(
        None, description="宏观面分析结果"
    )
    overall_conclusion: str = Field(..., description="综合结论")
    overall_score: int = Field(..., ge=-100, le=100, description="综合评分")
    overall_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="综合置信度"
    )
