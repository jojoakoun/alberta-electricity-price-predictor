from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.features.feature_quality import (
  ENGINEERED_FEATURE_COLUMNS,
  summarize_feature_quality,
)


def test_engineered_feature_columns_include_expected_features():
  assert ENGINEERED_FEATURE_COLUMNS == [
    "actual_price_lag_1h",
    "actual_price_lag_24h",
    "forecast_price_lag_1h",
    "actual_price_rolling_24h_mean",
    "actual_price_rolling_24h_max",
    "actual_price_rolling_7d_mean",
  ]


def test_summarize_feature_quality_counts_missing_engineered_features(tmp_path):
  file_path = tmp_path / "modeling_dataset.csv"

  data = pd.DataFrame({
    "actual_price_lag_1h": [None, 10.0, 20.0],
    "actual_price_lag_24h": [None, None, 5.0],
    "forecast_price_lag_1h": [None, 9.0, 19.0],
    "actual_price_rolling_24h_mean": [None, None, 15.0],
    "actual_price_rolling_24h_max": [None, None, 25.0],
    "actual_price_rolling_7d_mean": [None, None, None],
  })

  data.to_csv(file_path, index=False)

  summary = summarize_feature_quality(file_path)

  # This checks how many rows become unusable because engineered features are missing.
  assert summary["rows"] == 3
  assert summary["columns"] == 6
  assert summary["missing_engineered_features"]["actual_price_lag_1h"] == 1
  assert summary["missing_engineered_features"]["actual_price_lag_24h"] == 2
  assert summary["missing_engineered_features"]["actual_price_rolling_7d_mean"] == 3
  assert summary["rows_after_dropping_missing_engineered_features"] == 0
  assert summary["rows_removed"] == 3


def test_summarize_feature_quality_counts_complete_feature_rows(tmp_path):
  file_path = tmp_path / "modeling_dataset.csv"

  data = pd.DataFrame({
    "actual_price_lag_1h": [None, 10.0, 20.0],
    "actual_price_lag_24h": [None, 8.0, 18.0],
    "forecast_price_lag_1h": [None, 9.0, 19.0],
    "actual_price_rolling_24h_mean": [None, 11.0, 21.0],
    "actual_price_rolling_24h_max": [None, 12.0, 22.0],
    "actual_price_rolling_7d_mean": [None, 13.0, 23.0],
  })

  data.to_csv(file_path, index=False)

  summary = summarize_feature_quality(file_path)

  # The first row is incomplete, while the last two rows are ready for modeling.
  assert summary["rows_after_dropping_missing_engineered_features"] == 2
  assert summary["rows_removed"] == 1


def test_summarize_feature_quality_rejects_missing_file():
  missing_file = Path("missing_modeling_dataset.csv")

  with pytest.raises(FileNotFoundError):
    summarize_feature_quality(missing_file)
