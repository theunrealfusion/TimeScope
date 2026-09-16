from __future__ import annotations
"""Experiment configuration — complete reproducibility."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ExperimentConfig(BaseModel):
    """Full experiment configuration for reproducibility.

    Stored as canonical JSON. A previous experiment can be
    re-run from this configuration alone.
    """
    experiment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str = ""
    symbols: list[str]
    date_range_start: datetime
    date_range_end: datetime
    model: str = "timesfm3"
    model_version: str | None = None
    context_length: int = 512
    forecast_horizon: int = 5
    target_mode: str = "raw_price"
    target_variates: list[str] = ["close"]
    covariates: list[str] = []
    feature_config: dict = {}
    step_size: int = 1
    device: str = "auto"
    random_seed: int = 42
    data_source: str = "yahoo_finance"
    dataset_version: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExperimentResult(BaseModel):
    experiment_id: str
    status: str  # "completed", "failed", "running"
    total_origins: int = 0
    completed_origins: int = 0
    metrics: dict = {}
    per_horizon_metrics: list[dict] = []
    per_regime_metrics: dict = {}
    model_comparison: list[dict] = []
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
