from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.model_results import (
  REGRESSION_VALIDATION_RESULTS_PATH,
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


TARGET_COLUMN = "actual_price"
NAIVE_BASELINE_PREDICTION_COLUMN = "actual_price_lag_1h"


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
  split: str = "validation",
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for the naive regression baseline."""
  # The split is explicit so baseline comparisons can use validation,
  # while final protected evaluation can still use test later.
  return build_model_result_row(
    model_name="naive_baseline",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=f"prediction_column={NAIVE_BASELINE_PREDICTION_COLUMN}",
    notes=f"Previous hour price baseline evaluated on the chronological {split} split.",
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

  results_path = REGRESSION_VALIDATION_RESULTS_PATH
  modeling_config = configuration["modeling"]

  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  # Use validation for baseline comparison during model selection.
  # The protected test split is reserved for final evaluation only.
  baseline_scores = evaluate_naive_baseline(validation_data)

  baseline_result = build_naive_baseline_result(
    scores=baseline_scores,
    row_count=len(validation_data),
    split="validation",
  )

  written_results_path = append_model_result(
    result=baseline_result,
    output_path=results_path,
  )

  print_baseline_summary(
    scores=baseline_scores,
    row_count=len(validation_data),
    results_path=written_results_path,
  )
