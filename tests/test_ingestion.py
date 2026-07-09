from pathlib import Path

import pandas as pd

from electricity_predictor.data import pipeline
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


def test_build_clean_historical_dataset_writes_clean_file(
  tmp_path: Path,
  monkeypatch,
) -> None:
  raw_csv_path = tmp_path / "raw" / "historical.csv"
  interim_data_dir = tmp_path / "interim"
  write_fake_historical_csv(raw_csv_path)

  # Keep this test away from the real project data folders.
  monkeypatch.setattr(
    pipeline,
    "get_pipeline_paths",
    lambda: (raw_csv_path, interim_data_dir),
  )

  output_path = pipeline.build_clean_historical_dataset()

  assert output_path == interim_data_dir / "csv_historical_prices_clean.csv"
  assert output_path.exists()

  data = pd.read_csv(output_path)

  assert len(data) == 3
  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]


def test_get_api_start_date_after_history_returns_next_day_when_history_ends_at_23h() -> None:
  data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        [
          "2025-07-31 21:00",
          "2025-07-31 22:00",
          "2025-07-31 23:00",
        ]
      )
    }
  )

  start_date = pipeline.get_api_start_date_after_history(data)

  assert start_date == "2025-08-01"


def test_combine_historical_and_api_data_keeps_only_new_api_hours() -> None:
  historical_data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        [
          "2025-07-31 22:00",
          "2025-07-31 23:00",
        ]
      ),
      "datetime_local_time": pd.to_datetime(
        [
          "2025-07-31 16:00",
          "2025-07-31 17:00",
        ]
      ),
      "actual_price": [40.0, 50.0],
      "forecast_price": [38.0, 48.0],
      "alberta_internal_load": [10000, 10100],
    }
  )

  api_data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        [
          "2025-07-31 23:00",
          "2025-08-01 00:00",
        ]
      ),
      "datetime_local_time": pd.to_datetime(
        [
          "2025-07-31 17:00",
          "2025-07-31 18:00",
        ]
      ),
      "actual_price": [999.0, 60.0],
      "forecast_price": [999.0, 58.0],
    }
  )

  combined_data = pipeline.combine_historical_and_api_data(
    historical_data=historical_data,
    api_data=api_data,
  )

  assert len(combined_data) == 3
  assert combined_data["datetime_universal_time"].tolist() == pd.to_datetime(
    [
      "2025-07-31 22:00",
      "2025-07-31 23:00",
      "2025-08-01 00:00",
    ]
  ).tolist()

  historical_23h_price = combined_data.loc[
    combined_data["datetime_universal_time"] == pd.Timestamp("2025-07-31 23:00"),
    "actual_price",
  ].iloc[0]

  assert historical_23h_price == 50.0


def test_build_current_historical_dataset_uses_mocked_api_and_temp_paths(
  tmp_path: Path,
  monkeypatch,
) -> None:
  raw_csv_path = tmp_path / "raw" / "historical.csv"
  interim_data_dir = tmp_path / "interim"
  write_fake_historical_csv(raw_csv_path)

  captured_request = {}

  def fake_fetch_pool_price_report(start_date: str, end_date: str):
    captured_request["start_date"] = start_date
    captured_request["end_date"] = end_date
    return {"fake": "api_report"}

  def fake_normalize_pool_price_report(api_report):
    assert api_report == {"fake": "api_report"}

    return pd.DataFrame(
      {
        "datetime_universal_time": pd.to_datetime(
          [
            "2025-07-31 23:00",
            "2025-08-01 00:00",
          ]
        ),
        "datetime_local_time": pd.to_datetime(
          [
            "2025-07-31 17:00",
            "2025-07-31 18:00",
          ]
        ),
        "actual_price": [999.0, 60.0],
        "forecast_price": [999.0, 58.0],
      }
    )

  # The current dataset builder should be testable without real files or network calls.
  monkeypatch.setattr(
    pipeline,
    "get_pipeline_paths",
    lambda: (raw_csv_path, interim_data_dir),
  )
  monkeypatch.setattr(pipeline, "fetch_pool_price_report", fake_fetch_pool_price_report)
  monkeypatch.setattr(pipeline, "normalize_pool_price_report", fake_normalize_pool_price_report)

  output_path = pipeline.build_current_historical_dataset(end_date="2025-08-01")

  assert captured_request == {
    "start_date": "2025-08-01",
    "end_date": "2025-08-01",
  }

  assert output_path == interim_data_dir / "current_historical_prices_clean.csv"
  assert output_path.exists()

  data = pd.read_csv(output_path)

  assert len(data) == 4
  assert 999.0 not in data["actual_price"].tolist()
