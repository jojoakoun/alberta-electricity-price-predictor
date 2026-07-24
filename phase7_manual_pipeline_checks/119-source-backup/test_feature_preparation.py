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
  return pd.DataFrame(
    {
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
      ] * periods,
      "source": [
        "pipeline"
      ] * periods,
    }
  )


def prepare_from(
  raw: pd.DataFrame,
) -> pd.DataFrame:
  with patch(
    "electricity_predictor.worker."
    "feature_preparation."
    "load_inference_hourly_prices",
    return_value=raw,
  ):
    return prepare_model_features()


def test_inference_support_covers_safe_actual_rolling_window():
  with patch(
    "electricity_predictor.worker."
    "feature_preparation."
    "load_inference_hourly_prices",
    return_value=(
      build_hourly_prices()
    ),
  ) as load_prices:
    prepare_model_features()

  assert (
    load_prices.call_args.kwargs[
      "lookback_hours"
    ]
    == LIVE_INFERENCE_LOOKBACK_HOURS
  )

  assert (
    LIVE_INFERENCE_LOOKBACK_HOURS
    > LIVE_REQUIRED_LOOKBACK_HOURS
  )


def test_prepare_model_features_builds_current_hour_live_contract():
  result = prepare_from(
    build_hourly_prices()
  )

  assert len(result) == 1

  latest = result.iloc[0]

  assert latest[
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-10T03:00:00+00:00"
  )

  assert "datetime_local_time" in (
    result.columns
  )

  assert "actual_price_target_1h" not in (
    result.columns
  )

  assert set(
    SELECTED_LIVE_FEATURE_COLUMNS
  ).issubset(
    result.columns
  )

  assert latest[
    "forecast_price"
  ] == 219.0

  assert latest[
    "forecast_price_lag_1h"
  ] == 218.0

  assert latest[
    "forecast_price_lag_24h"
  ] == 195.0

  assert latest[
    "actual_price_lag_24h"
  ] == 195.0

  assert latest[
    "actual_price_safe_24h_max"
  ] == 195.0

  assert latest[
    "actual_price_safe_24h_mean"
  ] == pytest.approx(
    sum(
      range(
        172,
        196,
      )
    )
    / 24
  )

  assert latest[
    "actual_price_safe_7d_mean"
  ] == pytest.approx(
    sum(
      range(
        28,
        196,
      )
    )
    / 168
  )

  assert (
    "actual_price_lag_1h"
    not in result.columns
  )


def test_missing_current_forecast_names_timestamp():
  raw = build_hourly_prices()

  raw.loc[
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
    prepare_from(raw)


def test_missing_previous_forecast_names_timestamp():
  raw = build_hourly_prices()

  raw.loc[
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
    prepare_from(raw)


def test_gap_older_than_required_window_is_ignored():
  raw = (
    build_hourly_prices()
    .drop(index=10)
    .reset_index(drop=True)
  )

  result = prepare_from(raw)

  assert result.iloc[0][
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-10T03:00:00+00:00"
  )


def test_duplicate_older_than_required_window_is_ignored():
  raw = build_hourly_prices()

  raw = pd.concat(
    [
      raw,
      raw.iloc[[10]],
    ],
    ignore_index=True,
  )

  result = prepare_from(raw)

  assert result.iloc[0][
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-10T03:00:00+00:00"
  )


def test_missing_hour_inside_required_window_is_rejected():
  raw = (
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
    prepare_from(raw)


def test_missing_hour_at_required_boundary_is_rejected():
  raw = (
    build_hourly_prices()
    .drop(index=28)
    .reset_index(drop=True)
  )

  with pytest.raises(
    ValueError,
    match=(
      "2026-01-02T04:00:00\\+00:00"
    ),
  ):
    prepare_from(raw)


def test_missing_required_safe_actual_names_timestamp():
  raw = build_hourly_prices()

  raw.loc[
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
    prepare_from(raw)


def test_recent_actual_prices_may_be_missing():
  raw = build_hourly_prices()

  # H-23 through H may be unavailable because live features stop at H-24.
  raw.loc[
    196:,
    "actual_price",
  ] = pd.NA

  result = prepare_from(raw)

  latest = result.iloc[0]

  assert latest[
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-10T03:00:00+00:00"
  )

  assert latest[
    "actual_price_lag_24h"
  ] == 195.0

  assert pd.notna(
    latest[
      "actual_price_safe_7d_mean"
    ]
  )
