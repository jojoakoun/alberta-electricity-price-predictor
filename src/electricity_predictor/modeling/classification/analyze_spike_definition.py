from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import build_target_column_name
from electricity_predictor.modeling.classification.spike_definition import (
  calculate_iqr_spike_threshold,
  calculate_quantile_spike_threshold,
  summarize_spikes,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data,
)


ACTUAL_PRICE_COLUMN = "actual_price"

SPIKE_ANALYSIS_PATH = Path("reports/spike_definition_analysis.csv")

SPIKE_ANALYSIS_COLUMNS = [
  "method",
  "horizon_hours",
  "target_column",
  "threshold",
  "split",
  "row_count",
  "spike_count",
  "non_spike_count",
  "spike_rate",
]


def calculate_train_thresholds(train_prices: pd.Series) -> dict[str, float]:
  """Calculate candidate spike thresholds from train prices only."""
  return {
    "iqr": calculate_iqr_spike_threshold(train_prices),
    "q95": calculate_quantile_spike_threshold(train_prices, quantile=0.95),
    "q99": calculate_quantile_spike_threshold(train_prices, quantile=0.99),
  }


def build_spike_analysis_rows(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  test_data: pd.DataFrame,
  horizons_hours: list[int],
) -> list[dict]:
  """Compare one train-derived spike threshold across all horizons."""
  rows = []

  split_data = {
    "train": train_data,
    "validation": validation_data,
    "test": test_data,
  }

  # Learn one global spike definition from historical train prices only.
  thresholds = calculate_train_thresholds(
    train_data[ACTUAL_PRICE_COLUMN]
  )

  for horizon_hours in horizons_hours:
    target_column = build_target_column_name(horizon_hours)

    if target_column not in train_data.columns:
      raise ValueError(f"Missing target column: {target_column}")

    for method, threshold in thresholds.items():
      for split_name, data in split_data.items():
        if target_column not in data.columns:
          raise ValueError(f"Missing target column: {target_column}")

        summary = summarize_spikes(
          prices=data[target_column],
          threshold=threshold,
        )

        rows.append(
          {
            "method": method,
            "horizon_hours": horizon_hours,
            "target_column": target_column,
            "threshold": threshold,
            "split": split_name,
            **summary,
          }
        )

  return rows


def write_spike_analysis(
  rows: list[dict],
  output_path: Path = SPIKE_ANALYSIS_PATH,
) -> Path:
  """Write the spike-definition comparison report."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  report = pd.DataFrame(rows, columns=SPIKE_ANALYSIS_COLUMNS)
  report.to_csv(output_path, index=False)

  return output_path


def run_spike_definition_analysis(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  output_path: Path = SPIKE_ANALYSIS_PATH,
) -> Path:
  """Run the train-only spike-threshold analysis."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]

  data = load_training_dataset(training_dataset_path)

  train_data, validation_data, test_data = split_time_series_data(
    data=data,
    train_ratio=modeling_config["train_ratio"],
    validation_ratio=modeling_config["validation_ratio"],
    test_ratio=modeling_config["test_ratio"],
  )

  rows = build_spike_analysis_rows(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=modeling_config["horizons_hours"],
  )

  return write_spike_analysis(
    rows=rows,
    output_path=output_path,
  )


def print_spike_analysis_summary(report_path: Path) -> None:
  """Print a compact comparison of spike rates by method and horizon."""
  report = pd.read_csv(report_path)

  summary = report.pivot_table(
    index=["method", "horizon_hours", "threshold"],
    columns="split",
    values="spike_rate",
  ).reset_index()

  for split_name in ["train", "validation", "test"]:
    if split_name in summary.columns:
      summary[split_name] = summary[split_name] * 100

  print("Spike-definition analysis")
  print("=========================")
  print(summary.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
  print("")
  print(f"Report written to: {report_path}")


if __name__ == "__main__":
  written_path = run_spike_definition_analysis()
  print_spike_analysis_summary(written_path)
