"""Load the historical CSV for research rebuilds and one-time seeding."""

from pathlib import Path

import pandas as pd
from electricity_predictor.contracts.columns import (
  RAW_COLUMNS,
)




def validate_historical_data(data: pd.DataFrame) -> None:
  """Validate the cleaned historical electricity bootstrap data."""
  required_columns = set(RAW_COLUMNS.values())
  missing_columns = required_columns - set(data.columns)

  if missing_columns:
    raise ValueError(f"Missing required columns: {sorted(missing_columns)}")

  required_non_null_columns = [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  ]

  for column in required_non_null_columns:
    if data[column].isna().any():
      raise ValueError(f"Column contains missing values: {column}")

  # Duplicate or unordered UTC hours would make later row-based temporal
  # features point at the wrong market hour.
  if data["datetime_universal_time"].duplicated().any():
    raise ValueError("datetime_universal_time contains duplicate timestamps.")

  if not data["datetime_universal_time"].is_monotonic_increasing:
    raise ValueError("Data must be sorted by datetime_universal_time.")


def load_historical_data(csv_path: Path) -> pd.DataFrame:
  """Load and validate the historical Alberta electricity bootstrap CSV."""
  if not csv_path.exists():
    raise FileNotFoundError(f"Historical CSV not found: {csv_path}")

  data = pd.read_csv(
    csv_path,
    usecols=list(RAW_COLUMNS.keys()),
  )
  data = data.rename(columns=RAW_COLUMNS)

  # Stable column order is part of the seed and research pipeline contract.
  data = data[list(RAW_COLUMNS.values())]
  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"]
  )
  data["datetime_local_time"] = pd.to_datetime(
    data["datetime_local_time"]
  )
  data = data.sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)

  validate_historical_data(data)

  return data
