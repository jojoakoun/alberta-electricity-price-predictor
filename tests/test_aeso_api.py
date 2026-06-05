import pandas as pd

from electricity_predictor.data.aeso_api import normalize_pool_price_report

def test_normalize_pool_price_report_returns_clean_columns() -> None:

  # This fake response matches the AESO JSON structure used by our parser.
  fake_report = {
    "return": {
      "Pool Price Report": [
        {
          "begin_datetime_utc": "2025-07-01 06:00",
          "begin_datetime_mpt": "2025-07-01 00:00",
          "pool_price": "29.06",
          "forecast_pool_price": "28.31",
          "rolling_30day_avg": "46.79",
        }
      ]
    }
  }

  data = normalize_pool_price_report(fake_report)

  assert data.columns.tolist() == [
    "datetime_universal_time",
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  ]
  



def test_normalize_pool_price_report_converts_types() -> None:

  # Dates should become datetime values and prices should become numeric values.
  fake_report = {
    "return": {
      "Pool Price Report": [
        {
          "begin_datetime_utc": "2025-07-01 06:00",
          "begin_datetime_mpt": "2025-07-01 00:00",
          "pool_price": "29.06",
          "forecast_pool_price": "28.31",
          "rolling_30day_avg": "46.79",
        }
      ]
    }
  }

  data = normalize_pool_price_report(fake_report)

  assert pd.api.types.is_datetime64_any_dtype(data["datetime_universal_time"])
  assert pd.api.types.is_datetime64_any_dtype(data["datetime_local_time"])
  assert pd.api.types.is_numeric_dtype(data["actual_price"])
  assert pd.api.types.is_numeric_dtype(data["forecast_price"])
  



def test_normalize_pool_price_report_rejects_empty_records() -> None:

  # An empty API response should fail early with a clear error.
  fake_report = {
    "return": {
      "Pool Price Report": []
    }
  }

  try:
    normalize_pool_price_report(fake_report)
  except ValueError as error:
    assert "does not contain pool price records" in str(error)
  else:
    raise AssertionError("Expected empty API records to raise ValueError.")