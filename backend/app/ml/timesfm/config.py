"""TimesFM model configuration."""
from pydantic import BaseModel, Field


class TimesFMConfig(BaseModel):
    """Configuration for TimesFM model providers."""
    checkpoint: str = "google/timesfm-3.0-pytorch"
    device_mode: str = "auto"
    context_length: int = Field(default=512, ge=32, le=4096)
    forecast_horizon: int = Field(default=5, ge=1, le=128)
    batch_size: int = Field(default=1, ge=1, le=32)
    gpu_memory_threshold_mb: int = 3500
    quantile_levels: list[float] = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
