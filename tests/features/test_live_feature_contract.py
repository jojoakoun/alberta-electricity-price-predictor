"""Tests for feature contracts designed for current-hour inference."""

import numpy as np
import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.features.live_feature_contract import (
  CONSERVATIVE_ACTUAL_FEATURE_COLUMNS,
  CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS,
  FORECAST_ONLY_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
  add_live_feature_candidates,
  get_live_feature_columns,
)


def build_hourly_prices(
  row_count: int = 240,
) -> pd.DataFrame:
  """Build enough continuous history for all seven-day rolling features."""
  utc_hours = pd.date_range(
    start="2026-01-01T00:00:00Z",
    periods=row_count,
    freq="h",
  )

  actual_prices = np.linspace(
    20.0,
    80.0,
    row_count,
  )

  forecast_prices = (
    actual_prices
    + np.sin(
      np.arange(row_count) / 6
    ) * 5
  )

  local_hours = (
    utc_hours
    .tz_convert(
      "America/Edmonton"
    )
    .tz_localize(None)
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


def test_current_hour_supports_both_live_contracts():
  """Recent missing actuals must not block current-hour feature creation."""
  data = build_hourly_prices()

  data.loc[
    data.index[-3:],
    "actual_price",
  ] = np.nan

  features = add_live_feature_candidates(
    data
  )

  latest_row = features.tail(1)

  assert (
    latest_row[
      FORECAST_ONLY_LIVE_FEATURE_COLUMNS
    ]
    .notna()
    .all(axis=None)
  )

  assert (
    latest_row[
      CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS
    ]
    .notna()
    .all(axis=None)
  )


def test_hybrid_actual_features_ignore_latest_23_hours():
  """Safe actual features must depend only on H-24 or older observations."""
  complete_data = build_hourly_prices()
  delayed_data = complete_data.copy()

  delayed_data.loc[
    delayed_data.index[-23:],
    "actual_price",
  ] = np.nan

  complete_features = (
    add_live_feature_candidates(
      complete_data
    )
    .iloc[-1]
  )

  delayed_features = (
    add_live_feature_candidates(
      delayed_data
    )
    .iloc[-1]
  )

  for column in CONSERVATIVE_ACTUAL_FEATURE_COLUMNS:
    assert delayed_features[column] == pytest.approx(
      complete_features[column]
    )


def test_contract_lookup_returns_ordered_defensive_copy():
  """Callers must not be able to mutate the shared feature contract."""
  first_result = get_live_feature_columns(
    "conservative_hybrid"
  )

  second_result = get_live_feature_columns(
    "conservative_hybrid"
  )

  assert first_result == (
    CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS
  )

  first_result.append(
    "unexpected_column"
  )

  assert second_result == (
    CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS
  )


def test_unknown_live_contract_is_rejected():
  with pytest.raises(
    ValueError,
    match="Unsupported live feature contract",
  ):
    get_live_feature_columns(
      "three_hour_delayed_actual"
    )


def test_active_model_contract_remains_unchanged():
  """Candidate work must not silently alter the currently active models."""
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


def test_conservative_hybrid_is_the_selected_live_contract():
  """The selected contract must remain explicit and reproducible."""
  assert (
    SELECTED_LIVE_FEATURE_CONTRACT
    == "conservative_hybrid"
  )

  assert SELECTED_LIVE_FEATURE_COLUMNS == (
    CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS
  )


def test_selected_live_columns_are_separate_from_contract_registry():
  """Mutating a caller copy must not modify the shared contract registry."""
  selected_copy = list(
    SELECTED_LIVE_FEATURE_COLUMNS
  )

  selected_copy.append(
    "unexpected_column"
  )

  assert (
    "unexpected_column"
    not in CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS
  )
