"""Forecast service — orchestrates the full forecasting pipeline."""
import hashlib
import json
import logging
import uuid
from datetime import datetime
import numpy as np
import pandas as pd

from app.db.duckdb_manager import DuckDBManager
from app.features.transforms import TargetMode, compute_log_returns, reconstruct_prices_from_log_returns
from app.features.leakage_guard import LeakageGuard
from app.ml.base import ForecastResult
from app.ml.model_manager import ModelManager
from app.schemas.forecast import ForecastRequest, ForecastResponse

logger = logging.getLogger(__name__)


class ForecastService:
    """Orchestrates data retrieval, feature construction, model
    inference, and result persistence with leakage prevention."""

    def __init__(self, db: DuckDBManager, model_manager: ModelManager):
        self.db = db
        self.model_manager = model_manager
        self.leakage_guard = LeakageGuard()

    async def run_forecast(self, request: ForecastRequest) -> ForecastResponse:
        """Execute a single forecast with full pipeline."""
        run_id = str(uuid.uuid4())

        # 1. Fetch data up to cutoff only
        cutoff = request.cutoff_date or datetime.now()
        data = self._fetch_data(request.symbol, cutoff, request.context_length)

        # 2. Validate no future leakage
        self.leakage_guard.validate_information_cutoff(
            data, cutoff, context=f"forecast for {request.symbol}"
        )

        # 3. Prepare target based on mode
        if request.target_mode == TargetMode.LOG_RETURN:
            target_series = compute_log_returns(data["close"])
            target_series = target_series.dropna()
        else:
            target_series = data["close"]

        context = target_series.values[-request.context_length:]

        # 4. Load model if needed
        provider = self.model_manager.get_provider(request.model_name)
        if not provider.health().get("loaded"):
            await self.model_manager.load_model(request.model_name)

        # 5. Run inference
        result = await provider.forecast_univariate(
            context=context,
            horizon=request.horizon,
        )

        # 6. If log-return mode, reconstruct prices
        forecast_prices = None
        if request.target_mode == TargetMode.LOG_RETURN:
            last_price = data["close"].iloc[-1]
            forecast_prices = reconstruct_prices_from_log_returns(
                result.point_forecast, last_price, recursive=True
            )

        # 7. Persist forecast
        self._persist_forecast(run_id, request, result, cutoff)

        # 8. Build response
        return ForecastResponse(
            run_id=run_id,
            symbol=request.symbol,
            model_name=result.model_name,
            model_version=result.model_version,
            device=result.device_used,
            target_mode=request.target_mode,
            horizon=request.horizon,
            context_length=result.context_length_used,
            origin_timestamp=cutoff.isoformat(),
            point_forecast=result.point_forecast.tolist(),
            forecast_prices=forecast_prices.tolist() if forecast_prices is not None else None,
            quantiles={
                f"q{int(q*100)}": result.quantiles[:, i].tolist()
                for i, q in enumerate(result.quantile_levels)
            } if result.quantiles is not None else None,
            reconstruction_method="recursive" if request.target_mode == TargetMode.LOG_RETURN else None,
        )

    def _fetch_data(self, symbol: str, cutoff: datetime, min_rows: int) -> pd.DataFrame:
        """Fetch historical data up to cutoff — never beyond."""
        with self.db.read_connection() as conn:
            df = conn.execute("""
                SELECT * FROM market_data
                WHERE symbol = ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, [symbol, cutoff]).fetchdf()

        if len(df) < min_rows:
            raise ValueError(
                f"Insufficient history for {symbol}: "
                f"need {min_rows} rows, got {len(df)}"
            )
        return df

    def _persist_forecast(self, run_id, request, result, cutoff):
        """Save forecast run and individual points to DuckDB."""
        with self.db.write_connection() as conn:
            conn.execute("""
                INSERT INTO forecast_runs
                (id, symbol, origin_timestamp, information_cutoff,
                 horizon, model_name, model_version, device,
                 context_length, target_mode)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                run_id, request.symbol, cutoff, cutoff,
                request.horizon, result.model_name, result.model_version,
                result.device_used, result.context_length_used,
                request.target_mode.value,
            ])

            for step in range(request.horizon):
                quantile_vals = {}
                if result.quantiles is not None:
                    for i, q in enumerate(result.quantile_levels):
                        quantile_vals[f"q{int(q*100)}"] = float(result.quantiles[step, i])

                conn.execute("""
                    INSERT INTO forecast_points
                    (run_id, target_name, step, point_forecast,
                     q10, q20, q30, q40, q50, q60, q70, q80, q90)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    run_id, "close", step + 1,
                    float(result.point_forecast[step]),
                    quantile_vals.get("q10"), quantile_vals.get("q20"),
                    quantile_vals.get("q30"), quantile_vals.get("q40"),
                    quantile_vals.get("q50"), quantile_vals.get("q60"),
                    quantile_vals.get("q70"), quantile_vals.get("q80"),
                    quantile_vals.get("q90"),
                ])
