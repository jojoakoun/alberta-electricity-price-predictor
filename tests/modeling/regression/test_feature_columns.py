import pytest

from electricity_predictor.features.feature_columns import (
  HORIZON_TARGET_COLUMNS,
  MODEL_FEATURE_COLUMNS,
  SUPPORTED_FORECAST_HORIZONS_HOURS,
  parse_model_feature_columns,
)


def test_regression_feature_columns_include_expected_model_inputs():
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


def test_target_columns_follow_the_supported_horizon_contract():
  assert HORIZON_TARGET_COLUMNS == [
    f"actual_price_target_{horizon_hours}h"
    for horizon_hours in SUPPORTED_FORECAST_HORIZONS_HOURS
  ]


def test_parse_model_feature_columns_preserves_artifact_order():
  assert parse_model_feature_columns(
    "forecast_price|actual_price_lag_1h"
  ) == [
    "forecast_price",
    "actual_price_lag_1h",
  ]


@pytest.mark.parametrize("invalid_value", [None, "", " | "])
def test_parse_model_feature_columns_rejects_invalid_metadata(
  invalid_value: object,
):
  with pytest.raises(ValueError, match="feature columns"):
    parse_model_feature_columns(invalid_value)
