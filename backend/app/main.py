from __future__ import annotations
"""TimeScope FastAPI application factory."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.api.router import api_router
from app.db.duckdb_manager import DuckDBManager
from app.ml.model_manager import ModelManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    settings = get_settings()
    setup_logging(settings.log_level)

    # Initialize DuckDB
    db_manager = DuckDBManager(settings.duckdb_path)
    db_manager.initialize()
    app.state.db_manager = db_manager

    # Initialize Model Manager (lazy load, no models loaded yet)
    model_manager = ModelManager(settings)
    app.state.model_manager = model_manager

    yield

    # Shutdown: unload models, close DB
    await model_manager.unload_all()
    db_manager.close()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TimeScope",
        description="TimesFM Financial Forecast Research Lab",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS — local-first but configurable
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    return app
