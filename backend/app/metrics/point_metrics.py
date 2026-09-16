"""Point forecast metrics — MAE, RMSE, MAPE, sMAPE."""
import numpy as np


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Error."""
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Root Mean Squared Error."""
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Mean Absolute Percentage Error. Handles zero actuals."""
    mask = actual != 0
    if not mask.any():
        return float("inf")
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)


def smape(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Symmetric Mean Absolute Percentage Error."""
    denominator = (np.abs(actual) + np.abs(predicted))
    mask = denominator != 0
    if not mask.any():
        return 0.0
    return float(
        np.mean(2 * np.abs(actual[mask] - predicted[mask]) / denominator[mask]) * 100
    )


def directional_accuracy(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Percentage of correctly predicted directions.

    Compares sign of changes, not absolute direction.
    """
    if len(actual) < 2:
        return 0.0
    actual_dir = np.sign(np.diff(actual))
    pred_dir = np.sign(np.diff(predicted))
    return float(np.mean(actual_dir == pred_dir) * 100)
