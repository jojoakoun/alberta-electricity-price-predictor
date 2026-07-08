from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.features.training_data import (
  build_training_dataset,
  load_modeling_dataset,
)


def test_build_training_dataset_removes_rows_with_missing_engineered_features():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2026-01-01 07:00:00",
      "2026-01-01 08:00:00",
      "2026-01-01 09:00:00",
    ]),
    "datetime_local_time": pd.to_datetime([
      "2026-01-01 00:00:00",
      "2026-01-01 01:00:00",
      "2026-01-01 02:00:00",
    ]),
    "actual_price": [30.0, 40.0, 50.0],
    "forecast_price": [28.0, 38.0, 48.0],
    "hour": [0, 1, 2],
    "day_of_week": [3, 3, 3],
    "month": [1, 1, 1],
    "is_weekend": [0, 0, 0],
    "actual_price_lag_1h": [None, 30.0, 40.0],
    "actual_price_lag_24h": [None, None, 20.0],
    "forecast_price_lag_1h": [None, 28.0, 38.0],
    "actual_price_rolling_24h_mean": [None, None, 35.0],
    "actual_price_rolling_24h_max": [None, None, 40.0],
    "actual_price_rolling_7d_mean": [None, None, 33.0],
  })

  result = build_training_dataset(data)

  # Only rows with complete engineered features are ready for model training.
  assert len(result) == 1
  assert result.loc[0, "actual_price"] == 50.0
  assert result.isna().sum().sum() == 0


def test_build_training_dataset_resets_index_after_dropping_rows():
  data = pd.DataFrame({
    "actual_price_lag_1h": [None, 10.0],
    "actual_price_lag_24h": [None, 8.0],
    "forecast_price_lag_1h": [None, 9.0],
    "actual_price_rolling_24h_mean": [None, 11.0],
    "actual_price_rolling_24h_max": [None, 12.0],
    "actual_price_rolling_7d_mean": [None, 13.0],
  })

  result = build_training_dataset(data)

  # Resetting the index keeps the training dataset clean after rows are removed.
  assert result.index.tolist() == [0]


def test_load_modeling_dataset_rejects_missing_file():
  missing_file = Path("missing_modeling_dataset.csv")

  with pytest.raises(FileNotFoundError):
    load_modeling_dataset(missing_file)
