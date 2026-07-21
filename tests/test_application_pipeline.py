from pathlib import Path
from unittest.mock import patch

import pandas as pd

from electricity_predictor.application_pipeline import (
  run_application_pipeline,
)


def test_run_application_pipeline_synchronizes_then_runs_worker() -> None:
  worker_result = {
    "run_id": 42,
    "decisions": [],
  }

  with (
    patch(
      "electricity_predictor.application_pipeline."
      "synchronize_operational_prices",
      return_value=57347,
    ) as synchronize,
    patch(
      "electricity_predictor.application_pipeline.run_worker_cycle",
      return_value=worker_result,
    ) as worker,
  ):
    result = run_application_pipeline()

  synchronize.assert_called_once_with()
  worker.assert_called_once_with()

  assert result == {
    "synchronized_rows": 57347,
    "run_id": 42,
    "decisions": [],
  }


def test_operational_pipeline_runs_without_raw_or_interim_csvs(
  tmp_path: Path,
  monkeypatch,
) -> None:
  raw_dir = tmp_path / "data" / "raw"
  raw_dir.mkdir(parents=True)
  (raw_dir / ".gitkeep").touch()
  monkeypatch.chdir(tmp_path)

  api_report = {
    "return": {
      "Pool Price Report": [
        {
          "begin_datetime_utc": "2026-07-20 12:00",
          "begin_datetime_mpt": "2026-07-20 06:00",
          "pool_price": "42.50",
          "forecast_pool_price": "40.00",
        }
      ]
    }
  }

  with (
    patch(
      "electricity_predictor.worker.operational_refresh."
      "get_latest_hourly_price_timestamp",
      return_value=pd.Timestamp(
        "2026-07-20 12:00",
        tz="UTC",
      ),
    ),
    patch(
      "electricity_predictor.worker.operational_refresh."
      "get_current_api_end_date",
      return_value="2026-07-20",
    ),
    patch(
      "electricity_predictor.worker.operational_refresh."
      "fetch_pool_price_report",
      return_value=api_report,
    ) as fetch,
    patch(
      "electricity_predictor.worker.operational_refresh."
      "upsert_hourly_prices",
      return_value=1,
    ) as upsert,
    patch(
      "electricity_predictor.application_pipeline.run_worker_cycle",
      return_value={
        "run_id": 44,
        "decisions": [],
      },
    ) as worker,
  ):
    result = run_application_pipeline()

  assert result["synchronized_rows"] == 1
  assert result["run_id"] == 44
  fetch.assert_called_once_with(
    start_date="2026-07-18",
    end_date="2026-07-20",
  )
  upsert.assert_called_once()
  worker.assert_called_once_with()
  assert not (tmp_path / "data" / "interim").exists()
