from pathlib import Path

import pandas as pd
from sklearn.linear_model import Ridge

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
)
from electricity_predictor.features.feature_columns import MODEL_FEATURE_COLUMNS
from electricity_predictor.modeling.split import split_time_series_data_from_config
from electricity_predictor.contracts.columns import (
  TARGET_COLUMN,
)


RIDGE_ALPHA = 1.0


def train_ridge_regression_model(
  train_data: pd.DataFrame,
  alpha: float = RIDGE_ALPHA,
  target_column: str = TARGET_COLUMN,
) -> Ridge:
  """Train a Ridge Regression model for one regression target column."""
  # Use the same model inputs as Linear Regression for a fair comparison.
  features = train_data[MODEL_FEATURE_COLUMNS]
  # The target column controls which future horizon this model learns to predict.
  target = train_data[target_column]

  # Ridge learns linear weights but penalizes coefficients that become too large.
  model = Ridge(alpha=alpha)
  model.fit(features, target)

  return model


def evaluate_ridge_regression_model(
  model: Ridge,
  evaluation_data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate a trained Ridge Regression model against one target column."""
  features = evaluation_data[MODEL_FEATURE_COLUMNS]
  # The target column is the true future price for the selected horizon.
  target = evaluation_data[target_column]

  # Keep predictions aligned with validation rows before scoring.
  predictions = pd.Series(model.predict(features), index=evaluation_data.index)

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def build_ridge_regression_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  alpha: float = RIDGE_ALPHA,
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for Ridge Regression."""
  # Store alpha because it controls the strength of Ridge regularization.
  return build_model_result_row(
    model_name="ridge_regression",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=f"alpha={alpha}",
    notes="Ridge Regression trained on the chronological train set.",
  )


def print_ridge_regression_summary(
  scores: dict[str, float],
  row_count: int,
  split: str,
  results_path: Path,
  alpha: float = RIDGE_ALPHA,
) -> None:
  """Print a readable summary of Ridge Regression performance."""
  print("Ridge Regression")
  print("================")
  print(f"Alpha: {alpha}")
  print(f"Evaluation split: {split}")
  print(f"Evaluation rows: {row_count:,}")
  print(f"MAE: {scores['mae']:.2f}")
  print(f"RMSE: {scores['rmse']:.2f}")
  print(f"Results written to: {results_path}")


def main() -> None:
  """Run the standalone Ridge Regression research workflow."""
  configuration = load_configuration()

  results_path = REGRESSION_VALIDATION_RESULTS_PATH
  modeling_config = configuration["modeling"]

  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  ridge_regression_model = train_ridge_regression_model(
    train_data=train_data,
    alpha=RIDGE_ALPHA,
  )
  validation_scores = evaluate_ridge_regression_model(
    model=ridge_regression_model,
    evaluation_data=validation_data,
  )

  ridge_regression_result = build_ridge_regression_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    alpha=RIDGE_ALPHA,
  )

  written_results_path = append_model_result(
    result=ridge_regression_result,
    output_path=results_path,
  )

  print_ridge_regression_summary(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    results_path=written_results_path,
    alpha=RIDGE_ALPHA,
  )


if __name__ == "__main__":
  main()
