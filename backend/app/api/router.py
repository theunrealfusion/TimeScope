from __future__ import annotations
from fastapi import APIRouter
from app.api.health import router as health_router
from app.api.models import router as models_router
from app.api.forecast import router as forecast_router
from app.api.market_data import router as market_data_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(models_router, tags=["Models"])
api_router.include_router(forecast_router, tags=["Forecast"])
api_router.include_router(market_data_router, tags=["Market Data"])
