"""Probabilistic forecast metrics — pinball loss, coverage, calibration."""
import numpy as np


def pinball_loss(actual: np.ndarray, quantile_forecast: np.ndarray,
                 quantile: float) -> float:
    """Pinball (quantile) loss for a specific quantile level."""
    diff = actual - quantile_forecast
    return float(np.mean(np.where(diff >= 0, quantile * diff,
                                   (quantile - 1) * diff)))


def interval_coverage(actual: np.ndarray, lower: np.ndarray,
                      upper: np.ndarray) -> float:
    """Fraction of actual values falling within [lower, upper]."""
    covered = (actual >= lower) & (actual <= upper)
    return float(np.mean(covered) * 100)


def interval_width(lower: np.ndarray, upper: np.ndarray) -> float:
    """Mean width of prediction intervals."""
    return float(np.mean(upper - lower))


def quantile_calibration(actual: np.ndarray, quantile_forecasts: np.ndarray,
                         quantile_levels: list[float]) -> dict[float, float]:
    """Actual coverage vs nominal quantile level.

    Perfect calibration: actual coverage ≈ nominal level.
    """
    calibration = {}
    for i, q in enumerate(quantile_levels):
        below = np.mean(actual <= quantile_forecasts[:, i])
        calibration[q] = float(below)
    return calibration
