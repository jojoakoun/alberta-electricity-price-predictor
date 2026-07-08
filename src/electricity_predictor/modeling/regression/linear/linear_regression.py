from pathlib import Path

import pandas as pd
from sklearn.linear_model import LinearRegression

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.model_results import (
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.regression.baseline.naive_baseline import load_training_dataset
from electricity_predictor.modeling.regression.feature_columns import REGRESSION_FEATURE_COLUMNS
from electricity_predictor.modeling.split import split_time_series_data


TARGET_COLUMN = "actual_price"


def train_linear_regression_model(train_data: pd.DataFrame) -> LinearRegression:
  """Train a Linear Regression model using the regression feature columns."""
  # Use the shared regression feature list so model comparisons stay fair.
  features = train_data[REGRESSION_FEATURE_COLUMNS]
  target = train_data[TARGET_COLUMN]

  # Linear Regression learns one weight for each feature to predict actual_price.
  model = LinearRegression()
  model.fit(features, target)

  return model


def evaluate_linear_regression_model(
  model: LinearRegression,
  evaluation_data: pd.DataFrame,
) -> dict[str, float]:
  """Evaluate a trained Linear Regression model."""
  features = evaluation_data[REGRESSION_FEATURE_COLUMNS]
  target = evaluation_data[TARGET_COLUMN]

  # Keep predictions aligned with the evaluation rows before calculating errors.
  predictions = pd.Series(model.predict(features), index=evaluation_data.index)

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def build_linear_regression_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
) -> dict:
  """Build the model result row for Linear Regression."""
  # Store the model setup so the result can be reproduced later.
  return build_model_result_row(
    model_name="linear_regression",
    task="regression",
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters="fit_intercept=True",
    notes="Linear Regression trained on the chronological train set.",
  )


def print_linear_regression_summary(
  scores: dict[str, float],
  row_count: int,
  split: str,
  results_path: Path,
) -> None:
  """Print a readable summary of Linear Regression performance."""
  print("Linear Regression")
  print("=================")
  print(f"Evaluation split: {split}")
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

  linear_regression_model = train_linear_regression_model(train_data)
  validation_scores = evaluate_linear_regression_model(
    model=linear_regression_model,
    evaluation_data=validation_data,
  )

  linear_regression_result = build_linear_regression_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
  )

  written_results_path = append_model_result(
    result=linear_regression_result,
    output_path=results_path,
  )

  print_linear_regression_summary(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    results_path=written_results_path,
  )
