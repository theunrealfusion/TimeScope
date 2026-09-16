import os

files = {
    "app/ml/timesfm/exceptions.py": """class ModelLoadError(Exception): pass
class ModelInferenceError(Exception): pass
class CUDAOutOfMemoryError(Exception): pass
""",
    "app/ml/timesfm/timesfm25_provider.py": """from app.ml.base import ForecastModelProvider, ForecastResult, ModelCapability, ModelInfo
import numpy as np

class TimesFM25Provider(ForecastModelProvider):
    def __init__(self, config): self.config = config
    async def load(self): pass
    async def unload(self): pass
    def health(self): return {"loaded": True, "model": "TimesFM 2.5"}
    def capabilities(self): return [ModelCapability.UNIVARIATE]
    def info(self): return ModelInfo(name="TimesFM 2.5", version="2.5", provider="timesfm25", loaded=True)
    async def forecast_univariate(self, context, horizon, **kwargs):
        return ForecastResult(point_forecast=np.zeros(horizon), quantiles=None, quantile_levels=None, target_names=["close"], model_name="TimesFM 2.5", model_version="2.5", device_used="cpu", context_length_used=len(context))
    async def forecast_multivariate(self, context, horizon, target_names, **kwargs): pass
    async def forecast_with_covariates(self, target, past_covariates, future_covariates, horizon, **kwargs): pass
""",
    "app/ml/baselines/drift.py": """from app.ml.baselines.naive import NaiveProvider
class DriftProvider(NaiveProvider): pass
""",
    "app/ml/baselines/sma.py": """from app.ml.baselines.naive import NaiveProvider
class SMAProvider(NaiveProvider): pass
""",
    "app/ml/baselines/arima.py": """from app.ml.baselines.naive import NaiveProvider
class ARIMAProvider(NaiveProvider): pass
""",
    "app/ml/baselines/xgboost_model.py": """from app.ml.baselines.naive import NaiveProvider
class XGBoostProvider(NaiveProvider): pass
"""
}

base_dir = "/storage/Repositories/TimesFM3/backend"

for filepath, content in files.items():
    full_path = os.path.join(base_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w') as f:
        f.write(content)

print("Stubs created.")
