"""Summarize completeness of engineered research features."""

from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import ENGINEERED_FEATURE_COLUMNS


def summarize_feature_quality(file_path: Path) -> dict:
  """Summarize missing values created by feature engineering."""
  if not file_path.exists():
    raise FileNotFoundError(f"Modeling dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  missing_by_column = data.isna().sum()

  # Raw target rows are cleaned earlier; this report isolates feature losses.
  missing_engineered_features = data[ENGINEERED_FEATURE_COLUMNS].isna().sum()

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
  print(
    "Rows remaining: "
    f"{summary['rows_after_dropping_missing_engineered_features']:,}"
  )
  print(f"Rows removed: {summary['rows_removed']:,}")


if __name__ == "__main__":
  modeling_dataset_path = Path("data/processed/modeling_dataset.csv")
  quality_summary = summarize_feature_quality(modeling_dataset_path)
  print_feature_quality_summary(quality_summary)
