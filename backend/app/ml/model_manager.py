"""Model lifecycle manager — lazy loading, caching, device management."""
import logging
from typing import Dict, Any
from app.core.config import Settings
from app.ml.base import ForecastModelProvider, ModelInfo
from app.ml.timesfm.config import TimesFMConfig
from app.ml.timesfm.timesfm3_provider import TimesFM3Provider
from app.ml.timesfm.timesfm25_provider import TimesFM25Provider
from app.ml.baselines.naive import NaiveProvider
from app.ml.baselines.drift import DriftProvider
from app.ml.baselines.sma import SMAProvider
from app.ml.baselines.arima import ARIMAProvider
from app.ml.baselines.xgboost_model import XGBoostProvider

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model lifecycle with lazy loading and mutual exclusion.

    On 4GB VRAM, only one TimesFM variant can be loaded at a time.
    Baseline models are lightweight and always available.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._providers: Dict[str, ForecastModelProvider] = {}
        self._loaded_gpu_model: str | None = None

        # Register all available providers
        self._registry: Dict[str, type] = {
            "timesfm3": TimesFM3Provider,
            "timesfm25": TimesFM25Provider,
            "naive": NaiveProvider,
            "drift": DriftProvider,
            "sma": SMAProvider,
            "arima": ARIMAProvider,
            "xgboost": XGBoostProvider,
        }

    def get_provider(self, model_name: str) -> ForecastModelProvider:
        """Get or create a provider instance."""
        if model_name not in self._providers:
            if model_name not in self._registry:
                raise ValueError(f"Unknown model: {model_name}")
            self._providers[model_name] = self._create_provider(model_name)
        return self._providers[model_name]

    def _create_provider(self, model_name: str) -> ForecastModelProvider:
        if model_name == "timesfm3":
            config = TimesFMConfig(
                checkpoint=self.settings.timesfm3_checkpoint,
                device_mode=self.settings.device_mode.value,
                context_length=self.settings.default_context_length,
                forecast_horizon=self.settings.default_forecast_horizon,
                batch_size=self.settings.default_batch_size,
                gpu_memory_threshold_mb=self.settings.gpu_memory_threshold_mb,
            )
            return TimesFM3Provider(config)
        elif model_name == "timesfm25":
            config = TimesFMConfig(
                checkpoint=self.settings.timesfm25_checkpoint,
                device_mode=self.settings.device_mode.value,
            )
            return TimesFM25Provider(config)
        else:
            return self._registry[model_name]()

    async def load_model(self, model_name: str) -> ModelInfo:
        """Load a model, enforcing GPU mutual exclusion."""
        provider = self.get_provider(model_name)

        # If loading a GPU model, unload any existing GPU model first
        if model_name in ("timesfm3", "timesfm25"):
            if (self._loaded_gpu_model and
                self._loaded_gpu_model != model_name):
                logger.info(
                    f"Unloading {self._loaded_gpu_model} to make "
                    f"room for {model_name}"
                )
                await self._providers[self._loaded_gpu_model].unload()
                self._loaded_gpu_model = None

        await provider.load()

        if model_name in ("timesfm3", "timesfm25"):
            self._loaded_gpu_model = model_name

        return provider.info()

    def list_models(self) -> list[ModelInfo]:
        """List all registered models with their status."""
        models = []
        for name in self._registry:
            if name in self._providers:
                models.append(self._providers[name].info())
            else:
                # Create temporary to get info without loading
                provider = self._create_provider(name)
                models.append(provider.info())
        return models

    async def unload_all(self) -> None:
        for name, provider in self._providers.items():
            try:
                await provider.unload()
            except Exception as e:
                logger.error(f"Error unloading {name}: {e}")
        self._providers.clear()
        self._loaded_gpu_model = None
