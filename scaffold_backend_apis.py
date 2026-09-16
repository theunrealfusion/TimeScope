import os

files = {
    "app/core/logging.py": """import logging
import sys

def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
""",
    "app/schemas/forecast.py": """from pydantic import BaseModel, Field
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
""",
    "app/api/deps.py": """from fastapi import Request
from app.db.duckdb_manager import DuckDBManager
from app.ml.model_manager import ModelManager

def get_db_manager(request: Request) -> DuckDBManager:
    return request.app.state.db_manager

def get_model_manager(request: Request) -> ModelManager:
    return request.app.state.model_manager
""",
    "app/api/health.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "TimeScope API"}
""",
    "app/api/models.py": """from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from app.api.deps import get_model_manager
from app.ml.model_manager import ModelManager

router = APIRouter()

@router.get("/models")
def list_models(model_manager: ModelManager = Depends(get_model_manager)):
    return {"models": [m.__dict__ for m in model_manager.list_models()]}

@router.post("/models/{model_name}/load")
async def load_model(model_name: str, model_manager: ModelManager = Depends(get_model_manager)):
    info = await model_manager.load_model(model_name)
    return {"status": "loaded", "info": info.__dict__}
""",
    "app/api/forecast.py": """from fastapi import APIRouter, Depends
from app.schemas.forecast import ForecastRequest, ForecastResponse
from app.services.forecast_service import ForecastService
from app.api.deps import get_db_manager, get_model_manager
from app.db.duckdb_manager import DuckDBManager
from app.ml.model_manager import ModelManager

router = APIRouter()

def get_forecast_service(
    db: DuckDBManager = Depends(get_db_manager),
    model_manager: ModelManager = Depends(get_model_manager)
) -> ForecastService:
    return ForecastService(db, model_manager)

@router.post("/forecast", response_model=ForecastResponse)
async def run_forecast(
    request: ForecastRequest,
    service: ForecastService = Depends(get_forecast_service)
):
    return await service.run_forecast(request)
""",
    "app/api/market_data.py": """from fastapi import APIRouter
router = APIRouter()
# placeholder for market data endpoints
""",
    "app/api/router.py": """from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.forecast import router as forecast_router
from app.api.market_data import router as market_data_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(models_router, tags=["Models"])
api_router.include_router(forecast_router, tags=["Forecast"])
api_router.include_router(market_data_router, tags=["Market Data"])
"""
}

base_dir = "/storage/Repositories/TimesFM3/backend"

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)

print("Backend API scaffolded.")
