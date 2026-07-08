from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)


TARGET_COLUMN = "actual_price"
NAIVE_BASELINE_PREDICTION_COLUMN = "actual_price_lag_1h"


def load_training_dataset(file_path: Path) -> pd.DataFrame:
  """Load the model-ready training dataset."""
  if not file_path.exists():
    raise FileNotFoundError(f"Training dataset not found: {file_path}")

  return pd.read_csv(file_path)


def evaluate_naive_baseline(data: pd.DataFrame) -> dict[str, float]:
  """Evaluate a naive baseline that predicts price using the previous hour price."""
  target = data[TARGET_COLUMN]
  prediction = data[NAIVE_BASELINE_PREDICTION_COLUMN]

  # The baseline score becomes the benchmark future models must beat.
  return {
    "mae": mean_absolute_error_value(target, prediction),
    "rmse": root_mean_squared_error_value(target, prediction),
  }


def print_baseline_summary(scores: dict[str, float]) -> None:
  """Print a readable summary of baseline model performance."""
  print("Naive baseline regression")
  print("=========================")
  print(f"Prediction column: {NAIVE_BASELINE_PREDICTION_COLUMN}")
  print(f"Target column: {TARGET_COLUMN}")
  print(f"MAE: {scores['mae']:.2f}")
  print(f"RMSE: {scores['rmse']:.2f}")


if __name__ == "__main__":
  training_dataset_path = Path("data/processed/training_dataset.csv")

  training_data = load_training_dataset(training_dataset_path)
  baseline_scores = evaluate_naive_baseline(training_data)

  print_baseline_summary(baseline_scores)
