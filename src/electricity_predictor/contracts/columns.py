"""Authoritative WattWise column and feature contracts.

Reusable dataframe columns, feature groups, targets, and metadata schemas are
defined here. Report-specific output schemas stay beside the report code that
uses them.
"""

from __future__ import annotations


# Forecast horizons shared by research, lifecycle, serving, and the worker.
SUPPORTED_FORECAST_HORIZONS_HOURS = (
  1,
  3,
  6,
  12,
  24,
)


# Canonical timestamps used after ingestion.
DATETIME_COLUMN = "datetime_universal_time"
LOCAL_DATETIME_COLUMN = "datetime_local_time"


# Canonical Alberta electricity-market values.
ACTUAL_PRICE_COLUMN = "actual_price"
FORECAST_PRICE_COLUMN = "forecast_price"
ALBERTA_INTERNAL_LOAD_COLUMN = "alberta_internal_load"

# Regression code historically uses TARGET_COLUMN for the observed pool price.
TARGET_COLUMN = ACTUAL_PRICE_COLUMN


# Calendar feature columns.
HOUR_COLUMN = "hour"
DAY_OF_WEEK_COLUMN = "day_of_week"
MONTH_COLUMN = "month"
IS_WEEKEND_COLUMN = "is_weekend"


# Historical benchmark feature columns.
ACTUAL_PRICE_LAG_1H_COLUMN = "actual_price_lag_1h"
ACTUAL_PRICE_LAG_24H_COLUMN = "actual_price_lag_24h"
FORECAST_PRICE_LAG_1H_COLUMN = "forecast_price_lag_1h"

ACTUAL_PRICE_ROLLING_24H_MEAN_COLUMN = (
  "actual_price_rolling_24h_mean"
)
ACTUAL_PRICE_ROLLING_24H_MAX_COLUMN = (
  "actual_price_rolling_24h_max"
)
ACTUAL_PRICE_ROLLING_7D_MEAN_COLUMN = (
  "actual_price_rolling_7d_mean"
)


# Forecast-derived live feature columns.
FORECAST_PRICE_LAG_24H_COLUMN = "forecast_price_lag_24h"
FORECAST_PRICE_ROLLING_24H_MEAN_COLUMN = (
  "forecast_price_rolling_24h_mean"
)
FORECAST_PRICE_ROLLING_24H_MAX_COLUMN = (
  "forecast_price_rolling_24h_max"
)
FORECAST_PRICE_ROLLING_7D_MEAN_COLUMN = (
  "forecast_price_rolling_7d_mean"
)


# Leakage-safe actual-price features stop at least 24 hours behind source time.
ACTUAL_PRICE_SAFE_24H_MEAN_COLUMN = (
  "actual_price_safe_24h_mean"
)
ACTUAL_PRICE_SAFE_24H_MAX_COLUMN = (
  "actual_price_safe_24h_max"
)
ACTUAL_PRICE_SAFE_7D_MEAN_COLUMN = (
  "actual_price_safe_7d_mean"
)


# External source names mapped into the canonical WattWise schema.
API_COLUMNS = {
  "begin_datetime_utc": DATETIME_COLUMN,
  "begin_datetime_mpt": LOCAL_DATETIME_COLUMN,
  "pool_price": ACTUAL_PRICE_COLUMN,
  "forecast_pool_price": FORECAST_PRICE_COLUMN,
}

RAW_COLUMNS = {
  "Date_Begin_GMT": DATETIME_COLUMN,
  "Date_Begin_Local": LOCAL_DATETIME_COLUMN,
  "ACTUAL_POOL_PRICE": ACTUAL_PRICE_COLUMN,
  "HOUR_AHEAD_POOL_PRICE_FORECAST": FORECAST_PRICE_COLUMN,
  "ACTUAL_AIL": ALBERTA_INTERNAL_LOAD_COLUMN,
}


# Historical research contract retained for reproducible benchmark comparisons.
ENGINEERED_FEATURE_COLUMNS = [
  ACTUAL_PRICE_LAG_1H_COLUMN,
  ACTUAL_PRICE_LAG_24H_COLUMN,
  FORECAST_PRICE_LAG_1H_COLUMN,
  ACTUAL_PRICE_ROLLING_24H_MEAN_COLUMN,
  ACTUAL_PRICE_ROLLING_24H_MAX_COLUMN,
  ACTUAL_PRICE_ROLLING_7D_MEAN_COLUMN,
]

MODEL_FEATURE_COLUMNS = [
  FORECAST_PRICE_COLUMN,
  HOUR_COLUMN,
  DAY_OF_WEEK_COLUMN,
  MONTH_COLUMN,
  IS_WEEKEND_COLUMN,
  *ENGINEERED_FEATURE_COLUMNS,
]

# Classification research models intentionally share the benchmark features.
CLASSIFICATION_FEATURE_COLUMNS = MODEL_FEATURE_COLUMNS


# Live features that rely only on calendar and AESO forecast information.
FORECAST_DERIVED_FEATURE_COLUMNS = [
  FORECAST_PRICE_COLUMN,
  FORECAST_PRICE_LAG_1H_COLUMN,
  FORECAST_PRICE_LAG_24H_COLUMN,
  FORECAST_PRICE_ROLLING_24H_MEAN_COLUMN,
  FORECAST_PRICE_ROLLING_24H_MAX_COLUMN,
  FORECAST_PRICE_ROLLING_7D_MEAN_COLUMN,
]

LIVE_TIME_FEATURE_COLUMNS = [
  HOUR_COLUMN,
  DAY_OF_WEEK_COLUMN,
  MONTH_COLUMN,
  IS_WEEKEND_COLUMN,
]

FORECAST_ONLY_LIVE_FEATURE_COLUMNS = [
  *LIVE_TIME_FEATURE_COLUMNS,
  *FORECAST_DERIVED_FEATURE_COLUMNS,
]


# Live actual-price features that are safe against normal finalization delays.
CONSERVATIVE_ACTUAL_FEATURE_COLUMNS = [
  ACTUAL_PRICE_LAG_24H_COLUMN,
  ACTUAL_PRICE_SAFE_24H_MEAN_COLUMN,
  ACTUAL_PRICE_SAFE_24H_MAX_COLUMN,
  ACTUAL_PRICE_SAFE_7D_MEAN_COLUMN,
]

CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS = [
  *FORECAST_ONLY_LIVE_FEATURE_COLUMNS,
  *CONSERVATIVE_ACTUAL_FEATURE_COLUMNS,
]

LIVE_FEATURE_CONTRACTS = {
  "forecast_only": FORECAST_ONLY_LIVE_FEATURE_COLUMNS,
  "conservative_hybrid":
    CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS,
}

# Training and hourly prediction must use this same selected live contract.
SELECTED_LIVE_FEATURE_CONTRACT = "conservative_hybrid"

SELECTED_LIVE_FEATURE_COLUMNS = list(
  LIVE_FEATURE_CONTRACTS[
    SELECTED_LIVE_FEATURE_CONTRACT
  ]
)


# Horizon-specific supervised-learning targets.
HORIZON_TARGET_COLUMNS = [
  f"actual_price_target_{horizon_hours}h"
  for horizon_hours
  in SUPPORTED_FORECAST_HORIZONS_HOURS
]

TRAINING_REQUIRED_COLUMNS = [
  *MODEL_FEATURE_COLUMNS,
  *HORIZON_TARGET_COLUMNS,
]


# Shared baseline input columns.
BASELINE_PRICE_COLUMN = ACTUAL_PRICE_LAG_1H_COLUMN
NAIVE_BASELINE_PREDICTION_COLUMN = (
  ACTUAL_PRICE_LAG_1H_COLUMN
)
AESO_FORECAST_COLUMN = FORECAST_PRICE_COLUMN
PREVIOUS_DAY_PRICE_COLUMN = ACTUAL_PRICE_LAG_24H_COLUMN

RULE_BASELINE_PREDICTION_COLUMNS = {
  "naive_spike_baseline":
    NAIVE_BASELINE_PREDICTION_COLUMN,
  "aeso_forecast_spike_baseline":
    AESO_FORECAST_COLUMN,
  "previous_day_spike_baseline":
    PREVIOUS_DAY_PRICE_COLUMN,
}


# Persisted metadata contracts differ slightly between the two ML tasks.
REGRESSION_MODEL_METADATA_COLUMNS = [
  "model_name",
  "horizon_hours",
  "target_column",
  "artifact_path",
  "training_rows",
  "feature_columns",
  "sklearn_version",
  "training_start_utc",
  "training_end_utc",
  "selection_metric",
  "selection_rule",
  "model_parameters",
]

CLASSIFICATION_MODEL_METADATA_COLUMNS = [
  "model_name",
  "horizon_hours",
  "target_column",
  "spike_threshold",
  "decision_threshold",
  "artifact_path",
  "training_rows",
  "feature_columns",
  "sklearn_version",
  "training_start_utc",
  "training_end_utc",
  "selection_metric",
  "selection_rule",
  "model_parameters",
]
