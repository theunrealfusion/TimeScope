from __future__ import annotations
from fastapi import APIRouter, Depends
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
