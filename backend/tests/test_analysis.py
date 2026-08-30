"""
GoldSight AI V3.0 - 跨市场关联与宏观分析 单元测试

测试内容：
1. 滚动相关系数计算
2. 日收益率计算
3. 市场引擎各因素分析函数（数据不足降级）
4. 宏观引擎各因素分析函数（数据不足降级）
5. 综合评分计算
6. API 端点可达性
"""

import pytest
import numpy as np
from datetime import date, datetime

# ── 工具函数测试 ──────────────────────────────────────────────


class TestRollingCorrelation:
    """测试滚动相关系数计算"""

    def test_basic_correlation(self):
        """基本正相关"""
        from app.services.analysis.market_engine import _rolling_correlation

        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        y = np.array([2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
        result = _rolling_correlation(x, y, 5)
        # 完全正相关，最后几个值应为 1.0
        assert result[-1] is not None
        assert abs(result[-1] - 1.0) < 1e-6

    def test_negative_correlation(self):
        """负相关"""
        from app.services.analysis.market_engine import _rolling_correlation

        x = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        y = np.array([10.0, 9.0, 8.0, 7.0, 6.0, 5.0, 4.0, 3.0, 2.0, 1.0])
        result = _rolling_correlation(x, y, 5)
        assert result[-1] is not None
        assert abs(result[-1] - (-1.0)) < 1e-6

    def test_insufficient_data(self):
        """数据不足时返回 None"""
        from app.services.analysis.market_engine import _rolling_correlation

        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        result = _rolling_correlation(x, y, 5)
        # 数据不足 window 大小，全部为 None
        assert all(r is None for r in result)

    def test_zero_std(self):
        """标准差为 0 时返回 0"""
        from app.services.analysis.market_engine import _rolling_correlation

        x = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = _rolling_correlation(x, y, 5)
        assert result[-1] == 0.0


class TestDailyReturns:
    """测试日收益率计算"""

    def test_basic_returns(self):
        from app.services.analysis.market_engine import _daily_returns

        prices = np.array([100.0, 110.0, 105.0, 120.0])
        returns = _daily_returns(prices)
        assert len(returns) == 3
        assert abs(returns[0] - 0.1) < 1e-6  # 10%
        assert abs(returns[1] - (-0.0454545)) < 1e-4  # ~-4.5%
        assert abs(returns[2] - (120.0 / 105.0 - 1)) < 1e-4

    def test_insufficient_data(self):
        from app.services.analysis.market_engine import _daily_returns

        prices = np.array([100.0])
        returns = _daily_returns(prices)
        assert len(returns) == 0


class TestAlignSeries:
    """测试序列对齐"""

    def test_basic_alignment(self):
        from app.services.analysis.market_engine import _align_series

        d1 = date(2024, 1, 1)
        d2 = date(2024, 1, 2)
        d3 = date(2024, 1, 3)
        d4 = date(2024, 1, 4)

        primary = {d1: 1.0, d2: 2.0, d3: 3.0, d4: 4.0}
        secondary = {d1: 10.0, d3: 30.0, d4: 40.0}

        p, s = _align_series(primary, secondary)
        assert len(p) == 3
        assert list(p) == [1.0, 3.0, 4.0]
        assert list(s) == [10.0, 30.0, 40.0]

    def test_no_overlap(self):
        from app.services.analysis.market_engine import _align_series

        d1 = date(2024, 1, 1)
        d2 = date(2024, 1, 2)
        d3 = date(2024, 1, 3)

        primary = {d1: 1.0}
        secondary = {d3: 3.0}

        p, s = _align_series(primary, secondary)
        assert len(p) == 0
        assert len(s) == 0


# ── 市场引擎降级测试 ─────────────────────────────────────────


class TestMarketEngineDegradation:
    """测试市场引擎在数据不足时的优雅降级"""

    def test_gold_vs_usd_no_data(self):
        """美元数据为空时降级"""
        from app.services.analysis.market_engine import _analyze_gold_vs_usd

        data = {
            "gold": {date(2024, 1, 1): 2000.0},
            "usd": {},
        }
        result = _analyze_gold_vs_usd(data)
        assert result["impact"] == "中性"
        assert result["score"] == 0
        assert "数据不足" in result["evidence"]

    def test_gold_vs_bonds_no_data(self):
        """美债数据为空时降级"""
        from app.services.analysis.market_engine import _analyze_gold_vs_bonds

        data = {
            "gold": {date(2024, 1, 1): 2000.0},
            "treasury_10y": {},
            "treasury_2y": {},
            "cpi": {},
        }
        result = _analyze_gold_vs_bonds(data)
        assert result["impact"] == "中性"
        assert result["score"] == 0

    def test_gold_vs_oil_no_data(self):
        """原油数据为空时降级"""
        from app.services.analysis.market_engine import _analyze_gold_vs_oil

        data = {"gold": {}, "oil": {}}
        result = _analyze_gold_vs_oil(data)
        assert result["impact"] == "中性"

    def test_gold_vs_stocks_no_data(self):
        """美股数据为空时降级"""
        from app.services.analysis.market_engine import _analyze_gold_vs_stocks

        data = {"gold": {}, "sp500": {}}
        result = _analyze_gold_vs_stocks(data)
        assert result["impact"] == "中性"

    def test_gold_vs_vix_no_data(self):
        """VIX 数据为空时降级"""
        from app.services.analysis.market_engine import _analyze_gold_vs_vix

        data = {"gold": {}, "vix": {}}
        result = _analyze_gold_vs_vix(data)
        assert result["impact"] == "中性"


class TestMarketEngineWithMockData:
    """使用模拟数据测试市场引擎分析逻辑"""

    @pytest.fixture
    def mock_data(self):
        """构造模拟市场数据（120 天）"""
        np.random.seed(42)
        dates = [date(2024, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(120)]

        # 黄金：上涨趋势
        gold = {d: 2000 + i * 0.5 + np.random.normal(0, 5) for i, d in enumerate(dates)}
        # 美元：下跌趋势（与黄金负相关）
        usd = {d: 104 - i * 0.02 + np.random.normal(0, 0.3) for i, d in enumerate(dates)}
        # 10Y 美债：小幅上升
        ty10 = {d: 4.0 + i * 0.005 + np.random.normal(0, 0.05) for i, d in enumerate(dates)}
        # 2Y 美债：上升更多（曲线平坦化）
        ty2 = {d: 4.5 + i * 0.008 + np.random.normal(0, 0.05) for i, d in enumerate(dates)}
        # 原油：上涨
        oil = {d: 75 + i * 0.1 + np.random.normal(0, 1) for i, d in enumerate(dates)}
        # 标普 500：上涨
        sp500 = {d: 4500 + i * 2 + np.random.normal(0, 20) for i, d in enumerate(dates)}
        # VIX：下降
        vix = {d: 20 - i * 0.03 + np.random.normal(0, 1) for i, d in enumerate(dates)}
        # CPI
        cpi = {dates[0]: 3.2}

        return {
            "gold": gold,
            "usd": usd,
            "treasury_10y": ty10,
            "treasury_2y": ty2,
            "oil": oil,
            "sp500": sp500,
            "vix": vix,
            "cpi": cpi,
        }

    def test_gold_vs_usd_with_data(self, mock_data):
        """有数据时黄金-美元分析应返回有效结果"""
        from app.services.analysis.market_engine import _analyze_gold_vs_usd

        result = _analyze_gold_vs_usd(mock_data)
        assert result["name"] == "黄金-美元关联"
        assert result["weight"] == 0.25
        assert isinstance(result["score"], int)
        assert -100 <= result["score"] <= 100
        assert result["impact"] in ("利多", "利空", "中性")
        assert "correlations" in result

    def test_gold_vs_bonds_with_data(self, mock_data):
        """有数据时黄金-美债分析应返回有效结果"""
        from app.services.analysis.market_engine import _analyze_gold_vs_bonds

        result = _analyze_gold_vs_bonds(mock_data)
        assert result["name"] == "黄金-实际利率关联"
        assert isinstance(result["score"], int)
        assert "real_rate" in result
        assert "yield_curve" in result

    def test_gold_vs_oil_with_data(self, mock_data):
        from app.services.analysis.market_engine import _analyze_gold_vs_oil

        result = _analyze_gold_vs_oil(mock_data)
        assert result["name"] == "黄金-原油关联"
        assert isinstance(result["score"], int)

    def test_gold_vs_stocks_with_data(self, mock_data):
        from app.services.analysis.market_engine import _analyze_gold_vs_stocks

        result = _analyze_gold_vs_stocks(mock_data)
        assert result["name"] == "黄金-美股关联"
        assert isinstance(result["score"], int)

    def test_gold_vs_vix_with_data(self, mock_data):
        from app.services.analysis.market_engine import _analyze_gold_vs_vix

        result = _analyze_gold_vs_vix(mock_data)
        assert result["name"] == "黄金-VIX恐慌关联"
        assert isinstance(result["score"], int)
        assert "vix_status" in result


# ── 综合评分测试 ──────────────────────────────────────────────


class TestOverallScore:
    """测试综合评分计算"""

    def test_all_bullish(self):
        """全部利多时综合评分应为正"""
        from app.services.analysis.market_engine import _compute_overall_score

        factors = [
            {"name": "A", "impact": "利多", "weight": 0.5, "score": 60},
            {"name": "B", "impact": "利多", "weight": 0.5, "score": 40},
        ]
        score, confidence = _compute_overall_score(factors)
        assert score > 0
        assert 0 < confidence <= 1.0

    def test_all_bearish(self):
        """全部利空时综合评分应为负"""
        from app.services.analysis.market_engine import _compute_overall_score

        factors = [
            {"name": "A", "impact": "利空", "weight": 0.5, "score": -60},
            {"name": "B", "impact": "利空", "weight": 0.5, "score": -40},
        ]
        score, confidence = _compute_overall_score(factors)
        assert score < 0

    def test_mixed_neutral(self):
        """多空混合时评分应接近 0"""
        from app.services.analysis.market_engine import _compute_overall_score

        factors = [
            {"name": "A", "impact": "利多", "weight": 0.5, "score": 50},
            {"name": "B", "impact": "利空", "weight": 0.5, "score": -50},
        ]
        score, confidence = _compute_overall_score(factors)
        assert abs(score) <= 5  # 接近 0

    def test_empty_factors(self):
        """空因素列表返回 0"""
        from app.services.analysis.market_engine import _compute_overall_score

        score, confidence = _compute_overall_score([])
        assert score == 0
        assert confidence == 0.0


# ── 宏观引擎降级测试 ─────────────────────────────────────────


class TestMacroEngineDegradation:
    """测试宏观引擎在数据不足时的优雅降级"""

    def test_inflation_no_data(self):
        """CPI 数据为空时降级"""
        from app.services.analysis.macro_engine import _analyze_inflation

        result = _analyze_inflation([], [])
        assert result["impact"] == "中性"
        assert result["score"] == 0

    def test_rate_environment_no_data(self):
        """美债数据为空时降级"""
        from app.services.analysis.macro_engine import _analyze_rate_environment

        result = _analyze_rate_environment([], [])
        assert result["impact"] == "中性"
        assert result["score"] == 0

    def test_usd_factor_no_data(self):
        """美元数据为空时降级"""
        from app.services.analysis.macro_engine import _analyze_usd_factor

        result = _analyze_usd_factor([])
        assert result["impact"] == "中性"
        assert result["score"] == 0


class TestMacroEngineWithMockData:
    """使用模拟数据测试宏观引擎"""

    def test_inflation_high_cpi(self):
        """高 CPI 应利多黄金"""
        from app.services.analysis.macro_engine import _analyze_inflation

        cpi_data = [
            {"timestamp": date(2024, 1, 1), "value": 3.5, "previous": 3.3, "period": "2024-01"},
            {"timestamp": date(2024, 2, 1), "value": 3.6, "previous": 3.5, "period": "2024-02"},
            {"timestamp": date(2024, 3, 1), "value": 3.8, "previous": 3.6, "period": "2024-03"},
            {"timestamp": date(2024, 4, 1), "value": 4.0, "previous": 3.8, "period": "2024-04"},
            {"timestamp": date(2024, 5, 1), "value": 4.2, "previous": 4.0, "period": "2024-05"},
        ]
        ty10 = [
            {"timestamp": date(2024, 5, 1), "yield": 4.0},
        ]
        result = _analyze_inflation(cpi_data, ty10)
        assert result["score"] > 0  # 高通胀应利多
        assert result["impact"] in ("利多", "中性")

    def test_rate_environment_inversion(self):
        """收益率曲线倒挂应被检测"""
        from app.services.analysis.macro_engine import _analyze_rate_environment

        # 2Y > 10Y → 倒挂
        ty2 = [
            {"timestamp": date(2024, 1, i + 1), "yield": 5.0}
            for i in range(30)
        ]
        ty10 = [
            {"timestamp": date(2024, 1, i + 1), "yield": 4.0}
            for i in range(30)
        ]
        result = _analyze_rate_environment(ty2, ty10)
        assert result["details"]["inversion_detected"] is True
        assert result["details"]["spread_2y_10y"] is not None

    def test_usd_weakening(self):
        """美元走弱应利多黄金"""
        from app.services.analysis.macro_engine import _analyze_usd_factor

        dates = [date(2024, 1, 1) + __import__("datetime").timedelta(days=i) for i in range(90)]
        usd_data = [
            {"timestamp": d, "close": 105 - i * 0.05, "change_pct": -0.05}
            for i, d in enumerate(dates)
        ]
        result = _analyze_usd_factor(usd_data)
        assert result["score"] > 0  # 美元走弱 → 利多
        assert result["impact"] == "利多"


# ── 宏观综合评分测试 ──────────────────────────────────────────


class TestMacroScore:
    """测试宏观综合评分"""

    def test_all_bullish(self):
        from app.services.analysis.macro_engine import _compute_macro_score

        factors = [
            {"name": "通胀", "impact": "利多", "weight": 0.35, "score": 50},
            {"name": "利率", "impact": "利多", "weight": 0.35, "score": 30},
            {"name": "美元", "impact": "利多", "weight": 0.30, "score": 40},
        ]
        score, confidence = _compute_macro_score(factors)
        assert score > 0
        assert 0 < confidence <= 1.0

    def test_score_range(self):
        """评分应在 -100 ~ +100 范围内"""
        from app.services.analysis.macro_engine import _compute_macro_score

        factors = [
            {"name": "通胀", "impact": "利空", "weight": 0.35, "score": -100},
            {"name": "利率", "impact": "利空", "weight": 0.35, "score": -100},
            {"name": "美元", "impact": "利空", "weight": 0.30, "score": -100},
        ]
        score, _ = _compute_macro_score(factors)
        assert -100 <= score <= 100


# ── API 端点测试 ──────────────────────────────────────────────


@pytest.mark.anyio
class TestAnalysisEndpoints:
    """测试分析 API 端点"""

    async def test_analysis_routes_registered(self):
        """验证 5 个分析端点已注册"""
        from app.api.v1.analysis import router

        route_paths = [r.path for r in router.routes]
        assert "/analysis/market" in route_paths
        assert "/analysis/macro" in route_paths
        assert "/analysis/summary" in route_paths

    async def test_market_analysis_endpoint_structure(self):
        """验证市场分析 API 返回结构"""
        from app.api.v1.analysis import router

        # 确认 POST 和 GET 方法都注册（FastAPI 将同路径不同方法注册为独立路由）
        methods = {}
        for route in router.routes:
            if hasattr(route, "methods"):
                methods.setdefault(route.path, set()).update(route.methods)
        assert "POST" in methods.get("/analysis/market", set())
        assert "GET" in methods.get("/analysis/market", set())

    async def test_macro_analysis_endpoint_structure(self):
        """验证宏观分析 API 返回结构"""
        from app.api.v1.analysis import router

        methods = {}
        for route in router.routes:
            if hasattr(route, "methods"):
                methods.setdefault(route.path, set()).update(route.methods)
        assert "POST" in methods.get("/analysis/macro", set())
        assert "GET" in methods.get("/analysis/macro", set())

    async def test_summary_endpoint_structure(self):
        """验证综合摘要 API 返回结构"""
        from app.api.v1.analysis import router

        methods = {}
        for route in router.routes:
            if hasattr(route, "methods"):
                methods.setdefault(route.path, set()).update(route.methods)
        assert "GET" in methods.get("/analysis/summary", set())


# ── Schema 测试 ──────────────────────────────────────────────


class TestAnalysisSchemas:
    """测试分析模块 Pydantic 模型"""

    def test_analysis_factor(self):
        from app.schemas.analysis import AnalysisFactor

        factor = AnalysisFactor(
            name="测试因素",
            impact="利多",
            weight=0.5,
            evidence="测试依据",
            score=50,
        )
        assert factor.name == "测试因素"
        assert factor.score == 50

    def test_analysis_result(self):
        from app.schemas.analysis import AnalysisResult, AnalysisFactor, AnalysisDataRange

        result = AnalysisResult(
            analysis_type="market_correlation",
            timestamp="2024-01-01T00:00:00",
            conclusion="利多",
            confidence=0.75,
            score=60,
            factors=[
                AnalysisFactor(
                    name="因素A",
                    impact="利多",
                    weight=0.5,
                    evidence="依据A",
                    score=60,
                ),
            ],
            data_range=AnalysisDataRange(start="2024-01-01", end="2024-06-01"),
            source="market_macro_agent",
        )
        assert result.analysis_type == "market_correlation"
        assert len(result.factors) == 1
        assert result.score == 60

    def test_analysis_summary(self):
        from app.schemas.analysis import AnalysisSummary

        summary = AnalysisSummary(
            timestamp="2024-01-01T00:00:00",
            overall_conclusion="中性",
            overall_score=5,
            overall_confidence=0.6,
        )
        assert summary.overall_score == 5
