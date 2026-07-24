"""Build one validated inference feature row from PostgreSQL history."""

import pandas as pd

from electricity_predictor.features.feature_engineering import (
  ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS,
  add_lag_features,
  add_rolling_features,
  add_time_features,
)
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.worker.persistence import (
  load_inference_hourly_prices,
)


ALBERTA_TIMEZONE = "America/Edmonton"


def validate_candidate_forecast_support(
  window: pd.DataFrame,
  candidate_timestamp: pd.Timestamp,
) -> None:
  """Validate raw forecasts for the candidate and its preceding UTC hour.

  A missing value raises an error naming its timestamp; serving never fills it
  or substitutes an older candidate.
  """
  required_timestamps = [
    candidate_timestamp - pd.Timedelta(hours=1),
    candidate_timestamp,
  ]
  required_rows = window.loc[
    window["datetime_universal_time"].isin(
      required_timestamps
    )
  ]
  missing_forecast_rows = required_rows.loc[
    required_rows["forecast_price"].isna()
  ]

  if missing_forecast_rows.empty:
    return

  missing_timestamp = missing_forecast_rows[
    "datetime_universal_time"
  ].iloc[0]
  raise ValueError(
    "Inference feature window is missing forecast_price at "
    f"{missing_timestamp.isoformat()}; the candidate requires its "
    "forecast and the previous hour for forecast_price_lag_1h."
  )


def select_inference_feature_window(
  data: pd.DataFrame,
) -> pd.DataFrame:
  """Return the exact validated support window for one inference candidate.

  Missing hourly, finalized-actual, or forecast support raises an error with
  the affected UTC timestamp; serving must not fall back to an older row.
  """
  ordered_data = data.sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)
  candidate_hint = data.attrs.get(
    "inference_candidate_utc"
  )

  finalized_rows = ordered_data.loc[
    ordered_data["actual_price"].notna()
  ]

  if finalized_rows.empty:
    raise ValueError(
      "Inference feature preparation requires at least one finalized actual price."
    )

  latest_timestamp = ordered_data[
    "datetime_universal_time"
  ].iloc[-1]
  latest_finalized_timestamp = finalized_rows[
    "datetime_universal_time"
  ].iloc[-1]
  if candidate_hint is None:
    candidate_timestamp = min(
      latest_timestamp,
      latest_finalized_timestamp + pd.Timedelta(hours=1),
    )
  else:
    candidate_timestamp = pd.Timestamp(candidate_hint)

    if candidate_timestamp.tzinfo is None:
      candidate_timestamp = candidate_timestamp.tz_localize("UTC")
    else:
      candidate_timestamp = candidate_timestamp.tz_convert("UTC")
  window_start = candidate_timestamp - pd.Timedelta(
    hours=ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
  )
  expected_timestamps = pd.date_range(
    start=window_start,
    end=candidate_timestamp,
    freq="h",
    tz="UTC",
  )
  window = ordered_data.loc[
    ordered_data["datetime_universal_time"].between(
      window_start,
      candidate_timestamp,
    )
  ].copy()
  duplicate_timestamps = window.loc[
    window[
      "datetime_universal_time"
    ].duplicated(),
    "datetime_universal_time",
  ]

  if not duplicate_timestamps.empty:
    duplicate_timestamp = duplicate_timestamps.iloc[0]
    raise ValueError(
      "Inference feature window contains duplicate hourly price at "
      f"{duplicate_timestamp.isoformat()}."
    )

  available_timestamps = pd.DatetimeIndex(
    window["datetime_universal_time"]
  )
  missing_timestamps = expected_timestamps.difference(
    available_timestamps
  )

  if not missing_timestamps.empty:
    missing_timestamp = missing_timestamps[0]
    raise ValueError(
      "Inference feature window is missing hourly price at "
      f"{missing_timestamp.isoformat()}."
    )

  # The candidate may be forecast-only, but all observations used by its
  # lagged and rolling actual-price features must already be finalized.
  required_actual_rows = window.loc[
    window["datetime_universal_time"] < candidate_timestamp
  ]
  missing_actual_rows = required_actual_rows.loc[
    required_actual_rows["actual_price"].isna()
  ]

  if not missing_actual_rows.empty:
    missing_actual_timestamp = missing_actual_rows[
      "datetime_universal_time"
    ].iloc[0]
    raise ValueError(
      "Inference feature window is missing finalized actual price at "
      f"{missing_actual_timestamp.isoformat()}."
    )

  validate_candidate_forecast_support(
    window=window,
    candidate_timestamp=candidate_timestamp,
  )

  return window.reset_index(drop=True)


def prepare_model_features() -> pd.DataFrame:
  """Return one complete feature row for the latest inference source hour.

  Raises ValueError when required support is incomplete; an older complete row
  is never substituted for the selected candidate.
  """
  data = load_inference_hourly_prices(
    lookback_hours=ACTUAL_PRICE_ROLLING_7D_WINDOW_HOURS
  )

  if data.empty:
    raise ValueError("No hourly prices available.")

  data = data.copy()

  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"],
    utc=True,
  )

  data = select_inference_feature_window(data)

  data["datetime_local_time"] = (
    data["datetime_universal_time"]
    .dt.tz_convert(ALBERTA_TIMEZONE)
    .dt.tz_localize(None)
  )

  # Reuse the same calculations as training, without creating future targets.
  data = add_time_features(data)
  data = add_lag_features(data)
  data = add_rolling_features(data)

  # Only the selected source hour is publishable. Returning older complete rows
  # would hide a current source-data or feature-contract failure.
  candidate_row = data.tail(1).copy()
  missing_feature_columns = [
    column
    for column in MODEL_FEATURE_COLUMNS
    if pd.isna(candidate_row.iloc[0][column])
  ]

  if missing_feature_columns:
    candidate_timestamp = candidate_row[
      "datetime_universal_time"
    ].iloc[0]
    raise ValueError(
      "Inference candidate at "
      f"{candidate_timestamp.isoformat()} is missing model features: "
      f"{', '.join(missing_feature_columns)}."
    )

  return candidate_row.reset_index(drop=True)
