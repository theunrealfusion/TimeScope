from __future__ import annotations
"""DuckDB connection manager with Parquet integration."""
import duckdb
from pathlib import Path
from contextlib import contextmanager
import threading


class DuckDBManager:
    """Thread-safe DuckDB connection manager.

    Manages a single DuckDB database file with support for
    concurrent reads via separate connections.
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._write_lock = threading.Lock()
        self._conn: duckdb.DuckDBPyConnection | None = None

    def initialize(self):
        """Create database and tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self.db_path))
        self._create_tables()

    def _create_tables(self):
        """Create core analytical tables."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS market_data (
                symbol VARCHAR NOT NULL,
                market VARCHAR,
                exchange VARCHAR,
                timestamp TIMESTAMPTZ NOT NULL,
                timezone VARCHAR NOT NULL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE NOT NULL,
                adjusted_close DOUBLE,
                volume DOUBLE,
                source VARCHAR NOT NULL,
                retrieved_at TIMESTAMPTZ,
                dataset_version VARCHAR,
                PRIMARY KEY (symbol, timestamp)
            );

            CREATE TABLE IF NOT EXISTS forecast_runs (
                id VARCHAR PRIMARY KEY,
                experiment_id VARCHAR,
                symbol VARCHAR NOT NULL,
                origin_timestamp TIMESTAMPTZ NOT NULL,
                information_cutoff TIMESTAMPTZ NOT NULL,
                horizon INTEGER NOT NULL,
                model_name VARCHAR NOT NULL,
                model_version VARCHAR,
                device VARCHAR,
                context_length INTEGER,
                target_mode VARCHAR,
                target_variates VARCHAR[],
                created_at TIMESTAMPTZ DEFAULT now()
            );

            CREATE TABLE IF NOT EXISTS forecast_points (
                run_id VARCHAR NOT NULL REFERENCES forecast_runs(id),
                target_name VARCHAR NOT NULL,
                step INTEGER NOT NULL,
                forecast_timestamp TIMESTAMPTZ,
                point_forecast DOUBLE,
                q10 DOUBLE, q20 DOUBLE, q30 DOUBLE,
                q40 DOUBLE, q50 DOUBLE, q60 DOUBLE,
                q70 DOUBLE, q80 DOUBLE, q90 DOUBLE,
                actual_value DOUBLE,
                absolute_error DOUBLE,
                percentage_error DOUBLE,
                direction_predicted INTEGER,
                direction_actual INTEGER,
                PRIMARY KEY (run_id, target_name, step)
            );

            CREATE TABLE IF NOT EXISTS data_quality_reports (
                id VARCHAR PRIMARY KEY,
                symbol VARCHAR NOT NULL,
                checked_at TIMESTAMPTZ DEFAULT now(),
                total_rows INTEGER,
                duplicate_timestamps INTEGER,
                missing_sessions INTEGER,
                nan_count INTEGER,
                inf_count INTEGER,
                negative_prices INTEGER,
                zero_volume INTEGER,
                ohlc_violations INTEGER,
                suspicious_jumps INTEGER,
                issues_json VARCHAR,
                passed BOOLEAN
            );
        """)

    @contextmanager
    def read_connection(self):
        """Get a read-only connection."""
        conn = duckdb.connect(str(self.db_path), read_only=True)
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def write_connection(self):
        """Get a write connection with thread safety."""
        with self._write_lock:
            yield self._conn

    def close(self):
        if self._conn:
            self._conn.close()
