"""Inspect research CSVs for gaps, duplicates, and incomplete price rows."""

from pathlib import Path

import pandas as pd


def summarize_dataset(file_path: Path) -> dict:
  """Create a simple quality summary for a CSV dataset."""
  if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # Convert UTC timestamps before checking date range and duplicates.
  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"]
  )

  summary = {
    "file_path": str(file_path),
    "row_count": len(data),
    "column_count": len(data.columns),
    "columns": data.columns.tolist(),
    "min_utc_time": data["datetime_universal_time"].min(),
    "max_utc_time": data["datetime_universal_time"].max(),
    "duplicate_utc_timestamps": int(
      data["datetime_universal_time"].duplicated().sum()
    ),
    "missing_values": data.isna().sum().to_dict(),
  }

  if "actual_price" in data.columns:
    summary["zero_actual_price_count"] = int(
      (data["actual_price"] == 0).sum()
    )

  if "forecast_price" in data.columns:
    summary["zero_forecast_price_count"] = int(
      (data["forecast_price"] == 0).sum()
    )

  return summary


def find_missing_hourly_timestamps(file_path: Path) -> pd.DatetimeIndex:
  """Find missing hourly UTC timestamps in a CSV dataset."""
  if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # UTC timestamps define the expected hourly time-series sequence.
  utc_times = pd.to_datetime(data["datetime_universal_time"])

  expected_times = pd.date_range(
    start=utc_times.min(),
    end=utc_times.max(),
    freq="h",
  )

  missing_times = expected_times.difference(utc_times)

  return missing_times


def find_rows_with_missing_values(file_path: Path, column: str) -> pd.DataFrame:
  """Return rows where a selected column has missing values."""
  if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # Convert timestamps to make the output easier to inspect.
  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"]
  )
  data["datetime_local_time"] = pd.to_datetime(data["datetime_local_time"])

  if column not in data.columns:
    raise ValueError(f"Column not found: {column}")

  return data[data[column].isna()]


def count_recent_incomplete_price_rows(file_path: Path) -> int:
  """Count rows where the actual price is not finalized yet."""
  if not file_path.exists():
    raise FileNotFoundError(f"Dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  if "actual_price" not in data.columns:
    raise ValueError("Column not found: actual_price")

  return int(data["actual_price"].isna().sum())


def print_quality_summary(summary: dict) -> None:
  """Print a readable quality summary."""
  print("\nDATA QUALITY SUMMARY")
  print("-" * 50)

  print(f"File: {summary['file_path']}")
  print(f"Rows: {summary['row_count']}")
  print(f"Columns: {summary['column_count']}")
  print(f"Min UTC time: {summary['min_utc_time']}")
  print(f"Max UTC time: {summary['max_utc_time']}")
  print(f"Duplicate UTC timestamps: {summary['duplicate_utc_timestamps']}")

  print("\nMissing values:")
  for column, missing_count in summary["missing_values"].items():
    print(f"  - {column}: {missing_count}")

  if "zero_actual_price_count" in summary:
    print(f"\nZero actual price count: {summary['zero_actual_price_count']}")

  if "zero_forecast_price_count" in summary:
    print(f"Zero forecast price count: {summary['zero_forecast_price_count']}")


if __name__ == "__main__":
  dataset_path = Path("data/interim/current_historical_prices_clean.csv")
  summary = summarize_dataset(dataset_path)
  print_quality_summary(summary)
  missing_times = find_missing_hourly_timestamps(dataset_path)
  print("\nMissing hourly UTC timestamps:")
  print(f"  - Count: {len(missing_times)}")

  if len(missing_times) > 0:
    print(f"  - First missing: {missing_times.min()}")
    print(f"  - Last missing: {missing_times.max()}")

  missing_actual_price_rows = find_rows_with_missing_values(
    dataset_path,
    "actual_price",
  )

  print("\nRows with missing actual_price:")
  print(missing_actual_price_rows)

  incomplete_price_count = count_recent_incomplete_price_rows(dataset_path)

  print("\nRecent incomplete actual_price rows:")

  print(f"  - Count: {incomplete_price_count}")
