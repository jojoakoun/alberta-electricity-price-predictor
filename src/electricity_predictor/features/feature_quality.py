from pathlib import Path

import pandas as pd

ENGINEERED_FEATURE_COLUMNS = [
  "actual_price_lag_1h",
  "actual_price_lag_24h",
  "forecast_price_lag_1h",
  "actual_price_rolling_24h_mean",
  "actual_price_rolling_24h_max",
  "actual_price_rolling_7d_mean",
]

def summarize_feature_quality(file_path: Path) -> dict:
  """Summarize missing values created by feature engineering."""

  if not file_path.exists():
    raise FileNotFoundError(f"Modeling dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # These checks show whether lag and rolling features created unusable model rows.
  missing_by_column = data.isna().sum()

  # We focus on engineered features because raw target rows were already cleaned earlier.
  missing_engineered_features = data[ENGINEERED_FEATURE_COLUMNS].isna().sum()

  # This shows how many rows would remain if we train only on complete feature rows.
  complete_feature_rows = data.dropna(subset=ENGINEERED_FEATURE_COLUMNS)

  return {
    "file_path": str(file_path),
    "rows": len(data),
    "columns": len(data.columns),
    "missing_by_column": missing_by_column,
    "missing_engineered_features": missing_engineered_features,
    "rows_after_dropping_missing_engineered_features": len(complete_feature_rows),
    "rows_removed": len(data) - len(complete_feature_rows),
  }

def print_feature_quality_summary(summary: dict) -> None:
  """Print a readable feature quality summary."""

  print("Feature quality report")
  print("======================")
  print(f"File: {summary['file_path']}")
  print(f"Rows: {summary['rows']:,}")
  print(f"Columns: {summary['columns']}")
  print()
  print("Missing values by column")
  print("------------------------")
  print(summary["missing_by_column"].to_string())
  print()
  print("Missing values in engineered features")
  print("-------------------------------------")
  print(summary["missing_engineered_features"].to_string())
  print()
  print("Rows after dropping missing engineered features")
  print("-----------------------------------------------")
  print(f"Rows remaining: {summary['rows_after_dropping_missing_engineered_features']:,}")
  print(f"Rows removed: {summary['rows_removed']:,}")


if __name__ == "__main__":
  modeling_dataset_path = Path("data/processed/modeling_dataset.csv")
  quality_summary = summarize_feature_quality(modeling_dataset_path)
  print_feature_quality_summary(quality_summary)
