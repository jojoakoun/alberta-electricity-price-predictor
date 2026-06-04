from pathlib import Path
import pandas as pd 
from electricity_predictor.data.ingestion import load_historical_data, validate_historical_data
from electricity_predictor.data.pipeline import build_interim_dataset

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


  duplicated_data = pd.concat([data, data.iloc[[0]]], ignore_index=True)
  duplicated_data = duplicated_data.sort_values("datetime_universal_time").reset_index(drop=True)
  
  try:
    validate_historical_data(duplicated_data)
  except ValueError as error:
    assert "duplicate timestamps" in str(error)
  else:
    raise AssertionError("Expected duplicate UTC timestamps to raise ValueError.")
  
  
def test_build_interim_dataset_writes_clean_file() -> None:
  
  # The data pipeline should create a reusable cleaned CSV file.
  output_path = build_interim_dataset()
  assert output_path.exists()
  data = pd.read_csv(output_path)
  
  assert len(data) > 0

  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load"
  ]