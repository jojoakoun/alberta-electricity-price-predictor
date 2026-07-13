import pandas as pd
import pytest

from electricity_predictor.features.feature_engineering import (
  add_horizon_target_features,
  add_time_features,
  build_basic_modeling_dataset,
  build_target_column_name,
  build_target_column_names,
)


def test_build_target_column_name_uses_horizon_hours():
  assert build_target_column_name(3) == "actual_price_target_3h"


def test_build_target_column_names_uses_all_horizons():
  assert build_target_column_names([1, 3, 24]) == [
    "actual_price_target_1h",
    "actual_price_target_3h",
    "actual_price_target_24h",
  ]


def test_add_time_features_creates_expected_columns():
  data = pd.DataFrame({
    "datetime_local_time": pd.to_datetime([
      "2026-01-03 18:00:00",
      "2026-01-05 02:00:00",
    ])
  })

  result = add_time_features(data)

  # These features come from Alberta local time and support household usage decisions.
  assert result["hour"].tolist() == [18, 2]
  assert result["day_of_week"].tolist() == [5, 0]
  assert result["month"].tolist() == [1, 1]
  assert result["is_weekend"].tolist() == [1, 0]


def test_add_horizon_target_features_creates_future_price_targets():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2026-01-01 07:00:00",
      "2026-01-01 08:00:00",
      "2026-01-01 09:00:00",
      "2026-01-01 10:00:00",
    ]),
    "actual_price": [30.0, 40.0, 50.0, 60.0],
  })

  result = add_horizon_target_features(
    data=data,
    horizons_hours=[1, 3],
  )

  # Target 1h at the first row is the actual price one hour in the future.
  assert result.loc[0, "actual_price_target_1h"] == 40.0

  # Target 3h at the first row is the actual price three hours in the future.
  assert result.loc[0, "actual_price_target_3h"] == 60.0

  # The final rows naturally have missing targets because the future is not available.
  assert pd.isna(result.loc[3, "actual_price_target_1h"])
  assert pd.isna(result.loc[1, "actual_price_target_3h"])


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

  result = build_basic_modeling_dataset(data, horizons_hours=[1])

  # A supervised model cannot create reliable targets from rows without finalized actual_price.
  assert len(result) == 1
  assert result["actual_price"].tolist() == [30.24]


def test_build_basic_modeling_dataset_returns_expected_columns():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime(["2026-01-01 07:00:00"]),
    "datetime_local_time": pd.to_datetime(["2026-01-01 00:00:00"]),
    "actual_price": [30.24],
    "forecast_price": [28.79],
  })

  result = build_basic_modeling_dataset(data, horizons_hours=[1, 3])

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
    "actual_price_rolling_24h_mean",
    "actual_price_rolling_24h_max",
    "actual_price_rolling_7d_mean",
    "actual_price_target_1h",
    "actual_price_target_3h",
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

  result = build_basic_modeling_dataset(data, horizons_hours=[1])

  # Lag features must use previous values, not the current target value.
  assert pd.isna(result.loc[0, "actual_price_lag_1h"])
  assert result.loc[1, "actual_price_lag_1h"] == 30.00
  assert result.loc[2, "actual_price_lag_1h"] == 40.00

  assert pd.isna(result.loc[0, "forecast_price_lag_1h"])
  assert result.loc[1, "forecast_price_lag_1h"] == 28.00
  assert result.loc[2, "forecast_price_lag_1h"] == 38.00


def test_build_basic_modeling_dataset_adds_rolling_features():
  rows = []

  for hour in range(25):
    rows.append({
      "datetime_universal_time": pd.Timestamp("2026-01-01 07:00:00") + pd.Timedelta(hours=hour),
      "datetime_local_time": pd.Timestamp("2026-01-01 00:00:00") + pd.Timedelta(hours=hour),
      "actual_price": float(hour + 1),
      "forecast_price": float(hour + 1),
    })

  data = pd.DataFrame(rows)

  result = build_basic_modeling_dataset(data, horizons_hours=[1])

  # Rolling features must use past values only, so the current target is excluded.
  assert pd.isna(result.loc[23, "actual_price_rolling_24h_mean"])
  assert result.loc[24, "actual_price_rolling_24h_mean"] == 12.5
  assert result.loc[24, "actual_price_rolling_24h_max"] == 24.0


def test_build_basic_modeling_dataset_rejects_missing_utc_hour():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2026-01-01 07:00:00",
      "2026-01-01 08:00:00",
      "2026-01-01 10:00:00",
    ]),
    "datetime_local_time": pd.to_datetime([
      "2026-01-01 00:00:00",
      "2026-01-01 01:00:00",
      "2026-01-01 03:00:00",
    ]),
    "actual_price": [30.0, 40.0, 60.0],
    "forecast_price": [28.0, 38.0, 58.0],
  })

  with pytest.raises(ValueError, match="continuous hourly UTC timestamps"):
    build_basic_modeling_dataset(data, horizons_hours=[1])

def test_build_basic_modeling_dataset_rejects_duplicate_utc_hour():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2026-01-01 07:00:00",
      "2026-01-01 08:00:00",
      "2026-01-01 08:00:00",
    ]),
    "datetime_local_time": pd.to_datetime([
      "2026-01-01 00:00:00",
      "2026-01-01 01:00:00",
      "2026-01-01 01:00:00",
    ]),
    "actual_price": [30.0, 40.0, 41.0],
    "forecast_price": [28.0, 38.0, 39.0],
  })

  # A repeated hour makes shift(1) mean "same hour" instead of "previous hour".
  with pytest.raises(ValueError, match="continuous hourly UTC timestamps"):
    build_basic_modeling_dataset(data, horizons_hours=[1])


def test_build_basic_modeling_dataset_rejects_gap_created_by_missing_actual_price():
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
    "actual_price": [30.0, None, 50.0],
    "forecast_price": [28.0, 38.0, 48.0],
  })

  # Dropping the mid-series NaN row creates a hidden hourly gap.
  # This test locks in the guard ordering: validation must run AFTER dropna,
  # otherwise silently misaligned lags and targets come back (audit finding B3).
  with pytest.raises(ValueError, match="continuous hourly UTC timestamps"):
    build_basic_modeling_dataset(data, horizons_hours=[1])


def test_build_basic_modeling_dataset_rejects_missing_utc_timestamp():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2026-01-01 07:00:00",
      "2026-01-01 08:00:00",
      None,
    ]),
    "datetime_local_time": pd.to_datetime([
      "2026-01-01 00:00:00",
      "2026-01-01 01:00:00",
      "2026-01-01 02:00:00",
    ]),
    "actual_price": [30.0, 40.0, 50.0],
    "forecast_price": [28.0, 38.0, 48.0],
  })

  # NaT diffs would be silently dropped by the diff check, so the guard
  # must reject missing timestamps explicitly.
  with pytest.raises(ValueError, match="non-missing UTC timestamps"):
    build_basic_modeling_dataset(data, horizons_hours=[1])
