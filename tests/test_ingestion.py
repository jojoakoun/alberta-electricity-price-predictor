from pathlib import Path

import pandas as pd

from electricity_predictor.data.ingestion import load_historical_data, validate_historical_data
from electricity_predictor.data.pipeline import (
  build_clean_historical_dataset,
  combine_historical_and_api_data,
  get_api_start_date_after_history,
)


CSV_PATH = Path("data/raw/Hourly_Metered_Volumes_and_Pool_Price_and_AIL_2020-Jul2025.csv")


def test_load_historical_data_returns_expected_columns() -> None:
  # The ingestion step should expose only the clean project columns.
  data = load_historical_data(CSV_PATH)

  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]


def test_load_historical_data_returns_rows() -> None:
  # The historical CSV should contain data after loading.
  data = load_historical_data(CSV_PATH)

  assert len(data) > 0


def test_load_historical_data_sorts_by_utc_time() -> None:
  # Time-series data must be sorted before feature engineering.
  data = load_historical_data(CSV_PATH)

  assert data["datetime_universal_time"].is_monotonic_increasing


def test_validate_historical_data_rejects_duplicate_utc_timestamps() -> None:
  # Each UTC timestamp should appear only once in the historical data.
  data = load_historical_data(CSV_PATH)

  # Add a copied row to simulate a bad dataset with a duplicate hour.
  duplicated_data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
  duplicated_data = duplicated_data.sort_values("datetime_universal_time").reset_index(drop=True)

  try:
    validate_historical_data(duplicated_data)
  except ValueError as error:
    assert "duplicate timestamps" in str(error)
  else:
    raise AssertionError("Expected duplicate UTC timestamps to raise ValueError.")


def test_build_clean_historical_dataset_writes_clean_file() -> None:
  # The data pipeline should create a reusable cleaned CSV file.
  output_path = build_clean_historical_dataset()

  assert output_path.exists()

  data = pd.read_csv(output_path)

  assert len(data) > 0
  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  ]


def test_get_api_start_date_after_history_returns_next_day_when_history_ends_at_23h() -> None:
  # AESO accepts dates, so the API should start on the date of the next missing hour.
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

  start_date = get_api_start_date_after_history(data)

  assert start_date == "2025-08-01"


def test_combine_historical_and_api_data_keeps_only_new_api_hours() -> None:
  # Historical rows are the trusted base and should not be overwritten by API rows.
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

  # The API includes one duplicate hour and one new hour.
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

  combined_data = combine_historical_and_api_data(
    historical_data=historical_data,
    api_data=api_data,
  )

  # The duplicate API hour should be removed, leaving two historical rows and one new API row.
  assert len(combined_data) == 3

  # The final dataset should stay sorted by UTC time.
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

  # If the API overwrote the historical row, this value would be 999.0.
  assert historical_23h_price == 50.0