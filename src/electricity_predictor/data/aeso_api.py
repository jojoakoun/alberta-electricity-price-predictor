
import os
from typing import Any
import pandas as pd 
import requests
from dotenv import load_dotenv

from electricity_predictor.config import load_configuration

API_COLUMNS = {
  "begin_datetime_utc": "datetime_universal_time",  # UTC timestamp returned by AESO.
  "begin_datetime_mpt": "datetime_local_time",  # Alberta local timestamp returned by AESO.
  "pool_price": "actual_price",  # Actual pool price for the completed hour.
  "forecast_pool_price": "forecast_price",  # Forecasted pool price for that hour.
}


def fetch_pool_price_report(start_date: str, end_date: str) -> dict[str, Any]:
  """Fetch the AESO pool price report from the public API."""
  load_dotenv()

  configuration = load_configuration()
  base_url = os.getenv("AESO_API_BASE_URL", configuration["api"]["aeso_base_url"])
  subscription_key = os.getenv("AESO_API_SUBSCRIPTION_KEY")
  

  if not subscription_key:
    raise ValueError("Missing AESO_API_SUBSCRIPTION_KEY in local environment.")

  url = f"{base_url}{configuration['api']['aeso_pool_price_endpoint']}"
  
   # The project fetches a date range so we can extend the historical dataset.

  params = {
    "startDate": start_date,
    "endDate": end_date,
  }

  # AESO uses an API subscription key to authorize requests.
  headers = {
    "API-KEY": subscription_key,
  }
  response = requests.get(url, headers=headers, params=params, timeout=30)
  response.raise_for_status()

  return response.json()


def normalize_pool_price_report(report: dict[str, Any]) -> pd.DataFrame:
  """Convert the AESO pool price JSON response into a clean DataFrame."""

  # AESO stores the hourly records inside the return payload.
  records = report.get("return", {}).get("Pool Price Report", [])
  
  if not records:
    raise ValueError("AESO response does not contain pool price records.")
  
  data = pd.DataFrame(records)
  
  data = data.rename(columns=API_COLUMNS)
  
  # Keep only the columns that match the historical data schema.

  data = data[list(API_COLUMNS.values())]

  data["datetime_universal_time"] = pd.to_datetime(data["datetime_universal_time"])
  data["datetime_local_time"] = pd.to_datetime(data["datetime_local_time"])
  data["actual_price"] = pd.to_numeric(data["actual_price"])
  data["forecast_price"] = pd.to_numeric(data["forecast_price"])
  
  data = data.sort_values("datetime_universal_time").reset_index(drop=True)
  # Stop early if the normalized API data is invalid.
  validate_pool_price_data(data)

  return data


def validate_pool_price_data(data: pd.DataFrame) -> None:
  """Validate normalized AESO pool price data."""
  required_columns = set(API_COLUMNS.values())
  missing_columns = required_columns - set(data.columns)
  

  if missing_columns:
    raise ValueError(f"Missing required API columns: {sorted(missing_columns)}")

  # These fields are required before merging API data with historical data.
  required_non_null_columns = [
    "datetime_universal_time",
    "datetime_local_time",
    "forecast_price",
  ]

  for column in required_non_null_columns:
    if data[column].isna().any():
      raise ValueError(f"API column contains missing values: {column}")

  # API records should not repeat the same UTC hour.
  if data["datetime_universal_time"].duplicated().any():
    raise ValueError("API data contains duplicate UTC timestamps.")

  # API time-series data must stay in chronological order.
  if not data["datetime_universal_time"].is_monotonic_increasing:
    raise ValueError("API data must be sorted by datetime_universal_time.")





if __name__ == "__main__":
  report = fetch_pool_price_report(start_date="2026-06-01", end_date="2026-06-04")

  data = normalize_pool_price_report(report)

  print(data.head())
  print(data.shape)
  print(data.columns.tolist())
 