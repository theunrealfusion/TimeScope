from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.features.transforms import TargetMode

class ForecastRequest(BaseModel):
    symbol: str
    model_name: str = "naive"
    horizon: int = Field(5, ge=1, le=128)
    context_length: int = Field(512, ge=32, le=4096)
    target_mode: TargetMode = TargetMode.RAW_PRICE
    cutoff_date: Optional[datetime] = None

class ForecastResponse(BaseModel):
    run_id: str
    symbol: str
    model_name: str
    model_version: str
    device: str
    target_mode: TargetMode
    horizon: int
    context_length: int
    origin_timestamp: str
    point_forecast: List[float]
    forecast_prices: Optional[List[float]] = None
    quantiles: Optional[Dict[str, List[float]]] = None
    reconstruction_method: Optional[str] = None
