from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from electricity_predictor.worker.historical_seed import (
  load_seed_history,
  seed_historical_database,
)


def write_historical_seed_csv(dataset_path: Path) -> None:
  pd.DataFrame(
    {
      "Date_Begin_GMT": [
        "2026-07-17 01:00:00",
        "2026-07-17 00:00:00",
      ],
      "Date_Begin_Local": [
        "2026-07-16 19:00:00",
        "2026-07-16 18:00:00",
      ],
      "ACTUAL_POOL_PRICE": [42.0, 40.0],
      "HOUR_AHEAD_POOL_PRICE_FORECAST": [41.0, 39.0],
      "ACTUAL_AIL": [8150.0, 8100.0],
    }
  ).to_csv(dataset_path, index=False)


def test_load_seed_history_returns_sorted_required_columns(
  tmp_path: Path,
) -> None:
  dataset_path = tmp_path / "historical.csv"
  write_historical_seed_csv(dataset_path)

  data = load_seed_history(dataset_path)

  assert list(data.columns) == [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]
  assert data["datetime_universal_time"].is_monotonic_increasing
  assert str(data["datetime_universal_time"].dt.tz) == "UTC"


def test_load_seed_history_rejects_missing_file(
  tmp_path: Path,
) -> None:
  with pytest.raises(
    FileNotFoundError,
    match="Historical CSV not found",
  ):
    load_seed_history(tmp_path / "missing.csv")


def test_seed_historical_database_calls_bulk_upsert(
  tmp_path: Path,
) -> None:
  dataset_path = tmp_path / "historical.csv"
  write_historical_seed_csv(dataset_path)

  with patch(
    "electricity_predictor.worker.historical_seed."
    "upsert_hourly_prices",
    return_value=2,
  ) as upsert:
    synchronized_rows = seed_historical_database(
      dataset_path
    )

  assert synchronized_rows == 2
  assert upsert.call_args.kwargs["source"] == "historical_seed"
