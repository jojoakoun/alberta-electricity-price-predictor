"""One-time historical PostgreSQL seed from the bootstrap CSV."""

from pathlib import Path

import pandas as pd

from electricity_predictor.config import (
  PROJECT_ROOT,
  load_configuration,
)
from electricity_predictor.data.ingestion import (
  load_historical_data,
)
from electricity_predictor.worker.persistence import (
  upsert_hourly_prices,
)


_CONFIGURATION = load_configuration()
DEFAULT_HISTORICAL_CSV_PATH = (
  PROJECT_ROOT
  / _CONFIGURATION["paths"]["raw_data_dir"]
  / _CONFIGURATION["data"]["historical_csv_name"]
)


def load_seed_history(
  dataset_path: Path = DEFAULT_HISTORICAL_CSV_PATH,
) -> pd.DataFrame:
  """Load and shape the raw historical bootstrap CSV."""
  data = load_historical_data(
    dataset_path
  )

  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"],
    utc=True,
  )

  required_columns = [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]

  return data[required_columns].sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)


def seed_historical_database(
  dataset_path: Path = DEFAULT_HISTORICAL_CSV_PATH,
) -> int:
  """Seed PostgreSQL once from the historical bootstrap CSV."""
  data = load_seed_history(dataset_path)

  return upsert_hourly_prices(
    data=data,
    source="historical_seed",
  )


def main() -> None:
  """Run the explicit one-time historical database seed."""
  synchronized_rows = seed_historical_database()

  print(f"Seeded historical hourly price rows: {synchronized_rows}")


if __name__ == "__main__":
  main()
