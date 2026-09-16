from __future__ import annotations
"""TimeScope CLI — uses the same service layer as the REST API."""
import click
import asyncio
from app.core.config import get_settings
from app.db.duckdb_manager import DuckDBManager
from app.ml.model_manager import ModelManager


@click.group()
def cli():
    """TimeScope — TimesFM Financial Forecast Research Lab"""
    pass


@cli.group()
def data():
    """Market data operations."""
    pass


@data.command()
@click.argument("symbol")
def sync(symbol):
    """Download/update market data for SYMBOL."""
    asyncio.run(_sync_data(symbol))


@data.command("import")
@click.argument("filepath", type=click.Path(exists=True))
def import_csv(filepath):
    """Import market data from CSV file."""
    asyncio.run(_import_csv(filepath))


@cli.command()
@click.argument("symbol")
@click.option("--model", default="timesfm3")
@click.option("--horizon", default=5)
@click.option("--context", default=512)
def forecast(symbol, model, horizon, context):
    """Generate forecast for SYMBOL."""
    asyncio.run(_run_forecast(symbol, model, horizon, context))


@cli.command()
@click.argument("symbol")
@click.option("--model", default="timesfm3")
@click.option("--horizon", default=5)
@click.option("--context", default=512)
@click.option("--step", default=1)
def backtest(symbol, model, horizon, context, step):
    """Run walk-forward backtest for SYMBOL."""
    asyncio.run(_run_backtest(symbol, model, horizon, context, step))


@cli.command()
def models():
    """List available models and their status."""
    settings = get_settings()
    manager = ModelManager(settings)
    for m in manager.list_models():
        status = "✓ loaded" if m.loaded else "○ available"
        license_info = f" [{m.license}]" if m.license else ""
        click.echo(f"  {status} {m.name} v{m.version}{license_info}")


@cli.command("system-info")
def system_info():
    """Display system information."""
    from app.utils.system_info import get_system_info
    info = get_system_info()
    for k, v in info.items():
        click.echo(f"  {k}: {v}")
