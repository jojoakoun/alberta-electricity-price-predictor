from pathlib import Path

import pandas as pd


def load_current_historical_dataset(file_path: Path) -> pd.DataFrame:
  """Load the current historical dataset used as the source for feature engineering."""
  if not file_path.exists():
    raise FileNotFoundError(f"Current historical dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # Convert timestamp columns before creating time-based features.
  data["datetime_universal_time"] = pd.to_datetime(data["datetime_universal_time"])
  data["datetime_local_time"] = pd.to_datetime(data["datetime_local_time"])

  return data


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


def build_basic_modeling_dataset(data: pd.DataFrame) -> pd.DataFrame:
  """Build the first simple modeling dataset."""
  data = data.copy()

  # Supervised models need a finalized target value for training and evaluation.
  data = data.dropna(subset=["actual_price"])

  # Add simple time features identified as useful during EDA.
  data = add_time_features(data)

  # Add past price values without leaking the current target value.
  data = add_lag_features(data)

  # Keep only columns that are available now and useful for the first modeling dataset.
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
  source_path = Path("data/interim/current_historical_prices_clean.csv")
  output_path = Path("data/processed/modeling_dataset.csv")

  data = load_current_historical_dataset(source_path)
  modeling_data = build_basic_modeling_dataset(data)
  written_path = write_modeling_dataset(modeling_data, output_path)

  print(f"Modeling dataset written to: {written_path}")
  print(f"Rows: {modeling_data.shape[0]:,}")
  print(f"Columns: {modeling_data.shape[1]}")
  print(modeling_data.columns.tolist())
