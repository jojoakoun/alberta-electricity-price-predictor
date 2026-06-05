from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.data.aeso_api import fetch_pool_price_report,normalize_pool_price_report
from electricity_predictor.data.ingestion import load_historical_data


def get_pipeline_paths() -> tuple[Path, Path]:
  """Get the main paths needed by the data pipeline."""
  configuration = load_configuration()

  raw_data_dir = Path(configuration["paths"]["raw_data_dir"])
  interim_data_dir = Path(configuration["paths"]["interim_data_dir"])
  csv_name = configuration["data"]["historical_csv_name"]

  # Build the full path to the raw historical CSV.
  raw_csv_path = raw_data_dir / csv_name

  return raw_csv_path, interim_data_dir


def build_clean_historical_dataset() -> Path:
  """Build the cleaned historical dataset from the raw CSV."""
  raw_csv_path, interim_data_dir = get_pipeline_paths()
  output_path = interim_data_dir / "csv_historical_prices_clean.csv"

  # Create the output folder if it does not exist yet.
  interim_data_dir.mkdir(parents=True, exist_ok=True)

  data = load_historical_data(raw_csv_path)
  data.to_csv(output_path, index=False)

  return output_path


def get_api_start_date_after_history(historical_data: pd.DataFrame) -> str:
  """Get the first API date needed after the historical CSV ends."""
  last_historical_time = historical_data["datetime_universal_time"].max()

  # AESO accepts dates, so we convert the next missing hour to yyyy-mm-dd.
  next_missing_hour = last_historical_time + pd.Timedelta(hours=1)

  return next_missing_hour.strftime("%Y-%m-%d")


def combine_historical_and_api_data(historical_data: pd.DataFrame,api_data: pd.DataFrame) -> pd.DataFrame:
  """Combine historical CSV data with new AESO API data."""

  last_historical_time = historical_data["datetime_universal_time"].max()

  # API data should extend the historical CSV, not replace existing rows.
  api_data = api_data[api_data["datetime_universal_time"] > last_historical_time]

  # Combine the original history with only the new API hours.
  combined_data = pd.concat([historical_data, api_data], ignore_index=True)

  # The combined dataset must keep one row per UTC hour.
  if combined_data["datetime_universal_time"].duplicated().any():
    raise ValueError("Combined dataset contains duplicate UTC timestamps.")

  # Keep the final dataset in chronological order.
  combined_data = combined_data.sort_values("datetime_universal_time").reset_index(drop=True)
  
  return combined_data


def build_extended_historical_dataset(end_date: str) -> Path:
  """Build a historical dataset extended with AESO API data."""
  raw_csv_path, interim_data_dir = get_pipeline_paths()
  output_path = interim_data_dir / "extended_historical_prices_clean.csv"

  # Create the output folder if it does not exist yet.
  interim_data_dir.mkdir(parents=True, exist_ok=True)

  historical_data = load_historical_data(raw_csv_path)
  start_date = get_api_start_date_after_history(historical_data)

  api_report = fetch_pool_price_report(start_date=start_date, end_date=end_date)
  api_data = normalize_pool_price_report(api_report)

  combined_data = combine_historical_and_api_data(historical_data=historical_data, api_data=api_data)

  combined_data.to_csv(output_path, index=False)

  return output_path


if __name__ == "__main__":
  output_path = build_clean_historical_dataset()
  print(f"Clean historical dataset written to: {output_path}")