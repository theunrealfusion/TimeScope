from __future__ import annotations
"""Market regime detector using transparent, deterministic rules.

No opaque ML labels — all thresholds are documented and configurable.
"""
import numpy as np
import pandas as pd
from enum import Enum


class MarketRegime(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


def classify_regime(
    prices: pd.Series,
    lookback: int = 60,
    trend_threshold: float = 0.10,
    vol_lookback: int = 20,
    vol_high_percentile: float = 75,
    vol_low_percentile: float = 25,
) -> MarketRegime:
    """Classify current market regime based on recent price action.

    Rules (transparent, no black box):
    - BULL: cumulative return over lookback > +threshold
    - BEAR: cumulative return over lookback < -threshold
    - SIDEWAYS: cumulative return within [-threshold, +threshold]
    - HIGH_VOLATILITY: realized vol > vol_high_percentile of full history
    - LOW_VOLATILITY: realized vol < vol_low_percentile of full history

    Volatility classification is secondary (overlaid on trend).
    """
    if len(prices) < lookback:
        return MarketRegime.SIDEWAYS

    recent = prices.iloc[-lookback:]
    cum_return = (recent.iloc[-1] / recent.iloc[0]) - 1

    # Primary: trend classification
    if cum_return > trend_threshold:
        regime = MarketRegime.BULL
    elif cum_return < -trend_threshold:
        regime = MarketRegime.BEAR
    else:
        regime = MarketRegime.SIDEWAYS

    # Secondary: volatility check
    returns = prices.pct_change().dropna()
    if len(returns) < vol_lookback:
        return regime

    recent_vol = returns.iloc[-vol_lookback:].std() * np.sqrt(252)
    full_vol = returns.std() * np.sqrt(252)

    if len(returns) > 100:
        vol_series = returns.rolling(vol_lookback).std() * np.sqrt(252)
        vol_series = vol_series.dropna()
        high_threshold = np.percentile(vol_series, vol_high_percentile)
        low_threshold = np.percentile(vol_series, vol_low_percentile)

        if recent_vol > high_threshold:
            regime = MarketRegime.HIGH_VOLATILITY
        elif recent_vol < low_threshold:
            regime = MarketRegime.LOW_VOLATILITY

    return regime
