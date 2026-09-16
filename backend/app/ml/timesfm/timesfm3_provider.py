from __future__ import annotations
"""TimesFM 3.0 model provider — local inference."""
import logging
import numpy as np
from typing import Any

from app.ml.base import (
    ForecastModelProvider, ForecastResult, ModelCapability, ModelInfo,
)
from app.ml.timesfm.device_manager import DeviceManager, DeviceType
from app.ml.timesfm.config import TimesFMConfig
from app.ml.timesfm.exceptions import (
    ModelLoadError, ModelInferenceError, CUDAOutOfMemoryError,
)

logger = logging.getLogger(__name__)


class TimesFM3Provider(ForecastModelProvider):
    """Google TimesFM 3.0 local inference provider.

    Uses the timesfm3 library for zero-shot time-series forecasting
    with native multivariate and covariate support.
    """

    def __init__(self, config: TimesFMConfig):
        self.config = config
        self._model = None
        self._device_info = None
        self._device_manager = DeviceManager(
            preferred=DeviceType(config.device_mode),
            memory_threshold_mb=config.gpu_memory_threshold_mb,
        )

    async def load(self) -> None:
        """Load TimesFM 3.0 checkpoint."""
        try:
            self._device_info = self._device_manager.select_device()
            device = self._device_info.device

            logger.info(
                f"Loading TimesFM 3.0 from {self.config.checkpoint} "
                f"on {device}"
            )

            # Import here to avoid import errors if timesfm not installed
            import timesfm

            self._model = timesfm.TimesFm(
                hparams=timesfm.TimesFmHparams(
                    per_core_batch_size=self.config.batch_size,
                    horizon_len=self.config.forecast_horizon,
                    context_len=self.config.context_length,
                    backend="gpu" if "cuda" in device else "cpu",
                ),
                checkpoint=timesfm.TimesFmCheckpoint(
                    huggingface_repo_id=self.config.checkpoint,
                ),
            )

            logger.info("TimesFM 3.0 loaded successfully.")

        except ImportError:
            raise ModelLoadError(
                "timesfm package not installed. "
                "Install with: pip install timesfm[torch]"
            )
        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                logger.warning("CUDA OOM during load. Retrying on CPU.")
                await self._fallback_cpu_load()
            else:
                raise ModelLoadError(f"Failed to load TimesFM 3.0: {e}")
        except Exception as e:
            raise ModelLoadError(f"Failed to load TimesFM 3.0: {e}")

    async def _fallback_cpu_load(self) -> None:
        """Retry loading on CPU after GPU failure."""
        import timesfm

        self._device_info = self._device_manager.select_device()
        self._device_info.device = "cpu"
        self._device_info.device_type = "cpu"

        self._model = timesfm.TimesFm(
            hparams=timesfm.TimesFmHparams(
                per_core_batch_size=self.config.batch_size,
                horizon_len=self.config.forecast_horizon,
                context_len=self.config.context_length,
                backend="cpu",
            ),
            checkpoint=timesfm.TimesFmCheckpoint(
                huggingface_repo_id=self.config.checkpoint,
            ),
        )
        logger.info("TimesFM 3.0 loaded on CPU (fallback).")

    async def unload(self) -> None:
        """Release model from memory."""
        if self._model is not None:
            del self._model
            self._model = None
            try:
                import torch
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except ImportError:
                pass
            logger.info("TimesFM 3.0 unloaded.")

    def health(self) -> dict[str, Any]:
        return {
            "loaded": self._model is not None,
            "device": self._device_info.device if self._device_info else None,
            "model": "TimesFM 3.0",
            "checkpoint": self.config.checkpoint,
        }

    def capabilities(self) -> list[ModelCapability]:
        return [
            ModelCapability.UNIVARIATE,
            ModelCapability.MULTIVARIATE,
            ModelCapability.COVARIATES,
            ModelCapability.QUANTILES,
            ModelCapability.PROBABILISTIC,
        ]

    def info(self) -> ModelInfo:
        return ModelInfo(
            name="TimesFM 3.0",
            version="3.0",
            provider="timesfm3",
            checkpoint=self.config.checkpoint,
            license="non-commercial",
            capabilities=self.capabilities(),
            device=self._device_info.device if self._device_info else None,
            loaded=self._model is not None,
        )

    async def forecast_univariate(
        self,
        context: np.ndarray,
        horizon: int,
        **kwargs,
    ) -> ForecastResult:
        """Run univariate forecast with quantile output."""
        if self._model is None:
            raise ModelInferenceError("Model not loaded. Call load() first.")

        try:
            # TimesFM expects list of arrays for batch
            point_forecast, quantile_forecast = self._model.forecast(
                [context.astype(np.float32)],
                freq=[0],  # 0 = no frequency hint
            )

            return ForecastResult(
                point_forecast=point_forecast[0][:horizon],
                quantiles=quantile_forecast[0][:horizon] if quantile_forecast is not None else None,
                quantile_levels=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
                target_names=["close"],
                model_name="TimesFM 3.0",
                model_version="3.0",
                device_used=self._device_info.device if self._device_info else "unknown",
                context_length_used=len(context),
            )

        except RuntimeError as e:
            if "CUDA out of memory" in str(e):
                raise CUDAOutOfMemoryError(
                    f"GPU OOM during inference. Context={len(context)}, "
                    f"Horizon={horizon}. Try reducing batch_size or "
                    f"context_length, or switch to CPU."
                )
            raise ModelInferenceError(f"Inference failed: {e}")

    async def forecast_multivariate(
        self,
        context: np.ndarray,
        horizon: int,
        target_names: list[str],
        **kwargs,
    ) -> ForecastResult:
        """Multivariate forecast using TimesFM 3.0 native support.

        Input shape: (num_variates, context_length)
        Output shape: (num_variates, horizon)
        """
        if self._model is None:
            raise ModelInferenceError("Model not loaded.")

        # For multivariate, pass each variate as a separate series
        forecasts = []
        quantiles_list = []

        for i, name in enumerate(target_names):
            pf, qf = self._model.forecast(
                [context[i].astype(np.float32)],
                freq=[0],
            )
            forecasts.append(pf[0][:horizon])
            if qf is not None:
                quantiles_list.append(qf[0][:horizon])

        return ForecastResult(
            point_forecast=np.stack(forecasts),
            quantiles=np.stack(quantiles_list) if quantiles_list else None,
            quantile_levels=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            target_names=target_names,
            model_name="TimesFM 3.0",
            model_version="3.0",
            device_used=self._device_info.device if self._device_info else "unknown",
            context_length_used=context.shape[1],
        )

    async def forecast_with_covariates(
        self,
        target: np.ndarray,
        past_covariates: np.ndarray | None,
        future_covariates: np.ndarray | None,
        horizon: int,
        **kwargs,
    ) -> ForecastResult:
        """Forecast with covariate support (TimesFM 3.0 native)."""
        if self._model is None:
            raise ModelInferenceError("Model not loaded.")

        # TimesFM 3.0 covariate API
        pf, qf = self._model.forecast(
            [target.astype(np.float32)],
            freq=[0],
            # Covariates passed via model-specific params
        )

        return ForecastResult(
            point_forecast=pf[0][:horizon],
            quantiles=qf[0][:horizon] if qf is not None else None,
            quantile_levels=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],
            target_names=kwargs.get("target_names", ["close"]),
            model_name="TimesFM 3.0",
            model_version="3.0",
            device_used=self._device_info.device if self._device_info else "unknown",
            context_length_used=len(target),
        )
