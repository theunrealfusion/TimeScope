from __future__ import annotations
"""Application configuration using Pydantic Settings."""
from enum import Enum
from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class DeviceMode(str, Enum):
    AUTO = "auto"
    CUDA = "cuda"
    CPU = "cpu"


class MetadataBackend(str, Enum):
    SQLITE = "sqlite"
    MONGODB = "mongodb"


class Settings(BaseSettings):
    # Application
    app_name: str = "TimeScope"
    debug: bool = False
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Data paths
    data_dir: Path = Path("data")
    duckdb_path: Path = Path("data/timescope.duckdb")

    # Metadata backend
    metadata_backend: MetadataBackend = MetadataBackend.SQLITE
    sqlite_path: Path = Path("data/timescope_metadata.db")
    mongodb_uri: str | None = None
    mongodb_database: str = "timescope"

    # TimesFM defaults
    device_mode: DeviceMode = DeviceMode.AUTO
    default_context_length: int = 512
    default_forecast_horizon: int = 5
    default_batch_size: int = 1
    gpu_memory_threshold_mb: int = 3500  # Reserve ~500MB of 4GB

    # TimesFM model paths
    timesfm3_checkpoint: str = "google/timesfm-3.0-pytorch"
    timesfm25_checkpoint: str = "google/timesfm-2.5-200m-transformers"

    # Market data
    default_timezone: str = "Asia/Kolkata"
    max_import_file_size_mb: int = 100

    model_config = {"env_prefix": "TIMESCOPE_", "env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
