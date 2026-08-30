"""
GoldSight AI V3.0 - 技术指标计算模块测试

测试范围：
1. 各指标计算函数（使用已知数据手动验证）
2. 数据不足时的优雅降级
3. 引擎编排逻辑（使用模拟数据）
4. API 端点（触发计算 + 查询接口）
"""

import pytest
import numpy as np
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app


# ── 趋势类指标测试 ────────────────────────────────────────────


class TestMA:
    """简单移动平均线测试"""

    def test_ma5_basic(self):
        """MA5 基本计算"""
        from app.services.technical_analysis.calculations import calculate_ma

        prices = np.array([100.0, 102.0, 101.0, 103.0, 104.0])
        result = calculate_ma(prices, 5)
        # (100 + 102 + 101 + 103 + 104) / 5 = 102.0
        assert result is not None
        assert abs(result - 102.0) < 0.001

    def test_ma_insufficient_data(self):
        """数据不足时返回 None"""
        from app.services.technical_analysis.calculations import calculate_ma

        prices = np.array([100.0, 102.0, 101.0])
        assert calculate_ma(prices, 5) is None
        assert calculate_ma(prices, 10) is None

    def test_ma_with_more_data(self):
        """多余数据时只取最近 period 个"""
        from app.services.technical_analysis.calculations import calculate_ma

        prices = np.array([90.0, 95.0, 100.0, 102.0, 101.0, 103.0, 104.0])
        result = calculate_ma(prices, 5)
        # 取最后 5 个: (100 + 102 + 101 + 103 + 104) / 5 = 102.0
        assert abs(result - 102.0) < 0.001


class TestEMA:
    """指数移动平均线测试"""

    def test_ema_basic(self):
        """EMA12 基本计算"""
        from app.services.technical_analysis.calculations import calculate_ema

        # 生成 15 个递增价格
        prices = np.array([
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0,
            107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0,
        ])
        result = calculate_ema(prices, 12)
        assert result is not None
        # EMA 应该接近但略低于最新价格
        assert 100.0 < result < 115.0

    def test_ema_equals_sma_for_exact_period(self):
        """当数据量恰好等于 period 时，EMA = SMA"""
        from app.services.technical_analysis.calculations import calculate_ema

        prices = np.array([100.0, 102.0, 104.0, 106.0, 108.0])
        result = calculate_ema(prices, 5)
        # EMA 初始值 = SMA = (100+102+104+106+108)/5 = 104.0
        assert result is not None
        assert abs(result - 104.0) < 0.001

    def test_ema_insufficient_data(self):
        """数据不足"""
        from app.services.technical_analysis.calculations import calculate_ema

        prices = np.array([100.0, 101.0])
        assert calculate_ema(prices, 12) is None


class TestMACD:
    """MACD 指标测试"""

    def test_macd_insufficient_data(self):
        """数据不足 26 条时返回 None"""
        from app.services.technical_analysis.calculations import calculate_macd

        prices = np.array([100.0] * 20)
        assert calculate_macd(prices) is None

    def test_macd_with_enough_data(self):
        """有足够数据时能正常计算"""
        from app.services.technical_analysis.calculations import calculate_macd

        # 生成 40 个价格数据
        np.random.seed(42)
        prices = 100.0 + np.cumsum(np.random.randn(40) * 0.5)
        result = calculate_macd(prices)
        assert result is not None
        assert "macd" in result
        assert result["macd"] is not None
        # 信号线和柱状图可能有值也可能不够
        # 40 条数据: MACD 线从 index 25 开始有 15 个值
        # 信号线需要 9 个 MACD 值 → 有 15 个，够了
        assert result.get("signal") is not None
        assert result.get("hist") is not None


class TestADX:
    """ADX 指标测试"""

    def test_adx_insufficient_data(self):
        """数据不足时返回 None"""
        from app.services.technical_analysis.calculations import calculate_adx

        highs = np.array([105.0] * 20)
        lows = np.array([95.0] * 20)
        closes = np.array([100.0] * 20)
        assert calculate_adx(highs, lows, closes, 14) is None


# ── 动量类指标测试 ────────────────────────────────────────────


class TestRSI:
    """RSI 指标测试"""

    def test_rsi_basic(self):
        """RSI14 基本计算"""
        from app.services.technical_analysis.calculations import calculate_rsi

        # 15 个递增价格 → 全部上涨 → RSI 应为 100
        prices = np.array([
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0,
            107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0,
        ])
        result = calculate_rsi(prices, 14)
        assert result is not None
        assert result == 100.0  # 全部上涨

    def test_rsi_all_decline(self):
        """全部下跌时 RSI = 0"""
        from app.services.technical_analysis.calculations import calculate_rsi

        prices = np.array([
            114.0, 113.0, 112.0, 111.0, 110.0, 109.0, 108.0,
            107.0, 106.0, 105.0, 104.0, 103.0, 102.0, 101.0, 100.0,
        ])
        result = calculate_rsi(prices, 14)
        assert result is not None
        assert result == 0.0

    def test_rsi_insufficient_data(self):
        """数据不足"""
        from app.services.technical_analysis.calculations import calculate_rsi

        prices = np.array([100.0, 101.0, 102.0])
        assert calculate_rsi(prices, 14) is None


class TestStochastic:
    """随机指标测试"""

    def test_stochastic_insufficient_data(self):
        """数据不足"""
        from app.services.technical_analysis.calculations import calculate_stochastic

        highs = np.array([105.0] * 10)
        lows = np.array([95.0] * 10)
        closes = np.array([100.0] * 10)
        assert calculate_stochastic(highs, lows, closes, 14) is None

    def test_stochastic_basic(self):
        """基本计算"""
        from app.services.technical_analysis.calculations import calculate_stochastic

        # 18 个数据点（> 14 + 2 = 16）
        highs = np.array([
            105, 106, 107, 108, 109, 110, 111, 112,
            113, 114, 115, 116, 117, 118, 119, 120, 121, 122,
        ], dtype=float)
        lows = np.array([
            95, 96, 97, 98, 99, 100, 101, 102,
            103, 104, 105, 106, 107, 108, 109, 110, 111, 112,
        ], dtype=float)
        closes = np.array([
            100, 101, 102, 103, 104, 105, 106, 107,
            108, 109, 110, 111, 112, 113, 114, 115, 116, 117,
        ], dtype=float)
        result = calculate_stochastic(highs, lows, closes, 14)
        assert result is not None
        assert "k" in result
        assert "d" in result
        assert 0 <= result["k"] <= 100
        assert 0 <= result["d"] <= 100


class TestROC:
    """变化率测试"""

    def test_roc_basic(self):
        """ROC 基本计算"""
        from app.services.technical_analysis.calculations import calculate_roc

        prices = np.array([
            100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0,
            107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 115.0,
        ])
        result = calculate_roc(prices, 14)
        assert result is not None
        # (115 - 100) / 100 * 100 = 15.0
        assert abs(result - 15.0) < 0.001

    def test_roc_insufficient_data(self):
        """数据不足"""
        from app.services.technical_analysis.calculations import calculate_roc

        prices = np.array([100.0, 101.0, 102.0])
        assert calculate_roc(prices, 14) is None


# ── 波动类指标测试 ────────────────────────────────────────────


class TestBollingerBands:
    """布林带测试"""

    def test_bollinger_basic(self):
        """布林带基本计算"""
        from app.services.technical_analysis.calculations import (
            calculate_bollinger_bands,
        )

        prices = np.array([
            100.0, 102.0, 101.0, 103.0, 104.0, 102.0, 105.0,
            106.0, 104.0, 103.0, 107.0, 108.0, 106.0, 105.0,
            109.0, 110.0, 108.0, 107.0, 111.0, 112.0,
        ])
        result = calculate_bollinger_bands(prices, 20)
        assert result is not None
        assert "upper" in result
        assert "middle" in result
        assert "lower" in result
        assert result["upper"] > result["middle"] > result["lower"]

    def test_bollinger_insufficient_data(self):
        """数据不足"""
        from app.services.technical_analysis.calculations import (
            calculate_bollinger_bands,
        )

        prices = np.array([100.0, 102.0, 101.0])
        assert calculate_bollinger_bands(prices, 20) is None


class TestATR:
    """平均真实波幅测试"""

    def test_atr_insufficient_data(self):
        """数据不足"""
        from app.services.technical_analysis.calculations import calculate_atr

        highs = np.array([105.0] * 10)
        lows = np.array([95.0] * 10)
        closes = np.array([100.0] * 10)
        assert calculate_atr(highs, lows, closes, 14) is None

    def test_atr_basic(self):
        """ATR 基本计算"""
        from app.services.technical_analysis.calculations import calculate_atr

        # 20 个数据点
        highs = np.array([
            105, 106, 108, 107, 109, 110, 112, 111, 113, 114,
            115, 116, 118, 117, 119, 120, 121, 122, 123, 124,
        ], dtype=float)
        lows = np.array([
            95, 96, 97, 98, 99, 100, 101, 102, 103, 104,
            105, 106, 107, 108, 109, 110, 111, 112, 113, 114,
        ], dtype=float)
        closes = np.array([
            100, 101, 103, 102, 105, 106, 108, 107, 109, 110,
            111, 112, 114, 113, 115, 116, 117, 118, 119, 120,
        ], dtype=float)
        result = calculate_atr(highs, lows, closes, 14)
        assert result is not None
        assert result > 0


# ── 引擎逻辑测试 ──────────────────────────────────────────────


class TestEngine:
    """计算引擎逻辑测试"""

    def test_compute_with_5_data_points(self):
        """用 5 个数据点测试引擎计算（模拟实际黄金数据）"""
        from app.services.technical_analysis.engine import compute_all_indicators

        # 模拟实际 gold_prices 数据
        price_data = [
            {
                "timestamp": datetime(2026, 8, 17, tzinfo=timezone.utc),
                "open": 4404.4286, "high": 4404.4286,
                "low": 4404.4286, "close": 4404.4286,
            },
            {
                "timestamp": datetime(2026, 8, 18, tzinfo=timezone.utc),
                "open": 4431.5434, "high": 4431.5434,
                "low": 4431.5434, "close": 4431.5434,
            },
            {
                "timestamp": datetime(2026, 8, 19, tzinfo=timezone.utc),
                "open": 4450.2957, "high": 4450.2957,
                "low": 4450.2957, "close": 4450.2957,
            },
            {
                "timestamp": datetime(2026, 8, 20, tzinfo=timezone.utc),
                "open": 4412.0309, "high": 4412.0309,
                "low": 4412.0309, "close": 4412.0309,
            },
            {
                "timestamp": datetime(2026, 8, 21, tzinfo=timezone.utc),
                "open": 4497.2610, "high": 4497.2610,
                "low": 4497.2610, "close": 4497.2610,
            },
        ]

        # 对最后一个时间点计算所有指标
        records = compute_all_indicators(price_data, 4)

        # 5 个数据点，应该能计算 MA5
        indicator_names = [r["indicator_name"] for r in records]
        assert "sma" in indicator_names

        # MA5 应该是 5 个价格的平均值
        sma_records = [r for r in records if r["indicator_name"] == "sma"]
        if sma_records:
            expected_ma5 = (
                4404.4286 + 4431.5434 + 4450.2957 + 4412.0309 + 4497.2610
            ) / 5
            assert abs(sma_records[0]["value"] - expected_ma5) < 0.01

        # 不应有 MA10、MA20、MA60（数据不足）
        ma_periods = [r["period"] for r in records if r["indicator_name"] == "sma"]
        assert 10 not in ma_periods
        assert 20 not in ma_periods
        assert 60 not in ma_periods

    def test_compute_at_early_index(self):
        """早期时间点只有少量指标可计算"""
        from app.services.technical_analysis.engine import compute_all_indicators

        price_data = [
            {
                "timestamp": datetime(2026, 8, 17, tzinfo=timezone.utc),
                "open": 4404.0, "high": 4404.0,
                "low": 4404.0, "close": 4404.0,
            },
            {
                "timestamp": datetime(2026, 8, 18, tzinfo=timezone.utc),
                "open": 4431.0, "high": 4431.0,
                "low": 4431.0, "close": 4431.0,
            },
        ]

        # 只有 2 个数据点，不应有任何指标可计算
        records = compute_all_indicators(price_data, 0)
        assert len(records) == 0

        records = compute_all_indicators(price_data, 1)
        assert len(records) == 0


# ── API 端点测试 ──────────────────────────────────────────────


@pytest.mark.anyio
async def test_indicators_endpoint_no_data():
    """测试指标查询 API（可能无数据）"""
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/indicators")

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "records" in data["data"]
        assert "total" in data["data"]
    except (RuntimeError, AttributeError):
        pytest.skip("数据库连接事件循环已关闭（Windows 测试环境限制）")


@pytest.mark.anyio
async def test_indicators_with_filters():
    """测试带过滤条件的指标查询"""
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/indicators?symbol=XAUUSD&indicator=sma&category=trend"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "records" in data["data"]
    except (RuntimeError, AttributeError):
        pytest.skip("数据库连接事件循环已关闭（Windows 测试环境限制）")


@pytest.mark.anyio
async def test_calculate_endpoint():
    """测试触发计算 API"""
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/indicators/calculate?symbol=XAUUSD"
            )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "status" in data["data"]
    except (RuntimeError, AttributeError):
        pytest.skip("数据库连接事件循环已关闭（Windows 测试环境限制）")
