# TimeScope 📈

TimeScope is a production-quality, local-first research application that enables rigorous investigation of Google's TimesFM time-series foundation models on historical equity-market data using leakage-free walk-forward backtesting. 

It combines a FastAPI backend with DuckDB/Parquet analytics, multiple forecasting model providers (TimesFM 3.0, TimesFM 2.5, and statistical/ML baselines), and a React TypeScript dashboard—all designed to run on a single developer workstation with a 4 GB VRAM GPU.

## Key Features
- **Local-First AI Research**: Run Google's powerful zero-shot foundation models (TimesFM 3.0 & 2.5) entirely locally.
- **Leakage Guard Engine**: Strictly causal transformations to prevent future information leakage during feature engineering.
- **DuckDB + Parquet Analytics**: High-performance, columnar time-series data storage and analysis.
- **Walk-Forward Backtesting**: Production-grade rolling-origin evaluation.
- **Comprehensive Metrics**: Point metrics (MAE, RMSE, MAPE) and probabilistic metrics (Pinball loss, interval coverage, calibration) support.
- **Device Management Engine**: Carefully manages execution between CPU and GPU dynamically to avoid OOM on smaller GPUs (e.g., 4GB VRAM).

## Prerequisites
- Python 3.10+
- Node.js 18+
- GPU with 4GB+ VRAM (NVIDIA recommended for CUDA support)
- Docker & Docker Compose (optional, for containerized deployments)

> **Note regarding TimesFM Models:** Google's TimesFM 3.0 pretrained weights are under a non-commercial license. Please ensure your usage complies with this license.

## Setup Instructions

### 1. Backend Setup (Local)
Navigate to the backend directory and set up a Python virtual environment:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install core dependencies (ensure you install the torch version of timesfm)
pip install -r requirements.txt
# (Alternatively, manually install dependencies if a requirements.txt is not yet generated)
pip install fastapi uvicorn duckdb pandas numpy pydantic pydantic-settings yfinance
pip install timesfm[torch]
```

Run the backend development server:
```bash
uvicorn app.main:create_app --reload --port 8000
```
The API will be available at `http://localhost:8000/api`.

### 2. Frontend Setup (Local)
Navigate to the frontend directory:

```bash
cd frontend
npm install
```

Start the Vite development server:
```bash
npm run dev
```
The frontend dashboard will be available at `http://localhost:5173`.

### 3. Docker Deployment
If you prefer running everything in containers, you can use the provided docker-compose configuration.

For CPU-only environments:
```bash
docker-compose up --build
```

For GPU-accelerated environments:
```bash
docker-compose -f docker-compose.gpu.yml up --build
```

## Architecture

- **Backend**: FastAPI + DuckDB/SQLite + Pandas + TimesFM
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Data Providers**: Yahoo Finance (NSE & US Equities natively supported), Synthetic data generators

## License

This project itself is open source. However, **TimesFM 3.0** weights carry a non-commercial license. Do not redistribute the model weights. Users must download the checkpoints directly from HuggingFace (`google/timesfm-3.0-pytorch`).

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.
