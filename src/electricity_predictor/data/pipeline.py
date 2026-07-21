"""Rebuild research CSV datasets; the recurring worker does not use this path."""

from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.data.aeso_api import (
  fetch_pool_price_report,
  normalize_pool_price_report,
)
from electricity_predictor.data.ingestion import load_historical_data


def get_pipeline_paths() -> tuple[Path, Path]:
  """Get the main paths needed by the data pipeline."""
  configuration = load_configuration()

  raw_data_dir = Path(configuration["paths"]["raw_data_dir"])
  interim_data_dir = Path(configuration["paths"]["interim_data_dir"])
  csv_name = configuration["data"]["historical_csv_name"]

  raw_csv_path = raw_data_dir / csv_name

  return raw_csv_path, interim_data_dir


def get_current_api_end_date() -> str:
  """Get the current Alberta date for the AESO API."""
  # AESO pool price dates follow Alberta market time.
  current_alberta_time = datetime.now(ZoneInfo("America/Edmonton"))

  return current_alberta_time.strftime("%Y-%m-%d")


def build_clean_historical_dataset() -> Path:
  """Build the cleaned historical dataset from the raw CSV."""
  raw_csv_path, interim_data_dir = get_pipeline_paths()
  output_path = interim_data_dir / "csv_historical_prices_clean.csv"

  interim_data_dir.mkdir(parents=True, exist_ok=True)

  data = load_historical_data(raw_csv_path)
  data.to_csv(output_path, index=False)

  return output_path


def get_api_start_date_for_history_overlap(
  historical_data: pd.DataFrame,
) -> str:
  """Return the final historical Alberta date so AESO can revise that day."""
  last_historical_time = pd.Timestamp(
    historical_data["datetime_universal_time"].max()
  )

  if last_historical_time.tzinfo is None:
    last_historical_time = last_historical_time.tz_localize("UTC")
  else:
    last_historical_time = last_historical_time.tz_convert("UTC")

  final_market_date = last_historical_time.tz_convert(
    ZoneInfo("America/Edmonton")
  )

  return final_market_date.strftime("%Y-%m-%d")


def combine_historical_and_api_data(
  historical_data: pd.DataFrame,
  api_data: pd.DataFrame,
) -> pd.DataFrame:
  """Merge research history with AESO rows using explicit field precedence.

  Finalized historical actuals are immutable. AESO actuals fill only missing
  observations, while the newest non-null AESO forecast is an approved revision.
  """
  timestamp_column = "datetime_universal_time"
  historical_required_columns = {
    timestamp_column,
    "datetime_local_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  }
  api_required_columns = {
    timestamp_column,
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  }

  for source_name, source_data, required_columns in [
    (
      "Historical",
      historical_data,
      historical_required_columns,
    ),
    ("API", api_data, api_required_columns),
  ]:
    missing_columns = required_columns - set(source_data.columns)

    if missing_columns:
      raise ValueError(
        f"{source_name} dataset is missing columns: "
        f"{sorted(missing_columns)}"
      )

  historical_data = historical_data.copy()
  api_data = api_data.copy()

  for source_name, source_data in [
    ("Historical", historical_data),
    ("API", api_data),
  ]:
    source_data[timestamp_column] = pd.to_datetime(
      source_data[timestamp_column],
      utc=True,
    ).dt.tz_localize(None)

    if source_data[timestamp_column].duplicated().any():
      raise ValueError(
        f"{source_name} dataset contains duplicate UTC timestamps."
      )

  historical_by_time = historical_data.set_index(timestamp_column)
  api_by_time = api_data.set_index(timestamp_column)
  combined_index = historical_by_time.index.union(
    api_by_time.index
  ).sort_values()

  def aligned_column(
    source_data: pd.DataFrame,
    column_name: str,
  ) -> pd.Series:
    """Align one optional source column to the union of hourly timestamps."""
    if column_name not in source_data.columns:
      return pd.Series(index=combined_index, dtype="object")

    return source_data[column_name].reindex(combined_index)

  historical_local_time = aligned_column(
    historical_by_time,
    "datetime_local_time",
  )
  api_local_time = aligned_column(
    api_by_time,
    "datetime_local_time",
  )
  historical_actual = aligned_column(
    historical_by_time,
    "actual_price",
  )
  api_actual = aligned_column(
    api_by_time,
    "actual_price",
  )
  historical_forecast = aligned_column(
    historical_by_time,
    "forecast_price",
  )
  api_forecast = aligned_column(
    api_by_time,
    "forecast_price",
  )
  historical_load = aligned_column(
    historical_by_time,
    "alberta_internal_load",
  )
  api_load = aligned_column(
    api_by_time,
    "alberta_internal_load",
  )

  combined_actual = pd.to_numeric(
    historical_actual.combine_first(api_actual),
    errors="raise",
  )
  combined_forecast = pd.to_numeric(
    api_forecast.combine_first(historical_forecast),
    errors="raise",
  )
  combined_load = pd.to_numeric(
    historical_load.combine_first(api_load),
    errors="raise",
  )
  combined_data = pd.DataFrame(
    {
      timestamp_column: combined_index,
      "datetime_local_time": historical_local_time.combine_first(
        api_local_time
      ).to_numpy(),
      # Finalized historical actuals win; API actuals only fill nulls.
      "actual_price": combined_actual.to_numpy(),
      # The newest non-null API forecast is an approved revision.
      "forecast_price": combined_forecast.to_numpy(),
      "alberta_internal_load": combined_load.to_numpy(),
    }
  )

  return combined_data.reset_index(drop=True)


def build_current_historical_dataset(end_date: str | None = None) -> Path:
  """Build the research CSV used for model development and lifecycle runs.

  This full-history rebuild is deliberately separate from the PostgreSQL-first
  recurring worker.
  """
  raw_csv_path, interim_data_dir = get_pipeline_paths()
  output_path = interim_data_dir / "current_historical_prices_clean.csv"

  interim_data_dir.mkdir(parents=True, exist_ok=True)

  historical_data = load_historical_data(raw_csv_path)
  start_date = get_api_start_date_for_history_overlap(
    historical_data
  )

  if end_date is None:
    end_date = get_current_api_end_date()

  api_report = fetch_pool_price_report(start_date=start_date, end_date=end_date)
  api_data = normalize_pool_price_report(api_report)

  combined_data = combine_historical_and_api_data(
    historical_data=historical_data,
    api_data=api_data,
  )

  combined_data.to_csv(output_path, index=False)

  return output_path


if __name__ == "__main__":
  output_path = build_current_historical_dataset()
  print(f"Current historical dataset written to: {output_path}")
