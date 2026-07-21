from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest

from electricity_predictor.worker.operational_refresh import (
  derive_api_start_date,
  synchronize_operational_prices,
)


def build_api_report() -> dict:
  return {
    "return": {
      "Pool Price Report": [
        {
          "begin_datetime_utc": "2026-07-20 12:00",
          "begin_datetime_mpt": "2026-07-20 06:00",
          "pool_price": "42.50",
          "forecast_pool_price": "40.00",
        },
        {
          "begin_datetime_utc": "2026-07-20 13:00",
          "begin_datetime_mpt": "2026-07-20 07:00",
          "pool_price": None,
          "forecast_pool_price": "41.25",
        },
      ]
    }
  }


def test_derive_api_start_date_uses_database_timestamp_with_overlap() -> None:
  assert derive_api_start_date(
    pd.Timestamp("2026-07-20 13:00", tz="UTC")
  ) == "2026-07-18"


def test_derive_api_start_date_uses_alberta_market_date_near_utc_midnight() -> None:
  assert derive_api_start_date(
    pd.Timestamp("2026-07-21 03:00", tz="UTC")
  ) == "2026-07-18"


def test_operational_refresh_requires_historical_database_seed() -> None:
  with patch(
    "electricity_predictor.worker.operational_refresh."
    "get_latest_hourly_price_timestamp",
    return_value=None,
  ):
    with pytest.raises(
      RuntimeError,
      match="historical database seed",
    ):
      synchronize_operational_prices(
        end_date="2026-07-20"
      )


def test_operational_refresh_uses_postgresql_without_local_csvs(
  tmp_path: Path,
  monkeypatch,
) -> None:
  raw_dir = tmp_path / "data" / "raw"
  raw_dir.mkdir(parents=True)
  (raw_dir / ".gitkeep").touch()
  monkeypatch.chdir(tmp_path)

  captured: dict = {}

  def fake_fetch(start_date: str, end_date: str) -> dict:
    captured["request"] = (start_date, end_date)
    return build_api_report()

  def fake_upsert(data: pd.DataFrame, source: str) -> int:
    captured["data"] = data.copy()
    captured["source"] = source
    return len(data)

  with (
    patch(
      "electricity_predictor.worker.operational_refresh."
      "get_latest_hourly_price_timestamp",
      return_value=pd.Timestamp(
        "2026-07-20 13:00",
        tz="UTC",
      ),
    ),
    patch(
      "electricity_predictor.worker.operational_refresh."
      "fetch_pool_price_report",
      side_effect=fake_fetch,
    ),
    patch(
      "electricity_predictor.worker.operational_refresh."
      "upsert_hourly_prices",
      side_effect=fake_upsert,
    ),
  ):
    synchronized_rows = synchronize_operational_prices(
      end_date="2026-07-20"
    )

  assert synchronized_rows == 2
  assert captured["request"] == (
    "2026-07-18",
    "2026-07-20",
  )
  assert captured["source"] == "aeso_api"
  assert list(captured["data"].columns) == [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]
  assert pd.isna(
    captured["data"].iloc[1]["actual_price"]
  )
  assert str(
    captured["data"][
      "datetime_universal_time"
    ].dt.tz
  ) == "UTC"
  assert not (tmp_path / "data" / "interim").exists()


def test_repeated_operational_refresh_sends_one_stable_row_per_timestamp() -> None:
  stored_rows: dict[pd.Timestamp, dict] = {}

  def fake_upsert(data: pd.DataFrame, source: str) -> int:
    assert source == "aeso_api"

    for row in data.to_dict(orient="records"):
      stored_rows[row["datetime_universal_time"]] = row

    return len(data)

  with (
    patch(
      "electricity_predictor.worker.operational_refresh."
      "get_latest_hourly_price_timestamp",
      return_value=pd.Timestamp(
        "2026-07-20 13:00",
        tz="UTC",
      ),
    ),
    patch(
      "electricity_predictor.worker.operational_refresh."
      "fetch_pool_price_report",
      return_value=build_api_report(),
    ),
    patch(
      "electricity_predictor.worker.operational_refresh."
      "upsert_hourly_prices",
      side_effect=fake_upsert,
    ),
  ):
    first_count = synchronize_operational_prices(
      end_date="2026-07-20"
    )
    second_count = synchronize_operational_prices(
      end_date="2026-07-20"
    )

  assert first_count == 2
  assert second_count == 2
  assert len(stored_rows) == 2
