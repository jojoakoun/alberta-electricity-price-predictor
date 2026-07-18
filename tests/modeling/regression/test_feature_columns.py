from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
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
