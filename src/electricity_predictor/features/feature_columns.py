ENGINEERED_FEATURE_COLUMNS = [
  "actual_price_lag_1h",
  "actual_price_lag_24h",
  "forecast_price_lag_1h",
  "actual_price_rolling_24h_mean",
  "actual_price_rolling_24h_max",
  "actual_price_rolling_7d_mean",
]

HORIZON_TARGET_COLUMNS = [
  "actual_price_target_1h",
  "actual_price_target_3h",
  "actual_price_target_6h",
  "actual_price_target_12h",
  "actual_price_target_24h",
]

TRAINING_REQUIRED_COLUMNS = [
  *ENGINEERED_FEATURE_COLUMNS,
  *HORIZON_TARGET_COLUMNS,
]
