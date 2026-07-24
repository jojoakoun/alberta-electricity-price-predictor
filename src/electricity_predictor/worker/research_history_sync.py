"""Import a research CSV into PostgreSQL outside the recurring worker path."""

from pathlib import Path

import pandas as pd

from electricity_predictor.config import PROJECT_ROOT
from electricity_predictor.worker.hourly_price_database import insert_or_update_hourly_prices


DEFAULT_DATASET_PATH = (
  PROJECT_ROOT
  / "data"
  / "interim"
  / "current_historical_prices_clean.csv"
)


def load_current_history(
  dataset_path: Path = DEFAULT_DATASET_PATH,
) -> pd.DataFrame:
  """Load the current clean research pipeline dataset."""
  if not dataset_path.exists():
    raise FileNotFoundError(
      f"Current historical dataset not found: {dataset_path}"
    )

  data = pd.read_csv(dataset_path)

  required_columns = [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]

  missing_columns = set(required_columns) - set(data.columns)

  if missing_columns:
    raise ValueError(
      f"Current historical dataset is missing columns: "
      f"{sorted(missing_columns)}"
    )

  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"],
    utc=True,
  )

  return data[required_columns].sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)


def synchronize_current_history(
  dataset_path: Path = DEFAULT_DATASET_PATH,
) -> int:
  """Synchronize the current research dataset with PostgreSQL."""
  data = load_current_history(dataset_path)

  return insert_or_update_hourly_prices(
    data=data,
    source="pipeline",
  )


def main() -> None:
  """Run the research dataset synchronization command."""
  synchronized_rows = synchronize_current_history()

  print(f"Synchronized hourly price rows: {synchronized_rows}")


if __name__ == "__main__":
  main()
