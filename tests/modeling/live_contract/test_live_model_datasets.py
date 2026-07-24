"""Tests for isolated current-hour modeling datasets."""

import numpy as np
import pandas as pd

from electricity_predictor.features.feature_columns import (
  HORIZON_TARGET_COLUMNS,
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.live_contract.live_model_datasets import (
  build_live_modeling_dataset,
  build_live_training_dataset,
)


def build_source_data(
  row_count: int = 240,
) -> pd.DataFrame:
  """Build continuous hourly history for seven-day rolling features."""
  utc_hours = pd.date_range(
    start="2025-01-01T00:00:00Z",
    periods=row_count,
    freq="h",
  )

  local_hours = (
    utc_hours
    .tz_convert(
      "America/Edmonton"
    )
    .tz_localize(None)
  )

  actual_prices = np.linspace(
    20.0,
    100.0,
    row_count,
  )

  forecast_prices = (
    actual_prices
    + np.sin(
      np.arange(row_count) / 5
    )
  )

  return pd.DataFrame({
    "datetime_universal_time":
      utc_hours,
    "datetime_local_time":
      local_hours,
    "actual_price":
      actual_prices,
    "forecast_price":
      forecast_prices,
  })


def test_live_modeling_dataset_contains_selected_contract_and_targets():
  data = build_live_modeling_dataset(
    build_source_data()
  )

  for column in [
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *HORIZON_TARGET_COLUMNS,
  ]:
    assert column in data.columns


def test_recent_missing_actuals_do_not_block_current_hour_features():
  source_data = build_source_data()

  source_data.loc[
    source_data.index[-3:],
    "actual_price",
  ] = np.nan

  modeling_data = build_live_modeling_dataset(
    source_data
  )

  latest_row = modeling_data.iloc[-1]

  assert latest_row[
    SELECTED_LIVE_FEATURE_COLUMNS
  ].notna().all()


def test_training_dataset_removes_incomplete_targets_and_features():
  modeling_data = build_live_modeling_dataset(
    build_source_data()
  )

  training_data = build_live_training_dataset(
    modeling_data
  )

  assert (
    training_data[
      [
        *SELECTED_LIVE_FEATURE_COLUMNS,
        *HORIZON_TARGET_COLUMNS,
      ]
    ]
    .notna()
    .all(axis=None)
  )

  assert len(training_data) < len(
    modeling_data
  )


def test_active_model_feature_contract_is_not_switched_early():
  """The old active artifacts remain usable until coordinated migration."""
  assert MODEL_FEATURE_COLUMNS == [
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
  ]

  assert (
    MODEL_FEATURE_COLUMNS
    != SELECTED_LIVE_FEATURE_COLUMNS
  )
