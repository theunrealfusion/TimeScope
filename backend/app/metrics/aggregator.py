from __future__ import annotations
"""Aggregate metrics per-horizon-step and overall."""
import numpy as np
from dataclasses import dataclass
from app.metrics.point_metrics import mae, rmse, mape, smape, directional_accuracy
from app.metrics.probabilistic import pinball_loss, interval_coverage, interval_width


@dataclass
class HorizonMetrics:
    step: int   # H+1, H+2, ...
    mae: float
    rmse: float
    mape: float
    smape: float
    directional_accuracy: float | None = None
    pinball_loss_50: float | None = None
    interval_coverage_80: float | None = None
    interval_width_80: float | None = None


def compute_per_horizon_metrics(
    actuals: np.ndarray,   # (num_origins, horizon)
    forecasts: np.ndarray, # (num_origins, horizon)
    quantiles: np.ndarray | None = None,  # (num_origins, horizon, 9)
) -> list[HorizonMetrics]:
    """Calculate metrics separately for each horizon step.

    This is critical because models often perform well at H+1
    but degrade rapidly at H+5.
    """
    horizon = forecasts.shape[1]
    results = []

    for h in range(horizon):
        a = actuals[:, h]
        f = forecasts[:, h]

        metrics = HorizonMetrics(
            step=h + 1,
            mae=mae(a, f),
            rmse=rmse(a, f),
            mape=mape(a, f),
            smape=smape(a, f),
        )

        if quantiles is not None:
            # Q50 = median (index 4 in 0.1-0.9 range)
            metrics.pinball_loss_50 = pinball_loss(a, quantiles[:, h, 4], 0.5)
            # 80% interval: Q10–Q90 (indices 0 and 8)
            metrics.interval_coverage_80 = interval_coverage(
                a, quantiles[:, h, 0], quantiles[:, h, 8]
            )
            metrics.interval_width_80 = interval_width(
                quantiles[:, h, 0], quantiles[:, h, 8]
            )

        results.append(metrics)

    return results
