"""Build candidate feature contracts available at the current source hour."""

import pandas as pd

from electricity_predictor.features.feature_engineering import (
  ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
  add_time_features,
  validate_continuous_hourly_utc_timestamps,
)


FORECAST_DERIVED_FEATURE_COLUMNS = [
  "forecast_price",
  "forecast_price_lag_1h",
  "forecast_price_lag_24h",
  "forecast_price_rolling_24h_mean",
  "forecast_price_rolling_24h_max",
  "forecast_price_rolling_7d_mean",
]

CONSERVATIVE_ACTUAL_FEATURE_COLUMNS = [
  "actual_price_lag_24h",
  "actual_price_safe_24h_mean",
  "actual_price_safe_24h_max",
  "actual_price_safe_7d_mean",
]

LIVE_TIME_FEATURE_COLUMNS = [
  "hour",
  "day_of_week",
  "month",
  "is_weekend",
]

FORECAST_ONLY_LIVE_FEATURE_COLUMNS = [
  *LIVE_TIME_FEATURE_COLUMNS,
  *FORECAST_DERIVED_FEATURE_COLUMNS,
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

# One shared production contract keeps training and hourly inference aligned.
SELECTED_LIVE_FEATURE_CONTRACT = "conservative_hybrid"

SELECTED_LIVE_FEATURE_COLUMNS = list(
  LIVE_FEATURE_CONTRACTS[
    SELECTED_LIVE_FEATURE_CONTRACT
  ]
)


def get_live_feature_columns(
  contract_name: str,
) -> list[str]:
  """Return a defensive copy of one named live feature contract."""
  try:
    return list(
      LIVE_FEATURE_CONTRACTS[contract_name]
    )
  except KeyError as error:
    supported = ", ".join(
      sorted(LIVE_FEATURE_CONTRACTS)
    )

    raise ValueError(
      "Unsupported live feature contract "
      f"{contract_name!r}. Supported contracts: {supported}."
    ) from error


def validate_live_feature_source(
  data: pd.DataFrame,
) -> None:
  """Validate the raw hourly columns needed by both live contracts."""
  required_columns = {
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  }

  missing_columns = (
    required_columns - set(data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Live feature source is missing columns: "
      f"{sorted(missing_columns)}."
    )

  validate_continuous_hourly_utc_timestamps(
    data
  )


def add_live_feature_candidates(
  data: pd.DataFrame,
) -> pd.DataFrame:
  """Add forecast-only and conservative hybrid candidate features.

  Forecast-derived features are available at the current source hour.
  Conservative actual-price features stop at H-24, avoiding dependence on
  prices that AESO may not have finalized yet.
  """
  validate_live_feature_source(data)

  features = (
    data
    .sort_values(
      "datetime_universal_time"
    )
    .reset_index(drop=True)
    .copy()
  )

  features = add_time_features(
    features
  )

  features["forecast_price_lag_1h"] = (
    features["forecast_price"].shift(1)
  )

  features["forecast_price_lag_24h"] = (
    features["forecast_price"].shift(24)
  )

  past_forecast = (
    features["forecast_price"].shift(1)
  )

  features[
    "forecast_price_rolling_24h_mean"
  ] = (
    past_forecast
    .rolling(
      window=24,
      min_periods=24,
    )
    .mean()
  )

  features[
    "forecast_price_rolling_24h_max"
  ] = (
    past_forecast
    .rolling(
      window=24,
      min_periods=24,
    )
    .max()
  )

  features[
    "forecast_price_rolling_7d_mean"
  ] = (
    past_forecast
    .rolling(
      window=ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
      min_periods=ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
    )
    .mean()
  )

  # At source hour H, H-24 is safely behind normal AESO finalization delays.
  safe_actual_price = (
    features["actual_price"].shift(24)
  )

  features["actual_price_lag_24h"] = (
    safe_actual_price
  )

  features[
    "actual_price_safe_24h_mean"
  ] = (
    safe_actual_price
    .rolling(
      window=24,
      min_periods=24,
    )
    .mean()
  )

  features[
    "actual_price_safe_24h_max"
  ] = (
    safe_actual_price
    .rolling(
      window=24,
      min_periods=24,
    )
    .max()
  )

  features[
    "actual_price_safe_7d_mean"
  ] = (
    safe_actual_price
    .rolling(
      window=ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
      min_periods=ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
    )
    .mean()
  )

  return features
