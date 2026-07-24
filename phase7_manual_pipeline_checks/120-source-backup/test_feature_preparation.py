from unittest.mock import patch

import pandas as pd
import pytest

from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
)
from electricity_predictor.worker.feature_preparation import (
  LIVE_INFERENCE_LOOKBACK_HOURS,
  LIVE_REQUIRED_LOOKBACK_HOURS,
  prepare_model_features,
)


def build_hourly_prices(
  periods: int = 220,
) -> pd.DataFrame:
  return pd.DataFrame({
    "datetime_universal_time":
      pd.date_range(
        "2026-01-01",
        periods=periods,
        freq="h",
        tz="UTC",
      ),
    "actual_price": [
      float(value)
      for value in range(periods)
    ],
    "forecast_price": [
      float(value)
      for value in range(periods)
    ],
    "alberta_internal_load": [
      8000.0
      for _ in range(periods)
    ],
    "source": [
      "test"
      for _ in range(periods)
    ],
  })


def prepare_from(
  data: pd.DataFrame,
) -> pd.DataFrame:
  with patch(
    "electricity_predictor.worker."
    "feature_preparation."
    "load_inference_hourly_prices",
    return_value=data,
  ):
    return prepare_model_features()


def test_live_lookback_covers_safe_actual_window():
  with patch(
    "electricity_predictor.worker."
    "feature_preparation."
    "load_inference_hourly_prices",
    return_value=build_hourly_prices(),
  ) as loader:
    prepare_model_features()

  assert (
    loader.call_args.kwargs[
      "lookback_hours"
    ]
    == LIVE_INFERENCE_LOOKBACK_HOURS
  )

  assert (
    LIVE_INFERENCE_LOOKBACK_HOURS
    > LIVE_REQUIRED_LOOKBACK_HOURS
  )


def test_preparation_uses_latest_hour_and_selected_contract():
  result = prepare_from(
    build_hourly_prices()
  )

  assert len(result) == 1

  row = result.iloc[0]

  assert row[
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-10T03:00:00+00:00"
  )

  assert set(
    SELECTED_LIVE_FEATURE_COLUMNS
  ).issubset(
    result.columns
  )

  assert (
    result[
      SELECTED_LIVE_FEATURE_COLUMNS
    ]
    .notna()
    .all(axis=None)
  )

  assert (
    "actual_price_lag_1h"
    not in result.columns
  )


def test_missing_current_forecast_is_rejected():
  data = build_hourly_prices()

  data.loc[
    219,
    "forecast_price",
  ] = pd.NA

  with pytest.raises(
    ValueError,
    match=(
      "missing forecast_price at "
      "2026-01-10T03:00:00\\+00:00"
    ),
  ):
    prepare_from(data)


def test_missing_previous_forecast_is_rejected():
  data = build_hourly_prices()

  data.loc[
    218,
    "forecast_price",
  ] = pd.NA

  with pytest.raises(
    ValueError,
    match=(
      "missing forecast_price at "
      "2026-01-10T02:00:00\\+00:00"
    ),
  ):
    prepare_from(data)


def test_gap_older_than_required_window_is_ignored():
  data = (
    build_hourly_prices()
    .drop(index=10)
    .reset_index(drop=True)
  )

  result = prepare_from(
    data
  )

  assert len(result) == 1


def test_duplicate_older_than_required_window_is_ignored():
  data = build_hourly_prices()

  data = pd.concat(
    [
      data,
      data.iloc[[10]],
    ],
    ignore_index=True,
  )

  result = prepare_from(
    data
  )

  assert len(result) == 1


def test_missing_hour_inside_required_window_is_rejected():
  data = (
    build_hourly_prices()
    .drop(index=100)
    .reset_index(drop=True)
  )

  with pytest.raises(
    ValueError,
    match=(
      "2026-01-05T04:00:00\\+00:00"
    ),
  ):
    prepare_from(data)


def test_missing_safe_actual_is_rejected():
  data = build_hourly_prices()

  data.loc[
    100,
    "actual_price",
  ] = pd.NA

  with pytest.raises(
    ValueError,
    match=(
      "missing required actual_price.*"
      "2026-01-05T04:00:00\\+00:00"
    ),
  ):
    prepare_from(data)


def test_recent_actual_prices_may_be_missing():
  data = build_hourly_prices()

  # H-23 through H are intentionally excluded from safe-actual features.
  data.loc[
    196:,
    "actual_price",
  ] = pd.NA

  result = prepare_from(
    data
  )

  assert len(result) == 1

  assert (
    result[
      SELECTED_LIVE_FEATURE_COLUMNS
    ]
    .notna()
    .all(axis=None)
  )


def test_stale_candidate_hint_is_rejected():
  data = build_hourly_prices()

  data.attrs[
    "inference_candidate_utc"
  ] = pd.Timestamp(
    "2026-01-10T02:00:00+00:00"
  )

  with pytest.raises(
    ValueError,
    match=(
      "candidate must equal the latest"
    ),
  ):
    prepare_from(data)
