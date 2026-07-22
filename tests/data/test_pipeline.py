from pathlib import Path

import pandas as pd
from pandas.api.types import is_numeric_dtype
import pytest

from electricity_predictor.data import pipeline

from .test_ingestion import write_fake_historical_csv


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


def test_get_api_start_date_for_history_overlap_includes_final_market_date() -> None:
  data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        [
          "2025-08-01 01:00",
          "2025-08-01 02:00",
          "2025-08-01 03:00",
        ]
      )
    }
  )

  start_date = pipeline.get_api_start_date_for_history_overlap(data)

  assert start_date == "2025-07-31"


def test_api_actual_does_not_replace_finalized_historical_actual() -> None:
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

  revised_forecast = combined_data.loc[
    combined_data["datetime_universal_time"] == pd.Timestamp(
      "2025-07-31 23:00"
    ),
    "forecast_price",
  ].iloc[0]

  assert revised_forecast == 999.0
  assert combined_data.loc[
    combined_data["datetime_universal_time"] == pd.Timestamp(
      "2025-07-31 23:00"
    ),
    "alberta_internal_load",
  ].iloc[0] == 10100


def test_api_actual_fills_null_historical_actual() -> None:
  historical_data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        ["2025-07-31 23:00"]
      ),
      "datetime_local_time": pd.to_datetime(
        ["2025-07-31 17:00"]
      ),
      "actual_price": [None],
      "forecast_price": [48.0],
      "alberta_internal_load": [10100.0],
    }
  )
  api_data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        ["2025-07-31 23:00"],
        utc=True,
      ),
      "datetime_local_time": pd.to_datetime(
        ["2025-07-31 17:00"]
      ),
      "actual_price": [52.0],
      "forecast_price": [49.0],
    }
  )

  combined_data = pipeline.combine_historical_and_api_data(
    historical_data=historical_data,
    api_data=api_data,
  )

  assert len(combined_data) == 1
  assert combined_data.iloc[0]["actual_price"] == 52.0
  assert combined_data.iloc[0]["forecast_price"] == 49.0
  assert combined_data.iloc[0]["alberta_internal_load"] == 10100.0
  assert is_numeric_dtype(combined_data["actual_price"])
  assert is_numeric_dtype(combined_data["forecast_price"])
  assert is_numeric_dtype(combined_data["alberta_internal_load"])
  assert combined_data.iloc[0][
    "datetime_universal_time"
  ] == pd.Timestamp("2025-07-31 23:00")


def test_combine_historical_and_api_data_requires_price_columns() -> None:
  historical_data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        ["2025-07-31 23:00"]
      ),
      "datetime_local_time": pd.to_datetime(
        ["2025-07-31 17:00"]
      ),
      "actual_price": [52.0],
      "forecast_price": [49.0],
      "alberta_internal_load": [10100.0],
    }
  )
  api_data = historical_data.drop(columns="forecast_price")

  with pytest.raises(
    ValueError,
    match="API dataset is missing columns.*forecast_price",
  ):
    pipeline.combine_historical_and_api_data(
      historical_data=historical_data,
      api_data=api_data,
    )


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
    "start_date": "2025-07-31",
    "end_date": "2025-08-01",
  }

  assert output_path == interim_data_dir / "current_historical_prices_clean.csv"
  assert output_path.exists()

  data = pd.read_csv(output_path)

  assert len(data) == 4
  assert 999.0 not in data["actual_price"].tolist()
  assert 999.0 in data["forecast_price"].tolist()
