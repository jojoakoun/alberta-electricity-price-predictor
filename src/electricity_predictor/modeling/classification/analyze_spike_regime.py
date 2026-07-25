from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.classification.spike_definition import (
  calculate_iqr_spike_threshold,
  classify_spikes,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)
from electricity_predictor.contracts.columns import (
  ACTUAL_PRICE_COLUMN,
  DATETIME_COLUMN,
)



SPIKE_REGIME_ANALYSIS_PATH = Path(
  "reports/spike_regime_analysis.csv"
)

SPIKE_REGIME_ANALYSIS_COLUMNS = [
  "split",
  "year",
  "first_timestamp",
  "last_timestamp",
  "threshold_method",
  "threshold",
  "row_count",
  "spike_count",
  "non_spike_count",
  "spike_rate",
  "mean_price",
  "median_price",
  "price_std",
  "p95_price",
  "max_price",
]


def validate_regime_data(data: pd.DataFrame) -> None:
  """Validate the columns required for temporal spike analysis."""
  required_columns = {
    DATETIME_COLUMN,
    ACTUAL_PRICE_COLUMN,
  }
  missing_columns = required_columns - set(data.columns)

  if missing_columns:
    raise ValueError(
      f"Missing required regime-analysis columns: {sorted(missing_columns)}"
    )

  if data[DATETIME_COLUMN].isna().any():
    raise ValueError(
      "Spike regime analysis requires non-missing UTC timestamps."
    )

  if data[ACTUAL_PRICE_COLUMN].isna().any():
    raise ValueError(
      "Spike regime analysis requires non-missing actual prices."
    )

  if not pd.api.types.is_numeric_dtype(data[ACTUAL_PRICE_COLUMN]):
    raise ValueError(
      "Spike regime analysis requires numeric actual prices."
    )


def build_yearly_regime_rows(
  data: pd.DataFrame,
  split_name: str,
  threshold: float,
) -> list[dict]:
  """Summarize one frozen spike definition by calendar year."""
  validate_regime_data(data)

  analysis_data = data[
    [DATETIME_COLUMN, ACTUAL_PRICE_COLUMN]
  ].copy()

  analysis_data[DATETIME_COLUMN] = pd.to_datetime(
    analysis_data[DATETIME_COLUMN]
  )

  analysis_data["year"] = analysis_data[DATETIME_COLUMN].dt.year

  # One frozen threshold keeps yearly comparisons on the same price scale.
  analysis_data["is_spike"] = classify_spikes(
    prices=analysis_data[ACTUAL_PRICE_COLUMN],
    threshold=threshold,
  )

  rows = []

  for year, yearly_data in analysis_data.groupby("year", sort=True):
    prices = yearly_data[ACTUAL_PRICE_COLUMN]
    row_count = len(yearly_data)
    spike_count = int(yearly_data["is_spike"].sum())

    rows.append(
      {
        "split": split_name,
        "year": int(year),
        "first_timestamp": yearly_data[DATETIME_COLUMN].min(),
        "last_timestamp": yearly_data[DATETIME_COLUMN].max(),
        "threshold_method": "iqr",
        "threshold": threshold,
        "row_count": row_count,
        "spike_count": spike_count,
        "non_spike_count": row_count - spike_count,
        "spike_rate": spike_count / row_count,
        "mean_price": float(prices.mean()),
        "median_price": float(prices.median()),
        "price_std": float(prices.std()),
        "p95_price": float(prices.quantile(0.95)),
        "max_price": float(prices.max()),
      }
    )

  return rows


def build_spike_regime_rows(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
) -> list[dict]:
  """Build train and validation summaries using one train threshold."""
  validate_regime_data(train_data)
  validate_regime_data(validation_data)

  threshold = calculate_iqr_spike_threshold(
    train_data[ACTUAL_PRICE_COLUMN]
  )

  split_data = {
    "train": train_data,
    "validation": validation_data,
  }

  rows = []

  for split_name, data in split_data.items():
    rows.extend(
      build_yearly_regime_rows(
        data=data,
        split_name=split_name,
        threshold=threshold,
      )
    )

  return rows


def write_spike_regime_analysis(
  rows: list[dict],
  output_path: Path = SPIKE_REGIME_ANALYSIS_PATH,
) -> Path:
  """Write the yearly spike-regime analysis report."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  report = pd.DataFrame(
    rows,
    columns=SPIKE_REGIME_ANALYSIS_COLUMNS,
  )

  report.to_csv(output_path, index=False)

  return output_path


def run_spike_regime_analysis(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  output_path: Path = SPIKE_REGIME_ANALYSIS_PATH,
) -> Path:
  """Run the yearly spike-regime analysis."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]

  data = load_training_dataset(training_dataset_path)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=data,
    modeling_config=modeling_config,
)

  rows = build_spike_regime_rows(
    train_data=train_data,
    validation_data=validation_data,
  )

  return write_spike_regime_analysis(
    rows=rows,
    output_path=output_path,
  )


def print_spike_regime_summary(report_path: Path) -> None:
  """Print a readable yearly spike-regime summary."""
  report = pd.read_csv(report_path)
  display_report = report.copy()

  display_report["spike_rate_percent"] = (
    display_report["spike_rate"] * 100
  )

  summary_columns = [
    "split",
    "year",
    "first_timestamp",
    "last_timestamp",
    "row_count",
    "spike_count",
    "spike_rate_percent",
    "mean_price",
    "median_price",
    "price_std",
    "p95_price",
    "max_price",
  ]

  print("Spike regime analysis")
  print("=====================")
  print(
    display_report[summary_columns].to_string(
      index=False,
      float_format=lambda value: f"{value:.4f}",
    )
  )
  print("")
  print(f"Report written to: {report_path}")


if __name__ == "__main__":
  written_path = run_spike_regime_analysis()
  print_spike_regime_summary(written_path)
