"""Build one current-hour feature row for active live models."""

import pandas as pd

from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  add_live_feature_candidates,
)
from electricity_predictor.worker.hourly_price_database import (
  load_hourly_prices_for_prediction,
)


ALBERTA_TIMEZONE = "America/Edmonton"

# The 7-day safe-actual feature ends at H-24 and therefore begins at H-191.
LIVE_FORECAST_WINDOW_HOURS = 168
LIVE_SAFE_ACTUAL_DELAY_HOURS = 24
LIVE_SAFE_ACTUAL_WINDOW_HOURS = 168
LIVE_REQUIRED_LOOKBACK_HOURS = (
  LIVE_SAFE_ACTUAL_DELAY_HOURS
  + LIVE_SAFE_ACTUAL_WINDOW_HOURS
  - 1
)

# Request one additional hour from PostgreSQL as a harmless boundary buffer.
LIVE_INFERENCE_LOOKBACK_HOURS = (
  LIVE_REQUIRED_LOOKBACK_HOURS + 1
)


def normalize_candidate_timestamp(
  candidate_hint,
  latest_timestamp: pd.Timestamp,
) -> pd.Timestamp:
  """Normalize and validate the current inference source hour."""
  if candidate_hint is None:
    return latest_timestamp

  candidate_timestamp = pd.Timestamp(
    candidate_hint
  )

  if candidate_timestamp.tzinfo is None:
    candidate_timestamp = (
      candidate_timestamp.tz_localize(
        "UTC"
      )
    )
  else:
    candidate_timestamp = (
      candidate_timestamp.tz_convert(
        "UTC"
      )
    )

  if candidate_timestamp != latest_timestamp:
    raise ValueError(
      "Inference candidate must equal the latest "
      "available market hour. "
      f"candidate={candidate_timestamp.isoformat()}, "
      f"latest={latest_timestamp.isoformat()}."
    )

  return candidate_timestamp


def select_required_live_window(
  data: pd.DataFrame,
  candidate_timestamp: pd.Timestamp,
) -> pd.DataFrame:
  """Return the exact continuous support needed by the live contract."""
  window_start = (
    candidate_timestamp
    - pd.Timedelta(
      hours=LIVE_REQUIRED_LOOKBACK_HOURS
    )
  )

  window = data.loc[
    data[
      "datetime_universal_time"
    ].between(
      window_start,
      candidate_timestamp,
    )
  ].copy()

  duplicate_rows = window.loc[
    window[
      "datetime_universal_time"
    ].duplicated(),
    "datetime_universal_time",
  ]

  if not duplicate_rows.empty:
    duplicate_timestamp = (
      duplicate_rows.iloc[0]
    )

    raise ValueError(
      "Inference feature window contains "
      "duplicate hourly price at "
      f"{duplicate_timestamp.isoformat()}."
    )

  expected_timestamps = pd.date_range(
    start=window_start,
    end=candidate_timestamp,
    freq="h",
    tz="UTC",
  )

  available_timestamps = pd.DatetimeIndex(
    window[
      "datetime_universal_time"
    ]
  )

  missing_timestamps = (
    expected_timestamps.difference(
      available_timestamps
    )
  )

  if not missing_timestamps.empty:
    missing_timestamp = (
      missing_timestamps[0]
    )

    raise ValueError(
      "Inference feature window is missing "
      "hourly price at "
      f"{missing_timestamp.isoformat()}."
    )

  if len(window) != len(
    expected_timestamps
  ):
    raise ValueError(
      "Inference feature window does not "
      "contain exactly one row per UTC hour."
    )

  return window.reset_index(
    drop=True
  )


def validate_forecast_support(
  window: pd.DataFrame,
  candidate_timestamp: pd.Timestamp,
) -> None:
  """Require every forecast used by lagged and rolling forecast features."""
  forecast_start = (
    candidate_timestamp
    - pd.Timedelta(
      hours=(
        LIVE_FORECAST_WINDOW_HOURS - 1
      )
    )
  )

  forecast_rows = window.loc[
    window[
      "datetime_universal_time"
    ].between(
      forecast_start,
      candidate_timestamp,
    )
  ]

  missing_rows = forecast_rows.loc[
    forecast_rows[
      "forecast_price"
    ].isna()
  ]

  if missing_rows.empty:
    return

  missing_timestamp = missing_rows[
    "datetime_universal_time"
  ].iloc[0]

  raise ValueError(
    "Inference feature window is missing "
    "forecast_price at "
    f"{missing_timestamp.isoformat()}."
  )


def validate_safe_actual_support(
  window: pd.DataFrame,
  candidate_timestamp: pd.Timestamp,
) -> None:
  """Require actual prices only through H-24, never for recent live hours."""
  actual_start = (
    candidate_timestamp
    - pd.Timedelta(
      hours=LIVE_REQUIRED_LOOKBACK_HOURS
    )
  )

  actual_end = (
    candidate_timestamp
    - pd.Timedelta(
      hours=LIVE_SAFE_ACTUAL_DELAY_HOURS
    )
  )

  actual_rows = window.loc[
    window[
      "datetime_universal_time"
    ].between(
      actual_start,
      actual_end,
    )
  ]

  missing_rows = actual_rows.loc[
    actual_rows[
      "actual_price"
    ].isna()
  ]

  if missing_rows.empty:
    return

  missing_timestamp = missing_rows[
    "datetime_universal_time"
  ].iloc[0]

  raise ValueError(
    "Inference feature window is missing "
    "required actual_price for safe "
    "H-24 features at "
    f"{missing_timestamp.isoformat()}."
  )


def prepare_model_features() -> pd.DataFrame:
  """Build one complete selected-contract row for the latest market hour."""
  data = load_hourly_prices_for_prediction(
    lookback_hours=(
      LIVE_INFERENCE_LOOKBACK_HOURS
    )
  )

  if data.empty:
    raise ValueError(
      "No hourly prices available."
    )

  candidate_hint = data.attrs.get(
    "inference_candidate_utc"
  )

  data = data.copy()

  data[
    "datetime_universal_time"
  ] = pd.to_datetime(
    data[
      "datetime_universal_time"
    ],
    utc=True,
    errors="raise",
  )

  data = data.sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)

  latest_timestamp = data[
    "datetime_universal_time"
  ].iloc[-1]

  candidate_timestamp = (
    normalize_candidate_timestamp(
      candidate_hint=candidate_hint,
      latest_timestamp=latest_timestamp,
    )
  )

  window = select_required_live_window(
    data=data,
    candidate_timestamp=(
      candidate_timestamp
    ),
  )

  validate_forecast_support(
    window=window,
    candidate_timestamp=(
      candidate_timestamp
    ),
  )

  validate_safe_actual_support(
    window=window,
    candidate_timestamp=(
      candidate_timestamp
    ),
  )

  window["datetime_local_time"] = (
    window[
      "datetime_universal_time"
    ]
    .dt.tz_convert(
      ALBERTA_TIMEZONE
    )
    .dt.tz_localize(None)
  )

  featured_data = (
    add_live_feature_candidates(
      window
    )
  )

  candidate_row = featured_data.loc[
    featured_data[
      "datetime_universal_time"
    ]
    == candidate_timestamp
  ].copy()

  if len(candidate_row) != 1:
    raise ValueError(
      "Expected exactly one current-hour "
      "inference feature row."
    )

  missing_features = [
    column
    for column in (
      SELECTED_LIVE_FEATURE_COLUMNS
    )
    if pd.isna(
      candidate_row.iloc[0][column]
    )
  ]

  if missing_features:
    raise ValueError(
      "Current-hour inference features are "
      "incomplete: "
      f"{', '.join(missing_features)}."
    )

  return candidate_row.reset_index(
    drop=True
  )
