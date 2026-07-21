"""Shared feature and forecast-horizon contracts for training and serving."""


SUPPORTED_FORECAST_HORIZONS_HOURS = (1, 3, 6, 12, 24)


ENGINEERED_FEATURE_COLUMNS = [
  "actual_price_lag_1h",
  "actual_price_lag_24h",
  "forecast_price_lag_1h",
  "actual_price_rolling_24h_mean",
  "actual_price_rolling_24h_max",
  "actual_price_rolling_7d_mean",
]

MODEL_FEATURE_COLUMNS = [
  "forecast_price",
  "hour",
  "day_of_week",
  "month",
  "is_weekend",
  *ENGINEERED_FEATURE_COLUMNS,
]

HORIZON_TARGET_COLUMNS = [
  f"actual_price_target_{horizon_hours}h"
  for horizon_hours in SUPPORTED_FORECAST_HORIZONS_HOURS
]

TRAINING_REQUIRED_COLUMNS = [
  *MODEL_FEATURE_COLUMNS,
  *HORIZON_TARGET_COLUMNS,
]


def parse_model_feature_columns(value: object) -> list[str]:
  """Return the ordered feature names recorded in model metadata.

  Feature order is part of the artifact contract. Invalid metadata must fail
  instead of silently changing the estimator input shape.
  """
  if not isinstance(value, str) or not value.strip():
    raise ValueError("Model metadata contains no feature columns.")

  feature_columns = [
    column.strip()
    for column in value.split("|")
    if column.strip()
  ]

  if not feature_columns:
    raise ValueError("Model metadata contains no valid feature columns.")

  return feature_columns
