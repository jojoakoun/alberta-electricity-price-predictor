"""Build candidate feature contracts available at the current source hour."""

import pandas as pd

from electricity_predictor.contracts.columns import (
  ACTUAL_PRICE_COLUMN,
  ACTUAL_PRICE_LAG_24H_COLUMN,
  ACTUAL_PRICE_SAFE_24H_MAX_COLUMN,
  ACTUAL_PRICE_SAFE_24H_MEAN_COLUMN,
  ACTUAL_PRICE_SAFE_7D_MEAN_COLUMN,
  CONSERVATIVE_ACTUAL_FEATURE_COLUMNS,
  CONSERVATIVE_HYBRID_LIVE_FEATURE_COLUMNS,
  DATETIME_COLUMN,
  FORECAST_DERIVED_FEATURE_COLUMNS,
  FORECAST_ONLY_LIVE_FEATURE_COLUMNS,
  FORECAST_PRICE_COLUMN,
  FORECAST_PRICE_LAG_1H_COLUMN,
  FORECAST_PRICE_LAG_24H_COLUMN,
  FORECAST_PRICE_ROLLING_24H_MAX_COLUMN,
  FORECAST_PRICE_ROLLING_24H_MEAN_COLUMN,
  FORECAST_PRICE_ROLLING_7D_MEAN_COLUMN,
  LIVE_FEATURE_CONTRACTS,
  LIVE_TIME_FEATURE_COLUMNS,
  LOCAL_DATETIME_COLUMN,
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)
from electricity_predictor.features.feature_engineering import (
  ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
  add_time_features,
  validate_continuous_hourly_utc_timestamps,
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
    DATETIME_COLUMN,
    LOCAL_DATETIME_COLUMN,
    ACTUAL_PRICE_COLUMN,
    FORECAST_PRICE_COLUMN,
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
      DATETIME_COLUMN
    )
    .reset_index(drop=True)
    .copy()
  )

  features = add_time_features(
    features
  )

  features[
    FORECAST_PRICE_LAG_1H_COLUMN
  ] = (
    features[
      FORECAST_PRICE_COLUMN
    ].shift(1)
  )

  features[
    FORECAST_PRICE_LAG_24H_COLUMN
  ] = (
    features[
      FORECAST_PRICE_COLUMN
    ].shift(24)
  )

  past_forecast = (
    features[
      FORECAST_PRICE_COLUMN
    ].shift(1)
  )

  features[
    FORECAST_PRICE_ROLLING_24H_MEAN_COLUMN
  ] = (
    past_forecast
    .rolling(
      window=24,
      min_periods=24,
    )
    .mean()
  )

  features[
    FORECAST_PRICE_ROLLING_24H_MAX_COLUMN
  ] = (
    past_forecast
    .rolling(
      window=24,
      min_periods=24,
    )
    .max()
  )

  features[
    FORECAST_PRICE_ROLLING_7D_MEAN_COLUMN
  ] = (
    past_forecast
    .rolling(
      window=(
        ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
      ),
      min_periods=(
        ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
      ),
    )
    .mean()
  )

  # H-24 is safely behind normal AESO finalization delays.
  safe_actual_price = (
    features[
      ACTUAL_PRICE_COLUMN
    ].shift(24)
  )

  features[
    ACTUAL_PRICE_LAG_24H_COLUMN
  ] = safe_actual_price

  features[
    ACTUAL_PRICE_SAFE_24H_MEAN_COLUMN
  ] = (
    safe_actual_price
    .rolling(
      window=24,
      min_periods=24,
    )
    .mean()
  )

  features[
    ACTUAL_PRICE_SAFE_24H_MAX_COLUMN
  ] = (
    safe_actual_price
    .rolling(
      window=24,
      min_periods=24,
    )
    .max()
  )

  features[
    ACTUAL_PRICE_SAFE_7D_MEAN_COLUMN
  ] = (
    safe_actual_price
    .rolling(
      window=(
        ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
      ),
      min_periods=(
        ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
      ),
    )
    .mean()
  )

  return features
