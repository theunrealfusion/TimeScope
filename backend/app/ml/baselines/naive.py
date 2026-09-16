from __future__ import annotations
"""Naive (persistence) baseline forecast provider."""
import numpy as np
from app.ml.base import (
    ForecastModelProvider, ForecastResult, ModelCapability, ModelInfo,
)


class NaiveProvider(ForecastModelProvider):
    """Naive forecast: predicts last observed value for all horizons.

    This is the simplest baseline. Any useful model must beat this.
    """

    async def load(self) -> None:
        pass  # No model to load

    async def unload(self) -> None:
        pass

    def health(self) -> dict:
        return {"loaded": True, "model": "Naive/Persistence"}

    def capabilities(self) -> list[ModelCapability]:
        return [ModelCapability.UNIVARIATE]

    def info(self) -> ModelInfo:
        return ModelInfo(
            name="Naive (Persistence)",
            version="1.0",
            provider="naive",
            license="open",
            capabilities=self.capabilities(),
            loaded=True,
        )

    async def forecast_univariate(
        self, context: np.ndarray, horizon: int, **kwargs,
    ) -> ForecastResult:
        last_value = context[-1]
        point_forecast = np.full(horizon, last_value)

        # Simple quantiles based on historical volatility
        if len(context) > 1:
            std = np.std(np.diff(context))
            steps = np.arange(1, horizon + 1)
            quantiles = np.stack([
                point_forecast + std * np.sqrt(steps) * q_z
                for q_z in [-1.28, -0.84, -0.52, -0.25, 0.0, 0.25, 0.52, 0.84, 1.28]
            ], axis=-1)  # (horizon, 9)
        else:
            quantiles = None

        return ForecastResult(
            point_forecast=point_forecast,
            quantiles=quantiles,
            quantile_levels=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            target_names=["close"],
            model_name="Naive (Persistence)",
            model_version="1.0",
            device_used="cpu",
            context_length_used=len(context),
        )

    async def forecast_multivariate(self, context, horizon, target_names, **kwargs):
        results = []
        for i in range(context.shape[0]):
            r = await self.forecast_univariate(context[i], horizon)
            results.append(r.point_forecast)
        return ForecastResult(
            point_forecast=np.stack(results),
            quantiles=None,
            quantile_levels=None,
            target_names=target_names,
            model_name="Naive (Persistence)",
            model_version="1.0",
            device_used="cpu",
            context_length_used=context.shape[1],
        )

    async def forecast_with_covariates(self, target, past_covariates, future_covariates, horizon, **kwargs):
        return await self.forecast_univariate(target, horizon)
