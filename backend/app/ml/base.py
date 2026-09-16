from __future__ import annotations
"""Forecast model provider abstraction."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional
import numpy as np


class ModelCapability(str, Enum):
    UNIVARIATE = "univariate"
    MULTIVARIATE = "multivariate"
    COVARIATES = "covariates"
    QUANTILES = "quantiles"
    PROBABILISTIC = "probabilistic"


@dataclass
class ModelInfo:
    name: str
    version: str
    provider: str
    checkpoint: str | None = None
    library_version: str | None = None
    license: str | None = None
    capabilities: list[ModelCapability] | None = None
    device: str | None = None
    loaded: bool = False


@dataclass
class ForecastResult:
    """Container for forecast output."""
    point_forecast: np.ndarray        # (horizon,) or (num_variates, horizon)
    quantiles: np.ndarray | None      # (horizon, 9) or (num_variates, horizon, 9)
    quantile_levels: list[float] | None  # e.g. [0.1, 0.2, ..., 0.9]
    target_names: list[str]
    model_name: str
    model_version: str
    device_used: str
    context_length_used: int


class ForecastModelProvider(ABC):
    """Abstract interface for all forecast model providers."""

    @abstractmethod
    async def load(self) -> None:
        """Load model weights into memory."""
        ...

    @abstractmethod
    async def unload(self) -> None:
        """Release model from memory."""
        ...

    @abstractmethod
    def health(self) -> dict[str, Any]:
        """Return health status of the model."""
        ...

    @abstractmethod
    def capabilities(self) -> list[ModelCapability]:
        """Return list of supported capabilities."""
        ...

    @abstractmethod
    def info(self) -> ModelInfo:
        """Return model metadata."""
        ...

    @abstractmethod
    async def forecast_univariate(
        self,
        context: np.ndarray,
        horizon: int,
        **kwargs,
    ) -> ForecastResult:
        """Generate univariate forecast with optional quantiles."""
        ...

    @abstractmethod
    async def forecast_multivariate(
        self,
        context: np.ndarray,  # (num_variates, context_length)
        horizon: int,
        target_names: list[str],
        **kwargs,
    ) -> ForecastResult:
        """Generate multivariate forecast."""
        ...

    @abstractmethod
    async def forecast_with_covariates(
        self,
        target: np.ndarray,
        past_covariates: np.ndarray | None,
        future_covariates: np.ndarray | None,
        horizon: int,
        **kwargs,
    ) -> ForecastResult:
        """Generate forecast with external covariates."""
        ...
