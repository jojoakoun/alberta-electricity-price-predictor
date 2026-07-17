import pandas as pd

from electricity_predictor.features.feature_engineering import (
  add_lag_features,
  add_rolling_features,
  add_time_features,
  validate_continuous_hourly_utc_timestamps,
)
from electricity_predictor.modeling.regression.feature_columns import (
  REGRESSION_FEATURE_COLUMNS,
)
from electricity_predictor.worker.persistence import load_hourly_prices


ALBERTA_TIMEZONE = "America/Edmonton"


def prepare_model_features() -> pd.DataFrame:
  """Build application features without future training targets."""
  data = load_hourly_prices()

  if data.empty:
    raise ValueError("No hourly prices available.")

  data = data.copy()

  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"],
    utc=True,
  )

  data["datetime_local_time"] = (
    data["datetime_universal_time"]
    .dt.tz_convert(ALBERTA_TIMEZONE)
    .dt.tz_localize(None)
  )

  # Reuse the same calculations as training, without creating future targets.
  validate_continuous_hourly_utc_timestamps(data)
  data = add_time_features(data)
  data = add_lag_features(data)
  data = add_rolling_features(data)

  complete_rows = data.dropna(
    subset=REGRESSION_FEATURE_COLUMNS,
  )

  if complete_rows.empty:
    raise ValueError("No complete model feature row is available.")

  return complete_rows.reset_index(drop=True)
