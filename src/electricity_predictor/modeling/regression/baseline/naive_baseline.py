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

# Keep every simple regression benchmark in one explicit, ordered contract.
# The historical naive_baseline name stays unchanged for backward compatibility.
REGRESSION_BASELINE_CONFIGS = (
  {
    "model_name": "naive_baseline",
    "prediction_column": "actual_price_lag_1h",
    "description": "Previous observed hour price",
  },
  {
    "model_name": "previous_day_baseline",
    "prediction_column": "actual_price_lag_24h",
    "description": "Price observed 24 hours earlier",
  },
  {
    "model_name": "aeso_forecast_baseline",
    "prediction_column": "forecast_price",
    "description": "Current AESO forecast-price feature",
  },
  {
    "model_name": "previous_aeso_forecast_baseline",
    "prediction_column": "forecast_price_lag_1h",
    "description": "Previous AESO forecast-price feature",
  },
  {
    "model_name": "rolling_24h_mean_baseline",
    "prediction_column": "actual_price_rolling_24h_mean",
    "description": "Trailing 24-hour observed-price mean",
  },
  {
    "model_name": "rolling_7d_mean_baseline",
    "prediction_column": "actual_price_rolling_7d_mean",
    "description": "Trailing seven-day observed-price mean",
  },
)


def evaluate_rule_baseline(
  data: pd.DataFrame,
  prediction_column: str,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate one explicit prediction rule against one selected target."""
  if target_column not in data.columns:
    raise ValueError(f"Missing baseline target column: {target_column}")

  if prediction_column not in data.columns:
    raise ValueError(
      f"Missing baseline prediction column: {prediction_column}"
    )

  target = data[target_column]
  prediction = data[prediction_column]

  return {
    "mae": mean_absolute_error_value(target, prediction),
    "rmse": root_mean_squared_error_value(target, prediction),
  }


def evaluate_naive_baseline(
  data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate the historical previous-hour persistence baseline."""
  return evaluate_rule_baseline(
    data=data,
    prediction_column=NAIVE_BASELINE_PREDICTION_COLUMN,
    target_column=target_column,
  )


def build_rule_baseline_result(
  scores: dict[str, float],
  row_count: int,
  model_name: str,
  prediction_column: str,
  description: str,
  split: str = "validation",
  horizon_hours: int | None = None,
) -> dict:
  """Build one model-result row for an explicit regression rule."""
  return build_model_result_row(
    model_name=model_name,
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=f"prediction_column={prediction_column}",
    notes=(
      f"{description} baseline evaluated on the chronological {split} split."
    ),
  )


def build_naive_baseline_result(
  scores: dict[str, float],
  row_count: int,
  split: str = "validation",
  horizon_hours: int | None = None,
) -> dict:
  """Build the historical naive-baseline result row."""
  return build_rule_baseline_result(
    scores=scores,
    row_count=row_count,
    model_name="naive_baseline",
    prediction_column=NAIVE_BASELINE_PREDICTION_COLUMN,
    description="Previous hour price",
    split=split,
    horizon_hours=horizon_hours,
  )


def print_baseline_summary(
  model_name: str,
  prediction_column: str,
  target_column: str,
  scores: dict[str, float],
  row_count: int,
  results_path: Path,
) -> None:
  """Print a readable summary for one simple regression rule."""
  print(f"Regression baseline: {model_name}")
  print("=" * 40)
  print(f"Prediction column: {prediction_column}")
  print(f"Target column: {target_column}")
  print(f"Evaluation rows: {row_count:,}")
  print(f"MAE: {scores['mae']:.2f}")
  print(f"RMSE: {scores['rmse']:.2f}")
  print(f"Results written to: {results_path}")


if __name__ == "__main__":
  configuration = load_configuration()

  results_path = REGRESSION_VALIDATION_RESULTS_PATH
  modeling_config = configuration["modeling"]

  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  _, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
  )

  # This standalone command preserves the historical previous-hour baseline.
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
    model_name="naive_baseline",
    prediction_column=NAIVE_BASELINE_PREDICTION_COLUMN,
    target_column=TARGET_COLUMN,
    scores=baseline_scores,
    row_count=len(validation_data),
    results_path=written_results_path,
  )
