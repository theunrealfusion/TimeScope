"""LeakageGuard: ensures no future information leaks into features.

This is one of the most critical components. Every feature must be
strictly causal — using only data at or before time t to compute
features at time t.
"""
from datetime import datetime
from typing import Any
import numpy as np
import pandas as pd


class LeakageDetected(Exception):
    """Raised when future information leakage is detected."""
    pass


class LeakageGuard:
    """Validates feature pipelines for temporal leakage.

    Checks:
    1. No future timestamps in rolling windows
    2. No future normalization statistics
    3. No future target contamination
    4. Proper label shifting
    """

    @staticmethod
    def validate_rolling_feature(
        timestamps: pd.DatetimeIndex,
        feature_values: np.ndarray,
        window_size: int,
        feature_name: str,
    ) -> bool:
        """Verify a rolling feature uses only past data.

        For each point t, the feature should depend only on
        data at timestamps <= t.
        """
        # Check that feature has NaN for the first (window-1) points
        # (proper left-aligned rolling)
        expected_nan_count = window_size - 1
        actual_nan_count = np.isnan(feature_values[:expected_nan_count]).sum()

        if actual_nan_count < expected_nan_count:
            raise LeakageDetected(
                f"Feature '{feature_name}': expected {expected_nan_count} "
                f"leading NaNs for window={window_size}, got {actual_nan_count}. "
                "Possible centered or right-aligned window."
            )
        return True

    @staticmethod
    def validate_no_future_in_features(
        feature_df: pd.DataFrame,
        cutoff_timestamp: datetime,
        target_columns: list[str],
    ) -> bool:
        """Ensure features don't contain future target values."""
        mask = feature_df.index > cutoff_timestamp
        if mask.any():
            future_data = feature_df.loc[mask, target_columns]
            if future_data.notna().any().any():
                raise LeakageDetected(
                    f"Found non-NaN target values after cutoff "
                    f"{cutoff_timestamp}: future data is leaking into features."
                )
        return True

    @staticmethod
    def validate_normalization_stats(
        fit_data_end: datetime,
        predict_data_start: datetime,
    ) -> bool:
        """Ensure normalization was fit only on past data."""
        if fit_data_end >= predict_data_start:
            raise LeakageDetected(
                f"Normalization statistics computed on data up to "
                f"{fit_data_end}, but prediction starts at "
                f"{predict_data_start}. "
                "Future data may have been used for normalization."
            )
        return True

    @staticmethod
    def validate_information_cutoff(
        data: pd.DataFrame,
        cutoff: datetime,
        context: str = "",
    ) -> bool:
        """Verify no data after cutoff is accessible."""
        if hasattr(data.index, 'max'):
            max_ts = data.index.max()
        elif 'timestamp' in data.columns:
            max_ts = data['timestamp'].max()
        else:
            return True

        if pd.Timestamp(max_ts) > pd.Timestamp(cutoff):
            raise LeakageDetected(
                f"Data extends to {max_ts}, beyond cutoff {cutoff}. "
                f"Context: {context}"
            )
        return True

    @staticmethod
    def create_synthetic_leakage_test(
        num_sessions: int = 500,
        seed: int = 42,
    ) -> tuple[pd.DataFrame, float]:
        """Create synthetic data with a known future signal.

        Returns data where future values contain an obvious pattern.
        If any feature pipeline can "see" this pattern before the
        cutoff, leakage is present.

        Returns:
            (df, future_signal_value): The data and the injected signal.
        """
        rng = np.random.default_rng(seed)
        dates = pd.bdate_range("2020-01-01", periods=num_sessions)
        close = 100 + np.cumsum(rng.normal(0, 1, num_sessions))

        # Inject a massive signal in the last 50 sessions
        future_signal = 999.0
        close[-50:] = future_signal

        df = pd.DataFrame({
            "timestamp": dates,
            "close": close,
            "volume": rng.integers(1000, 10000, num_sessions).astype(float),
        })

        return df, future_signal
