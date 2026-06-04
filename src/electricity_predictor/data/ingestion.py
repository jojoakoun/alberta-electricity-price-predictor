from pathlib import Path

import pandas as pd

RAW_COLUMNS = {
  "Date_Begin_GMT": "datetime_universal_time",  # UTC timestamp for each hourly record.
  "Date_Begin_Local": "datetime_local_time",  # Alberta local timestamp for each hourly record.
  "ACTUAL_POOL_PRICE": "actual_price",  # Real pool price observed for that hour.
  "HOUR_AHEAD_POOL_PRICE_FORECAST": "forecast_price",  # Forecasted pool price before the hour.
  "ACTUAL_AIL": "alberta_internal_load",  # Alberta electricity demand/load for that hour.
}

def validate_historical_data(data:pd.DataFrame):
  """Validate the cleaned historical electricity data."""
  required_columns = set(RAW_COLUMNS.values())
  missing_columns = required_columns - set(data.columns)
  
  
  if missing_columns:
    raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
  
  # These fields are essential for time-based modeling.
  required_non_null_columns = [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  ]
  
  for column in required_non_null_columns:
    if data[column].isna().any():
      raise ValueError(f"Column contains missing values: {column}")
    
  # Each UTC hour should appear only once in the historical data.
  if data["datetime_universal_time"].duplicated().any():
      raise ValueError("datetime_universal_time contains duplicate timestamps.")

  # Time-series data must stay in chronological order before modeling.
  if not data["datetime_universal_time"].is_monotonic_increasing:
    raise ValueError("Data must be sorted by datetime_universal_time.")
   

def load_historical_data(csv_path: Path) -> pd.DataFrame:
  """Load the historical Alberta electricity CSV with clean column names."""
  
  if not csv_path.exists():
    raise FileNotFoundError(f"Historical CSV not found: {csv_path}")
  
  # Keep only the columns we need from the large raw CSV.
  data = pd.read_csv(csv_path, usecols=list(RAW_COLUMNS.keys()))
  
  
  data = data.rename(columns=RAW_COLUMNS)
  
  # Keep a stable column order for tests and downstream code.
  data = data[list(RAW_COLUMNS.values())]
  
  data["datetime_universal_time"] = pd.to_datetime(data["datetime_universal_time"])
  data["datetime_local_time"] = pd.to_datetime(data["datetime_local_time"])
  
  data = data.sort_values("datetime_universal_time").reset_index(drop=True)
  
  # Stop the pipeline early if the cleaned data is invalid.
  validate_historical_data(data)
  
  return data


load_historical_data(Path('data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv'))