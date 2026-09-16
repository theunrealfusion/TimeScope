"""Walk-forward backtesting engine with leakage-free evaluation.

Implements rolling-origin evaluation where at each step:
1. Data is truncated to the current cutoff
2. Features are computed using only available data
3. Forecast is generated
4. Cutoff advances by step_size
"""
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator
import numpy as np
import pandas as pd

from app.features.leakage_guard import LeakageGuard
from app.features.transforms import TargetMode, compute_log_returns
from app.ml.base import ForecastModelProvider, ForecastResult

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    symbol: str
    train_start: datetime
    end_date: datetime
    initial_context_length: int = 512
    forecast_horizon: int = 5
    step_size: int = 1
    target_mode: TargetMode = TargetMode.RAW_PRICE
    target_variates: list[str] | None = None
    model_names: list[str] | None = None


@dataclass
class BacktestOriginResult:
    """Result from a single forecast origin."""
    origin_index: int
    origin_timestamp: datetime
    information_cutoff: datetime
    point_forecast: np.ndarray
    quantiles: np.ndarray | None
    actual_values: np.ndarray | None
    model_name: str


@dataclass
class BacktestProgress:
    completed_origins: int
    total_origins: int
    percent: float
    current_origin: datetime | None = None
    status: str = "running"


class WalkForwardEngine:
    """Rolling-origin walk-forward backtesting.

    At each origin:
    1. Take only data <= cutoff
    2. Build features from causal data only
    3. Generate forecast
    4. Record forecast + actual
    5. Advance cutoff by step_size
    6. Repeat

    NEVER:
    - Use data after cutoff for features
    - Fit normalization on future data
    - Select hyperparameters using test period
    """

    def __init__(self):
        self.leakage_guard = LeakageGuard()

    async def run(
        self,
        config: BacktestConfig,
        full_data: pd.DataFrame,
        provider: ForecastModelProvider,
        progress_callback=None,
    ) -> AsyncIterator[BacktestOriginResult]:
        """Execute walk-forward backtest.

        Yields one BacktestOriginResult per forecast origin.
        """
        # Sort by timestamp
        data = full_data.sort_values("timestamp").reset_index(drop=True)
        timestamps = data["timestamp"].values

        # Calculate origin indices
        start_idx = config.initial_context_length
        # End index: we need at least horizon points after the origin
        end_idx = len(data) - config.forecast_horizon
        total_origins = max(0, (end_idx - start_idx) // config.step_size + 1)

        if total_origins == 0:
            raise ValueError(
                f"Insufficient data for backtest: need at least "
                f"{config.initial_context_length + config.forecast_horizon} "
                f"sessions, got {len(data)}"
            )

        logger.info(
            f"Starting walk-forward backtest: {total_origins} origins, "
            f"context={config.initial_context_length}, "
            f"horizon={config.forecast_horizon}, step={config.step_size}"
        )

        for origin_num, origin_idx in enumerate(
            range(start_idx, end_idx + 1, config.step_size)
        ):
            cutoff_ts = pd.Timestamp(timestamps[origin_idx])

            # 1. Strict cutoff: only data <= origin_idx
            context_data = data.iloc[:origin_idx + 1]

            # 2. Validate no leakage
            self.leakage_guard.validate_information_cutoff(
                context_data, cutoff_ts,
                context=f"backtest origin {origin_num}"
            )

            # 3. Prepare target
            if config.target_mode == TargetMode.LOG_RETURN:
                target = compute_log_returns(context_data["close"]).dropna().values
            else:
                target = context_data["close"].values

            # Use last context_length points
            context = target[-config.initial_context_length:]

            # 4. Run forecast
            result = await provider.forecast_univariate(
                context=context,
                horizon=config.forecast_horizon,
            )

            # 5. Get actual values for evaluation
            actual_start = origin_idx + 1
            actual_end = actual_start + config.forecast_horizon
            if actual_end <= len(data):
                if config.target_mode == TargetMode.LOG_RETURN:
                    actual_values = compute_log_returns(
                        data["close"].iloc[origin_idx:actual_end]
                    ).dropna().values
                else:
                    actual_values = data["close"].iloc[actual_start:actual_end].values
            else:
                actual_values = None

            # 6. Report progress
            if progress_callback:
                progress_callback(BacktestProgress(
                    completed_origins=origin_num + 1,
                    total_origins=total_origins,
                    percent=round((origin_num + 1) / total_origins * 100, 1),
                    current_origin=cutoff_ts,
                ))

            yield BacktestOriginResult(
                origin_index=origin_num,
                origin_timestamp=cutoff_ts,
                information_cutoff=cutoff_ts,
                point_forecast=result.point_forecast,
                quantiles=result.quantiles,
                actual_values=actual_values,
                model_name=result.model_name,
            )
