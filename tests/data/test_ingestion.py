from pathlib import Path

import pandas as pd

from electricity_predictor.data.ingestion import (
  load_historical_data,
  validate_historical_data,
)


def write_fake_historical_csv(csv_path: Path) -> None:
  """Create a small raw historical CSV for hermetic ingestion tests."""
  data = pd.DataFrame(
    {
      "Date_Begin_GMT": [
        "2025-07-31 23:00",
        "2025-07-31 21:00",
        "2025-07-31 22:00",
      ],
      "Date_Begin_Local": [
        "2025-07-31 17:00",
        "2025-07-31 15:00",
        "2025-07-31 16:00",
      ],
      "ACTUAL_POOL_PRICE": [50.0, 40.0, 45.0],
      "HOUR_AHEAD_POOL_PRICE_FORECAST": [48.0, 38.0, 43.0],
      "ACTUAL_AIL": [10100, 10000, 10050],
    }
  )

  csv_path.parent.mkdir(parents=True, exist_ok=True)
  data.to_csv(csv_path, index=False)


def test_load_historical_data_returns_expected_columns(tmp_path: Path) -> None:
  csv_path = tmp_path / "raw" / "historical.csv"
  write_fake_historical_csv(csv_path)

  data = load_historical_data(csv_path)

  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]


def test_load_historical_data_returns_rows(tmp_path: Path) -> None:
  csv_path = tmp_path / "raw" / "historical.csv"
  write_fake_historical_csv(csv_path)

  data = load_historical_data(csv_path)

  assert len(data) == 3


def test_load_historical_data_sorts_by_utc_time(tmp_path: Path) -> None:
  csv_path = tmp_path / "raw" / "historical.csv"
  write_fake_historical_csv(csv_path)

  data = load_historical_data(csv_path)

  assert data["datetime_universal_time"].is_monotonic_increasing


def test_validate_historical_data_rejects_duplicate_utc_timestamps(tmp_path: Path) -> None:
  csv_path = tmp_path / "raw" / "historical.csv"
  write_fake_historical_csv(csv_path)

  data = load_historical_data(csv_path)

  # Add a copied row to simulate a bad dataset with a duplicate hour.
  duplicated_data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
  duplicated_data = duplicated_data.sort_values("datetime_universal_time").reset_index(drop=True)

  try:
    validate_historical_data(duplicated_data)
  except ValueError as error:
    assert "duplicate timestamps" in str(error)
  else:
    raise AssertionError("Expected duplicate UTC timestamps to raise ValueError.")
