from unittest.mock import patch

import pandas as pd
import pytest

from electricity_predictor.features.feature_engineering import (
  ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
)
from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)


def build_hourly_prices(
  periods: int = 200,
) -> pd.DataFrame:
  return pd.DataFrame(
    {
      "datetime_universal_time": pd.date_range(
        "2026-01-01",
        periods=periods,
        freq="h",
        tz="UTC",
      ),
      "actual_price": [float(value) for value in range(periods)],
      "forecast_price": [float(value) for value in range(periods)],
      "alberta_internal_load": [8000.0] * periods,
      "source": ["pipeline"] * periods,
    }
  )


def prepare_from(raw: pd.DataFrame) -> pd.DataFrame:
  with patch(
    "electricity_predictor.worker.feature_preparation."
    "load_inference_hourly_prices",
    return_value=raw,
  ):
    return prepare_model_features()


def test_inference_support_covers_longest_active_rolling_feature() -> None:
  with patch(
    "electricity_predictor.worker.feature_preparation."
    "load_inference_hourly_prices",
    return_value=build_hourly_prices(),
  ) as load_prices:
    prepare_model_features()

  lookback_hours = load_prices.call_args.kwargs[
    "lookback_hours"
  ]

  assert (
    lookback_hours
    >= ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
  )


def test_prepare_model_features_builds_complete_candidate_with_forecast_support() -> None:
  result = prepare_from(build_hourly_prices())

  assert len(result) == 1
  latest = result.iloc[-1]

  assert "datetime_local_time" in result.columns
  assert "actual_price_target_1h" not in result.columns
  assert latest[
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-09T07:00:00+00:00"
  )
  assert latest["forecast_price"] == 199.0
  assert latest["actual_price_lag_1h"] == 198.0
  assert latest["actual_price_lag_24h"] == 175.0
  assert latest["forecast_price_lag_1h"] == 198.0
  assert pd.notna(latest["actual_price_rolling_7d_mean"])


def test_prepare_model_features_rejects_missing_candidate_forecast_price() -> None:
  raw = build_hourly_prices()
  raw.loc[199, "forecast_price"] = pd.NA

  with pytest.raises(
    ValueError,
    match=(
      "missing forecast_price at "
      "2026-01-09T07:00:00\\+00:00"
    ),
  ):
    prepare_from(raw)


def test_prepare_model_features_rejects_missing_previous_forecast_price() -> None:
  raw = build_hourly_prices()
  raw.loc[198, "forecast_price"] = pd.NA

  with pytest.raises(
    ValueError,
    match=(
      "missing forecast_price at "
      "2026-01-09T06:00:00\\+00:00"
    ),
  ):
    prepare_from(raw)


def test_prepare_model_features_ignores_gap_older_than_inference_window() -> None:
  raw = build_hourly_prices(periods=201).drop(
    index=10
  ).reset_index(drop=True)

  result = prepare_from(raw)

  assert result.iloc[-1][
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-09T08:00:00+00:00"
  )


def test_prepare_model_features_ignores_duplicate_older_than_inference_window() -> None:
  raw = build_hourly_prices(periods=201)
  raw = pd.concat(
    [raw, raw.iloc[[10]]],
    ignore_index=True,
  )

  result = prepare_from(raw)

  assert result.iloc[-1][
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-09T08:00:00+00:00"
  )


def test_prepare_model_features_names_missing_hour_inside_inference_window() -> None:
  raw = build_hourly_prices().drop(
    index=100
  ).reset_index(drop=True)

  with pytest.raises(
    ValueError,
    match="2026-01-05T04:00:00\\+00:00",
  ):
    prepare_from(raw)


def test_prepare_model_features_names_missing_hour_at_window_boundary() -> None:
  raw = build_hourly_prices().drop(
    index=31
  ).reset_index(drop=True)

  with pytest.raises(
    ValueError,
    match="2026-01-02T07:00:00\\+00:00",
  ):
    prepare_from(raw)


def test_prepare_model_features_rejects_missing_required_actual_without_imputation() -> None:
  raw = build_hourly_prices()
  raw.loc[100, "actual_price"] = pd.NA

  with pytest.raises(
    ValueError,
    match=(
      "missing finalized actual price.*"
      "2026-01-05T04:00:00\\+00:00"
    ),
  ):
    prepare_from(raw)


def test_prepare_model_features_anchors_after_latest_finalized_actual() -> None:
  raw = build_hourly_prices()
  raw.loc[195:, "actual_price"] = pd.NA

  result = prepare_from(raw)

  assert result.iloc[-1][
    "datetime_universal_time"
  ] == pd.Timestamp(
    "2026-01-09T03:00:00+00:00"
  )
  assert result.iloc[-1]["actual_price_lag_1h"] == 194.0
  assert result.iloc[-1][
    "actual_price_rolling_7d_mean"
  ] == pytest.approx(
    sum(range(27, 195))
    / ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
  )
