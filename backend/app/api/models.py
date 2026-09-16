from __future__ import annotations
from fastapi import APIRouter, Depends
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
