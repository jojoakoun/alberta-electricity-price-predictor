from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration


def load_current_historical_dataset(file_path: Path) -> pd.DataFrame:
  """Load the current historical dataset used as the source for feature engineering."""
  if not file_path.exists():
    raise FileNotFoundError(f"Current historical dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # Convert timestamp columns before creating time-based features.
  data["datetime_universal_time"] = pd.to_datetime(data["datetime_universal_time"])
  data["datetime_local_time"] = pd.to_datetime(data["datetime_local_time"])

  return data


def build_target_column_name(horizon_hours: int) -> str:
  """Build the target column name for one forecast horizon."""
  return f"actual_price_target_{horizon_hours}h"


def build_target_column_names(horizons_hours: list[int]) -> list[str]:
  """Build all target column names for the configured forecast horizons."""
  return [
    build_target_column_name(horizon_hours)
    for horizon_hours in horizons_hours
  ]


def validate_continuous_hourly_utc_timestamps(data: pd.DataFrame) -> None:
  """Validate that rows follow a continuous hourly UTC sequence."""
  if len(data) <= 1:
    return

  # NaT timestamps would silently vanish from the diff check below,
  # so reject them explicitly before validating the hourly sequence.
  if data["datetime_universal_time"].isna().any():
    raise ValueError("Feature engineering requires non-missing UTC timestamps.")

  sorted_timestamps = data["datetime_universal_time"].sort_values().reset_index(drop=True)

  # Duplicate or skipped UTC hours would make row-based shifts unsafe.
  expected_step = pd.Timedelta(hours=1)
  observed_steps = sorted_timestamps.diff().dropna()

  if not (observed_steps == expected_step).all():
    raise ValueError("Feature engineering requires continuous hourly UTC timestamps.")


def add_time_features(data: pd.DataFrame) -> pd.DataFrame:
  """Add simple local time features for modeling."""
  data = data.copy()

  # Local time matters because household electricity decisions happen in Alberta local time.
  data["hour"] = data["datetime_local_time"].dt.hour
  data["day_of_week"] = data["datetime_local_time"].dt.dayofweek
  data["month"] = data["datetime_local_time"].dt.month

  # Weekends behaved differently in the EDA, so this feature separates weekday and weekend hours.
  data["is_weekend"] = data["day_of_week"].isin([5, 6]).astype(int)

  return data


def add_lag_features(data: pd.DataFrame) -> pd.DataFrame:
  """Add past price values that can help predict the target hour."""
  data = data.copy()

  # Sort by UTC time so each lag uses the true previous hour.
  data = data.sort_values("datetime_universal_time").reset_index(drop=True)

  # Use past actual prices only. This avoids giving the model the current target value.
  data["actual_price_lag_1h"] = data["actual_price"].shift(1)
  data["actual_price_lag_24h"] = data["actual_price"].shift(24)

  # Forecast history may also help the model understand recent forecast direction.
  data["forecast_price_lag_1h"] = data["forecast_price"].shift(1)

  return data


def add_rolling_features(data: pd.DataFrame) -> pd.DataFrame:
  """Add rolling summaries from past actual prices."""
  data = data.copy()

  # Sort by UTC time so rolling windows follow the true hourly sequence.
  data = data.sort_values("datetime_universal_time").reset_index(drop=True)

  # Shift first so the current target value is not included in its own features.
  past_actual_price = data["actual_price"].shift(1)

  # The 24-hour mean captures the recent market level before the target hour.
  data["actual_price_rolling_24h_mean"] = past_actual_price.rolling(24).mean()

  # The 24-hour max captures whether the market recently had a high-price event.
  data["actual_price_rolling_24h_max"] = past_actual_price.rolling(24).max()

  # The 7-day mean captures broader market context before the target hour.
  data["actual_price_rolling_7d_mean"] = past_actual_price.rolling(24 * 7).mean()

  return data


def add_horizon_target_features(
  data: pd.DataFrame,
  horizons_hours: list[int],
) -> pd.DataFrame:
  """Add future actual price targets for each forecast horizon."""
  data = data.copy()

  # Sort first so shifting rows means moving forward in real chronological order.
  data = data.sort_values("datetime_universal_time").reset_index(drop=True)

  for horizon_hours in horizons_hours:
    target_column = build_target_column_name(horizon_hours)

    # A negative shift moves future prices onto the current decision row.
    # Example: target_3h at time t equals actual_price at time t + 3.
    data[target_column] = data["actual_price"].shift(-horizon_hours)

  return data


def build_basic_modeling_dataset(
  data: pd.DataFrame,
  horizons_hours: list[int] | None = None,
) -> pd.DataFrame:
  """Build the modeling dataset with features and future price targets."""
  data = data.copy()

  if horizons_hours is None:
    horizons_hours = [1, 3, 6, 12, 24]

  # Supervised models need finalized actual prices before we can create targets.
  data = data.dropna(subset=["actual_price"])

  # Row-based lag and target shifts are only safe when every UTC hour is present.
  validate_continuous_hourly_utc_timestamps(data)

  # Add simple time features identified as useful during EDA.
  data = add_time_features(data)

  # Add past price values without leaking the current or future target value.
  data = add_lag_features(data)

  # Add rolling summaries from past prices to describe recent market conditions.
  data = add_rolling_features(data)

  # Add future target prices for each horizon the app will eventually compare.
  data = add_horizon_target_features(
    data=data,
    horizons_hours=horizons_hours,
  )

  target_columns = build_target_column_names(horizons_hours)

  # Keep only columns that are available now and useful for the modeling dataset.
  modeling_columns = [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
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
    *target_columns,
  ]

  return data[modeling_columns]


def write_modeling_dataset(data: pd.DataFrame, output_path: Path) -> Path:
  """Write the modeling dataset to a CSV file."""
  # Create the processed data folder if it does not exist yet.
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # Save the model-ready dataset so future ML steps can reuse it.
  data.to_csv(output_path, index=False)

  return output_path


if __name__ == "__main__":
  configuration = load_configuration()

  source_path = Path("data/interim/current_historical_prices_clean.csv")
  output_path = Path("data/processed/modeling_dataset.csv")
  horizons_hours = configuration["modeling"]["horizons_hours"]

  data = load_current_historical_dataset(source_path)
  modeling_data = build_basic_modeling_dataset(
    data=data,
    horizons_hours=horizons_hours,
  )
  written_path = write_modeling_dataset(modeling_data, output_path)

  print(f"Modeling dataset written to: {written_path}")
  print(f"Rows: {modeling_data.shape[0]:,}")
  print(f"Columns: {modeling_data.shape[1]}")
  print(modeling_data.columns.tolist())
