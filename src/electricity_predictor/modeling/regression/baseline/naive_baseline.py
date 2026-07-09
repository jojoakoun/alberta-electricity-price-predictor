from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.model_results import (
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.split import split_time_series_data


TARGET_COLUMN = "actual_price"
NAIVE_BASELINE_PREDICTION_COLUMN = "actual_price_lag_1h"


def load_training_dataset(file_path: Path) -> pd.DataFrame:
  """Load the model-ready training dataset."""
  if not file_path.exists():
    raise FileNotFoundError(f"Training dataset not found: {file_path}")

  # This file is produced by the training-data step and contains complete model rows.
  return pd.read_csv(file_path)


def evaluate_naive_baseline(
  data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate a naive baseline against one selected target column."""
  # The target column controls which forecast horizon the baseline is evaluated against.
  target = data[target_column]
  prediction = data[NAIVE_BASELINE_PREDICTION_COLUMN]

  # The baseline score becomes the benchmark future models must beat.
  return {
    "mae": mean_absolute_error_value(target, prediction),
    "rmse": root_mean_squared_error_value(target, prediction),
  }


def build_naive_baseline_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for the naive regression baseline."""
  # Save the benchmark result so every learned model can be compared against it.
  return build_model_result_row(
    model_name="naive_baseline",
    task="regression",
    horizon_hours=horizon_hours,
    split="test",
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=f"prediction_column={NAIVE_BASELINE_PREDICTION_COLUMN}",
    notes="Previous hour price baseline evaluated on the chronological test set.",
  )


def print_baseline_summary(scores: dict[str, float], row_count: int, results_path: Path) -> None:
  """Print a readable summary of baseline model performance."""
  print("Naive baseline regression")
  print("=========================")
  print(f"Prediction column: {NAIVE_BASELINE_PREDICTION_COLUMN}")
  print(f"Target column: {TARGET_COLUMN}")
  print(f"Evaluation rows: {row_count:,}")
  print(f"MAE: {scores['mae']:.2f}")
  print(f"RMSE: {scores['rmse']:.2f}")
  print(f"Results written to: {results_path}")


if __name__ == "__main__":
  configuration = load_configuration()

  training_dataset_path = Path("data/processed/training_dataset.csv")
  results_path = Path("reports/model_results.csv")
  modeling_config = configuration["modeling"]

  training_data = load_training_dataset(training_dataset_path)

  train_data, validation_data, test_data = split_time_series_data(
    data=training_data,
    train_ratio=modeling_config["train_ratio"],
    validation_ratio=modeling_config["validation_ratio"],
    test_ratio=modeling_config["test_ratio"],
  )

  # Evaluate on the newest split to estimate future-like baseline performance.
  baseline_scores = evaluate_naive_baseline(test_data)

  baseline_result = build_naive_baseline_result(
    scores=baseline_scores,
    row_count=len(test_data),
  )

  written_results_path = append_model_result(
    result=baseline_result,
    output_path=results_path,
  )

  print_baseline_summary(
    scores=baseline_scores,
    row_count=len(test_data),
    results_path=written_results_path,
  )
