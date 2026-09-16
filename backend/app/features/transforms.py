from __future__ import annotations
"""Causal time-series transforms for feature engineering."""
import numpy as np
import pandas as pd
from enum import Enum


class TargetMode(str, Enum):
    RAW_PRICE = "raw_price"
    LOG_RETURN = "log_return"


def compute_log_returns(prices: pd.Series) -> pd.Series:
    """Compute log returns: log(P_t / P_{t-1}).

    First value will be NaN (no previous price).
    Correctly handles negative returns.
    """
    return np.log(prices / prices.shift(1))


def reconstruct_prices_from_log_returns(
    log_returns: np.ndarray,
    last_known_price: float,
    recursive: bool = True,
) -> np.ndarray:
    """Convert predicted log returns back to prices.

    Args:
        log_returns: Array of predicted log returns.
        last_known_price: The last actual known price before forecast.
        recursive: If True, each step uses the previous forecast price.
                   If False, all steps use last_known_price.

    Returns:
        Array of forecast prices.
    """
    prices = np.zeros_like(log_returns)
    if recursive:
        prev_price = last_known_price
        for i, lr in enumerate(log_returns):
            prices[i] = prev_price * np.exp(lr)
            prev_price = prices[i]
    else:
        prices = last_known_price * np.exp(log_returns)
    return prices


def rolling_mean(series: pd.Series, window: int) -> pd.Series:
    """Left-aligned (causal) rolling mean. No future data used."""
    return series.rolling(window=window, min_periods=window).mean()


def rolling_std(series: pd.Series, window: int) -> pd.Series:
    """Left-aligned (causal) rolling standard deviation."""
    return series.rolling(window=window, min_periods=window).std()


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index — strictly causal computation."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_atr(
    high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
) -> pd.Series:
    """Average True Range — strictly causal."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()
