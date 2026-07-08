import pandas as pd

from electricity_predictor.features.feature_engineering import (
  add_time_features,
  build_basic_modeling_dataset,
)


def test_add_time_features_creates_expected_columns():
  data = pd.DataFrame({
    "datetime_local_time": pd.to_datetime([
      "2026-01-03 18:00:00",  # Saturday evening
      "2026-01-05 02:00:00",  # Monday early morning
    ])
  })

  result = add_time_features(data)

  # These features come from Alberta local time and support household usage decisions.
  assert result["hour"].tolist() == [18, 2]
  assert result["day_of_week"].tolist() == [5, 0]
  assert result["month"].tolist() == [1, 1]
  assert result["is_weekend"].tolist() == [1, 0]


def test_build_basic_modeling_dataset_removes_missing_target_rows():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2026-01-01 07:00:00",
      "2026-01-01 08:00:00",
    ]),
    "datetime_local_time": pd.to_datetime([
      "2026-01-01 00:00:00",
      "2026-01-01 01:00:00",
    ]),
    "actual_price": [30.24, None],
    "forecast_price": [28.79, 29.10],
  })

  result = build_basic_modeling_dataset(data)

  # A supervised model cannot train on rows where the target value is not finalized.
  assert len(result) == 1
  assert result["actual_price"].tolist() == [30.24]


def test_build_basic_modeling_dataset_returns_expected_columns():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime(["2026-01-01 07:00:00"]),
    "datetime_local_time": pd.to_datetime(["2026-01-01 00:00:00"]),
    "actual_price": [30.24],
    "forecast_price": [28.79],
  })

  result = build_basic_modeling_dataset(data)

  assert result.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
    "actual_price_lag_1h",
    "actual_price_lag_24h",
    "forecast_price_lag_1h",
  ]


def test_build_basic_modeling_dataset_adds_lag_features():
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
    "actual_price": [30.00, 40.00, 50.00],
    "forecast_price": [28.00, 38.00, 48.00],
  })

  result = build_basic_modeling_dataset(data)

  # Lag features must use previous values, not the current target value.
  assert pd.isna(result.loc[0, "actual_price_lag_1h"])
  assert result.loc[1, "actual_price_lag_1h"] == 30.00
  assert result.loc[2, "actual_price_lag_1h"] == 40.00

  assert pd.isna(result.loc[0, "forecast_price_lag_1h"])
  assert result.loc[1, "forecast_price_lag_1h"] == 28.00
  assert result.loc[2, "forecast_price_lag_1h"] == 38.00