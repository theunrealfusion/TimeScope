from __future__ import annotations
from fastapi import Request
from app.db.duckdb_manager import DuckDBManager
from app.ml.model_manager import ModelManager

def get_db_manager(request: Request) -> DuckDBManager:
    return request.app.state.db_manager

def get_model_manager(request: Request) -> ModelManager:
    return request.app.state.model_manager
