from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from electricity_predictor.worker.research_history_sync import (
  load_current_history,
  synchronize_current_history,
)


def test_relocated_module_contract() -> None:
  assert find_spec(
    "electricity_predictor.worker.research_history_sync"
  ) is not None
  assert find_spec("electricity_predictor.worker.importer") is None


def test_sync_history_target_uses_relocated_module() -> None:
  makefile = Path("Makefile").read_text(encoding="utf-8")
  target = makefile.split("sync-history:\n", 1)[1].split(
    "\n\n", 1
  )[0]
  normalized_target = " ".join(
    target.replace("\\\n", " ").split()
  )

  assert (
    "$(PYTHON) -m "
    "electricity_predictor.worker.research_history_sync"
    in normalized_target
  )
  assert "electricity_predictor.worker.importer" not in target


def test_load_current_history_returns_sorted_required_columns(
  tmp_path: Path,
) -> None:
  dataset_path = tmp_path / "current_history.csv"

  pd.DataFrame(
    {
      "datetime_universal_time": [
        "2026-07-17 01:00:00",
        "2026-07-17 00:00:00",
      ],
      "datetime_local_time": [
        "2026-07-16 19:00:00",
        "2026-07-16 18:00:00",
      ],
      "actual_price": [42.0, 40.0],
      "forecast_price": [41.0, 39.0],
      "alberta_internal_load": [8150.0, 8100.0],
    }
  ).to_csv(dataset_path, index=False)

  data = load_current_history(dataset_path)

  assert list(data.columns) == [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]
  assert data["datetime_universal_time"].is_monotonic_increasing
  assert str(data["datetime_universal_time"].dt.tz) == "UTC"


def test_load_current_history_rejects_missing_file(
  tmp_path: Path,
) -> None:
  with pytest.raises(
    FileNotFoundError,
    match="Current historical dataset not found",
  ):
    load_current_history(tmp_path / "missing.csv")


def test_synchronize_current_history_calls_bulk_upsert(
  tmp_path: Path,
) -> None:
  dataset_path = tmp_path / "current_history.csv"

  pd.DataFrame(
    {
      "datetime_universal_time": ["2026-07-17 00:00:00"],
      "actual_price": [40.0],
      "forecast_price": [39.0],
      "alberta_internal_load": [8100.0],
    }
  ).to_csv(dataset_path, index=False)

  with patch(
    "electricity_predictor.worker.research_history_sync."
    "insert_or_update_hourly_prices",
    return_value=1,
  ) as upsert:
    synchronized_rows = synchronize_current_history(dataset_path)

  assert synchronized_rows == 1
  upsert.assert_called_once()
