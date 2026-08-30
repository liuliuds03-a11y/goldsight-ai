"""
GoldSight AI V3.0 - 技术指标计算模块

纯 Python + numpy 实现常用技术指标计算，不依赖 TA-Lib。
所有函数接收 numpy 数组，返回 float 或 None（数据不足时）。

指标分类：
- 趋势类：MA、EMA、MACD、ADX
- 动量类：RSI、Stochastic、ROC
- 波动类：Bollinger Bands、ATR
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Union

import numpy as np


# ── 趋势类指标 ────────────────────────────────────────────────


def calculate_ma(prices: np.ndarray, period: int) -> Optional[float]:
    """
    简单移动平均线 (SMA)

    计算最近 period 个价格的算术平均值。

    Args:
        prices: 收盘价数组（按时间升序）
        period: 周期（如 5/10/20/60）

    Returns:
        MA 值，数据不足时返回 None
    """
    if len(prices) < period:
        return None
    return float(np.mean(prices[-period:]))


def calculate_ema(prices: np.ndarray, period: int) -> Optional[float]:
    """
    指数移动平均线 (EMA)

    使用标准 EMA 公式：
        multiplier = 2 / (period + 1)
        EMA = (price - prev_EMA) * multiplier + prev_EMA

    初始 EMA 取前 period 个价格的 SMA。

    Args:
        prices: 收盘价数组（按时间升序）
        period: 周期（如 12/26）

    Returns:
        EMA 值，数据不足时返回 None
    """
    if len(prices) < period:
        return None

    multiplier = 2.0 / (period + 1)
    # 初始 EMA = 前 period 个价格的 SMA
    ema = float(np.mean(prices[:period]))

    # 从第 period 个价格开始递推
    for i in range(period, len(prices)):
        ema = (float(prices[i]) - ema) * multiplier + ema

    return ema


def calculate_macd(
    prices: np.ndarray,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Optional[Dict[str, float]]:
    """
    移动平均收敛散度 (MACD)

    计算流程：
        1. MACD 线 = EMA(fast) - EMA(slow)
        2. 信号线 = EMA(MACD 线, signal_period)
        3. 柱状图 = MACD 线 - 信号线

    注意：需要至少 slow_period + signal_period - 1 个数据点
    才能产生有效的信号线和柱状图。

    Args:
        prices: 收盘价数组（按时间升序）
        fast_period: 快线周期，默认 12
        slow_period: 慢线周期，默认 26
        signal_period: 信号线周期，默认 9

    Returns:
        包含 macd/signal/hist 的字典，数据不足时返回 None
    """
    if len(prices) < slow_period:
        return None

    # 计算快慢 EMA 序列
    fast_ema = _ema_series(prices, fast_period)
    slow_ema = _ema_series(prices, slow_period)

    # 对齐长度：慢线 EMA 从 index (slow_period-1) 开始有效
    # 快线 EMA 从 index (fast_period-1) 开始有效
    # MACD 线从 index (slow_period-1) 开始有效
    offset = slow_period - fast_period
    macd_line = fast_ema[offset:] - slow_ema

    if len(macd_line) < signal_period:
        # 仅有 MACD 线，无法计算信号线
        return {
            "macd": float(macd_line[-1]),
            "signal": None,
            "hist": None,
        }

    # 信号线 = MACD 线的 EMA
    signal_ema = _ema_series(macd_line, signal_period)
    macd_val = float(macd_line[-1])
    signal_val = float(signal_ema[-1])

    return {
        "macd": macd_val,
        "signal": signal_val,
        "hist": macd_val - signal_val,
    }


def calculate_adx(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> Optional[float]:
    """
    平均趋向指数 (ADX)

    使用 Wilder 平滑法计算：
        1. 计算 TR、+DM、-DM
        2. Wilder 平滑得到 smoothed TR、+DM、-DM
        3. +DI = +DM / TR * 100, -DI = -DM / TR * 100
        4. DX = |+DI - -DI| / (+DI + -DI) * 100
        5. ADX = DX 的 Wilder 平滑

    Args:
        highs: 最高价数组
        lows: 最低价数组
        closes: 收盘价数组
        period: 周期，默认 14

    Returns:
        ADX 值，数据不足时返回 None
    """
    n = len(highs)
    if n < period * 2 + 1:
        return None

    # 计算 True Range, +DM, -DM
    tr_list: list = []
    plus_dm_list: list = []
    minus_dm_list: list = []

    for i in range(1, n):
        high_low = highs[i] - lows[i]
        high_prev_close = abs(highs[i] - closes[i - 1])
        low_prev_close = abs(lows[i] - closes[i - 1])

        tr = max(high_low, high_prev_close, low_prev_close)
        up_move = highs[i] - highs[i - 1]
        down_move = lows[i - 1] - lows[i]

        plus_dm = up_move if (up_move > down_move and up_move > 0) else 0.0
        minus_dm = down_move if (down_move > up_move and down_move > 0) else 0.0

        tr_list.append(tr)
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    tr_arr = np.array(tr_list)
    plus_dm_arr = np.array(plus_dm_list)
    minus_dm_arr = np.array(minus_dm_list)

    # Wilder 平滑：第一个值用简单求和，后续用递推公式
    smoothed_tr = np.sum(tr_arr[:period])
    smoothed_plus_dm = np.sum(plus_dm_arr[:period])
    smoothed_minus_dm = np.sum(minus_dm_arr[:period])

    dx_values: list = []

    for i in range(period, len(tr_arr)):
        if i > period:
            smoothed_tr = smoothed_tr - smoothed_tr / period + tr_arr[i]
            smoothed_plus_dm = (
                smoothed_plus_dm - smoothed_plus_dm / period + plus_dm_arr[i]
            )
            smoothed_minus_dm = (
                smoothed_minus_dm - smoothed_minus_dm / period + minus_dm_arr[i]
            )

        if smoothed_tr == 0:
            continue

        plus_di = smoothed_plus_dm / smoothed_tr * 100
        minus_di = smoothed_minus_dm / smoothed_tr * 100
        di_sum = plus_di + minus_di

        if di_sum != 0:
            dx = abs(plus_di - minus_di) / di_sum * 100
            dx_values.append(dx)

    if len(dx_values) < period:
        return None

    # ADX = DX 的 Wilder 平滑（第一个 ADX 取简单平均）
    adx = float(np.mean(dx_values[:period]))
    for i in range(period, len(dx_values)):
        adx = (adx * (period - 1) + dx_values[i]) / period

    return adx


# ── 动量类指标 ────────────────────────────────────────────────


def calculate_rsi(
    prices: np.ndarray, period: int = 14
) -> Optional[float]:
    """
    相对强弱指数 (RSI)

    使用 Wilder 平滑法：
        1. 计算每日涨跌幅
        2. 分离涨幅和跌幅
        3. 平均涨幅 / 平均跌幅 = RS
        4. RSI = 100 - 100 / (1 + RS)

    Args:
        prices: 收盘价数组（按时间升序）
        period: 周期，默认 14

    Returns:
        RSI 值（0-100），数据不足时返回 None
    """
    if len(prices) < period + 1:
        return None

    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # 初始平均涨幅/跌幅 = 前 period 个变化的简单平均
    avg_gain = float(np.mean(gains[:period]))
    avg_loss = float(np.mean(losses[:period]))

    # Wilder 平滑递推
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + float(gains[i])) / period
        avg_loss = (avg_loss * (period - 1) + float(losses[i])) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def calculate_stochastic(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> Optional[Dict[str, float]]:
    """
    随机指标 (Stochastic Oscillator)

    计算流程：
        1. %K = (Close - Lowest Low) / (Highest High - Lowest Low) * 100
        2. %D = SMA(%K, 3)

    Args:
        highs: 最高价数组
        lows: 最低价数组
        closes: 收盘价数组
        period: 回看周期，默认 14

    Returns:
        包含 k/d 的字典，数据不足时返回 None
    """
    n = len(closes)
    if n < period + 2:
        return None

    # 计算 Fast %K 序列
    k_values: list = []
    for i in range(period - 1, n):
        highest_high = float(np.max(highs[i - period + 1: i + 1]))
        lowest_low = float(np.min(lows[i - period + 1: i + 1]))
        if highest_high == lowest_low:
            k_values.append(50.0)
        else:
            k_values.append(
                (float(closes[i]) - lowest_low)
                / (highest_high - lowest_low)
                * 100
            )

    if len(k_values) < 3:
        return None

    k_arr = np.array(k_values)
    k_val = float(k_arr[-1])
    d_val = float(np.mean(k_arr[-3:]))

    return {"k": k_val, "d": d_val}


def calculate_roc(
    prices: np.ndarray, period: int = 14
) -> Optional[float]:
    """
    变化率 (ROC)

    ROC = (当前价格 - period 前价格) / period 前价格 * 100

    Args:
        prices: 收盘价数组（按时间升序）
        period: 回看周期，默认 14

    Returns:
        ROC 值（百分比），数据不足时返回 None
    """
    if len(prices) <= period:
        return None

    prev_price = float(prices[-(period + 1)])
    curr_price = float(prices[-1])

    if prev_price == 0:
        return None

    return (curr_price - prev_price) / prev_price * 100.0


# ── 波动类指标 ────────────────────────────────────────────────


def calculate_bollinger_bands(
    prices: np.ndarray,
    period: int = 20,
    std_dev: float = 2.0,
) -> Optional[Dict[str, float]]:
    """
    布林带 (Bollinger Bands)

    计算流程：
        1. 中轨 = SMA(period)
        2. 上轨 = 中轨 + std_dev * STD(period)
        3. 下轨 = 中轨 - std_dev * STD(period)

    Args:
        prices: 收盘价数组（按时间升序）
        period: 周期，默认 20
        std_dev: 标准差倍数，默认 2.0

    Returns:
        包含 upper/middle/lower 的字典，数据不足时返回 None
    """
    if len(prices) < period:
        return None

    window = prices[-period:]
    middle = float(np.mean(window))
    std = float(np.std(window, ddof=0))

    return {
        "upper": middle + std_dev * std,
        "middle": middle,
        "lower": middle - std_dev * std,
    }


def calculate_atr(
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    period: int = 14,
) -> Optional[float]:
    """
    平均真实波幅 (ATR)

    使用 Wilder 平滑法：
        1. TR = max(H-L, |H-prevC|, |L-prevC|)
        2. 首个 ATR = 前 period 个 TR 的简单平均
        3. 后续 ATR = (prev_ATR * (period-1) + TR) / period

    Args:
        highs: 最高价数组
        lows: 最低价数组
        closes: 收盘价数组
        period: 周期，默认 14

    Returns:
        ATR 值，数据不足时返回 None
    """
    n = len(highs)
    if n < period + 1:
        return None

    # 计算 True Range 序列
    tr_values: list = []
    for i in range(1, n):
        high_low = highs[i] - lows[i]
        high_prev_close = abs(highs[i] - closes[i - 1])
        low_prev_close = abs(lows[i] - closes[i - 1])
        tr_values.append(max(high_low, high_prev_close, low_prev_close))

    if len(tr_values) < period:
        return None

    # Wilder 平滑：初始 ATR = 前 period 个 TR 的 SMA
    atr = float(np.mean(tr_values[:period]))
    for i in range(period, len(tr_values)):
        atr = (atr * (period - 1) + tr_values[i]) / period

    return atr


# ── 内部辅助函数 ──────────────────────────────────────────────


def _ema_series(prices: np.ndarray, period: int) -> np.ndarray:
    """
    计算 EMA 完整序列（用于 MACD 等需要中间序列的指标）

    初始 EMA 取前 period 个价格的 SMA，之后递推。
    返回数组长度 = len(prices) - period + 1，
    其中 index 0 对应输入 prices 的 index (period-1)。

    Args:
        prices: 价格数组
        period: EMA 周期

    Returns:
        EMA 序列数组
    """
    if len(prices) < period:
        return np.array([])

    multiplier = 2.0 / (period + 1)
    result = np.zeros(len(prices) - period + 1)

    # 初始值 = SMA
    result[0] = float(np.mean(prices[:period]))

    # 递推
    for i in range(1, len(result)):
        result[i] = (
            (float(prices[period - 1 + i]) - result[i - 1]) * multiplier
            + result[i - 1]
        )

    return result
