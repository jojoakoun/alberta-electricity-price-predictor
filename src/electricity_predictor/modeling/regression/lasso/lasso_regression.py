from pathlib import Path

import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.exceptions import ConvergenceWarning
import warnings

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.model_results import (
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.split import load_training_dataset
from electricity_predictor.modeling.regression.feature_columns import REGRESSION_FEATURE_COLUMNS
from electricity_predictor.modeling.split import split_time_series_data


TARGET_COLUMN = "actual_price"
LASSO_ALPHA = 1.0
LASSO_MAX_ITER = 10000


def train_lasso_regression_model(
  train_data: pd.DataFrame,
  alpha: float = LASSO_ALPHA,
  max_iter: int = LASSO_MAX_ITER,
  target_column: str = TARGET_COLUMN,
) -> Lasso:
  """Train a Lasso Regression model for one regression target column."""
  # Use the same regression feature set as the other models so comparisons stay fair.
  features = train_data[REGRESSION_FEATURE_COLUMNS]
  # The target column controls which future horizon this model learns to predict.
  target = train_data[target_column]

  # Lasso can shrink weak feature coefficients all the way to zero.
  model = Lasso(alpha=alpha, max_iter=max_iter)

  with warnings.catch_warnings():
    warnings.simplefilter("ignore", ConvergenceWarning)
    model.fit(features, target)

  return model


def evaluate_lasso_regression_model(
  model: Lasso,
  evaluation_data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate a trained Lasso Regression model against one target column."""
  features = evaluation_data[REGRESSION_FEATURE_COLUMNS]
  # The target column is the true future price for the selected horizon.
  target = evaluation_data[target_column]

  # Keep the original index so predictions stay aligned with the validation rows.
  predictions = pd.Series(model.predict(features), index=evaluation_data.index)

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def build_lasso_regression_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  alpha: float = LASSO_ALPHA,
  max_iter: int = LASSO_MAX_ITER,
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for Lasso Regression."""
  # Store model parameters so the result can be reproduced later.
  return build_model_result_row(
    model_name="lasso_regression",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=f"alpha={alpha}; max_iter={max_iter}",
    notes="Lasso Regression trained on the chronological train set.",
  )


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

  lasso_model = train_lasso_regression_model(train_data)
  validation_scores = evaluate_lasso_regression_model(
    model=lasso_model,
    evaluation_data=validation_data,
  )

  lasso_result = build_lasso_regression_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
  )

  written_results_path = append_model_result(
    result=lasso_result,
    output_path=results_path,
  )

  print("Lasso Regression")
  print("================")
  print(f"Alpha: {LASSO_ALPHA}")
  print(f"Max iterations: {LASSO_MAX_ITER}")
  print(f"Evaluation split: validation")
  print(f"Evaluation rows: {len(validation_data):,}")
  print(f"MAE: {validation_scores['mae']:.2f}")
  print(f"RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")
