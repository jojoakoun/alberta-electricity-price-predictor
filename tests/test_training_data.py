from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.features.training_data import (
  build_training_dataset,
  load_modeling_dataset,
)


def build_direct_model_features(row_count: int) -> dict[str, list]:
  return {
    "forecast_price": [30.0] * row_count,
    "hour": [12] * row_count,
    "day_of_week": [2] * row_count,
    "month": [7] * row_count,
    "is_weekend": [0] * row_count,
  }


def test_build_training_dataset_removes_rows_with_missing_model_features_or_targets():
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
    "actual_price_target_1h": [40.0, 50.0, 60.0],
    "actual_price_target_3h": [60.0, 70.0, 80.0],
    "actual_price_target_6h": [90.0, 100.0, 110.0],
    "actual_price_target_12h": [150.0, 160.0, 170.0],
    "actual_price_target_24h": [270.0, 280.0, 290.0],
  })

  result = build_training_dataset(data)

  # Only rows with every artifact input and horizon target are usable.
  assert len(result) == 1
  assert result.loc[0, "actual_price"] == 50.0
  assert result.isna().sum().sum() == 0


def test_build_training_dataset_removes_rows_with_missing_horizon_targets():
  data = pd.DataFrame({
    **build_direct_model_features(2),
    "actual_price_lag_1h": [10.0, 20.0],
    "actual_price_lag_24h": [8.0, 18.0],
    "forecast_price_lag_1h": [9.0, 19.0],
    "actual_price_rolling_24h_mean": [11.0, 21.0],
    "actual_price_rolling_24h_max": [12.0, 22.0],
    "actual_price_rolling_7d_mean": [13.0, 23.0],
    "actual_price_target_1h": [30.0, 40.0],
    "actual_price_target_3h": [50.0, 60.0],
    "actual_price_target_6h": [70.0, 80.0],
    "actual_price_target_12h": [90.0, 100.0],
    "actual_price_target_24h": [110.0, None],
  })

  result = build_training_dataset(data)

  assert len(result) == 1
  assert result.loc[0, "actual_price_target_24h"] == 110.0


def test_build_training_dataset_resets_index_after_dropping_rows():
  data = pd.DataFrame({
    **build_direct_model_features(2),
    "actual_price_lag_1h": [None, 10.0],
    "actual_price_lag_24h": [None, 8.0],
    "forecast_price_lag_1h": [None, 9.0],
    "actual_price_rolling_24h_mean": [None, 11.0],
    "actual_price_rolling_24h_max": [None, 12.0],
    "actual_price_rolling_7d_mean": [None, 13.0],
    "actual_price_target_1h": [None, 20.0],
    "actual_price_target_3h": [None, 30.0],
    "actual_price_target_6h": [None, 40.0],
    "actual_price_target_12h": [None, 50.0],
    "actual_price_target_24h": [None, 60.0],
  })

  result = build_training_dataset(data)

  assert result.index.tolist() == [0]


def test_load_modeling_dataset_rejects_missing_file():
  missing_file = Path("missing_modeling_dataset.csv")

  with pytest.raises(FileNotFoundError):
    load_modeling_dataset(missing_file)


@pytest.mark.parametrize(
  "missing_column",
  ["forecast_price", "hour"],
)
def test_build_training_dataset_rejects_missing_direct_model_feature(
  missing_column,
):
  data = pd.DataFrame({
    **build_direct_model_features(2),
    "actual_price_lag_1h": [10.0, 20.0],
    "actual_price_lag_24h": [8.0, 18.0],
    "forecast_price_lag_1h": [9.0, 19.0],
    "actual_price_rolling_24h_mean": [11.0, 21.0],
    "actual_price_rolling_24h_max": [12.0, 22.0],
    "actual_price_rolling_7d_mean": [13.0, 23.0],
    "actual_price_target_1h": [30.0, 40.0],
    "actual_price_target_3h": [50.0, 60.0],
    "actual_price_target_6h": [70.0, 80.0],
    "actual_price_target_12h": [90.0, 100.0],
    "actual_price_target_24h": [110.0, 120.0],
  })
  expected_value = data.loc[0, missing_column]
  data.loc[1, missing_column] = None

  result = build_training_dataset(data)

  assert len(result) == 1
  assert result.loc[0, missing_column] == expected_value
