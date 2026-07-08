from pathlib import Path

import pandas as pd
from sklearn.linear_model import ElasticNet
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
from electricity_predictor.modeling.regression.baseline.naive_baseline import load_training_dataset
from electricity_predictor.modeling.regression.feature_columns import REGRESSION_FEATURE_COLUMNS
from electricity_predictor.modeling.split import split_time_series_data


TARGET_COLUMN = "actual_price"
ELASTIC_NET_ALPHA = 1.0
ELASTIC_NET_L1_RATIO = 0.5
ELASTIC_NET_MAX_ITER = 10000


def train_elastic_net_regression_model(
  train_data: pd.DataFrame,
  alpha: float = ELASTIC_NET_ALPHA,
  l1_ratio: float = ELASTIC_NET_L1_RATIO,
  max_iter: int = ELASTIC_NET_MAX_ITER,
  target_column: str = TARGET_COLUMN,
) -> ElasticNet:
  """Train an Elastic Net Regression model for one regression target column."""
  # Use the shared regression features so Elastic Net is compared fairly.
  features = train_data[REGRESSION_FEATURE_COLUMNS]
  # The target column controls which future horizon this model learns to predict.
  target = train_data[target_column]

  # Elastic Net mixes Ridge-style shrinkage with Lasso-style feature selection.
  model = ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=max_iter)

  with warnings.catch_warnings():
    warnings.simplefilter("ignore", ConvergenceWarning)
    model.fit(features, target)

  return model


def evaluate_elastic_net_regression_model(
  model: ElasticNet,
  evaluation_data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate a trained Elastic Net Regression model against one target column."""
  features = evaluation_data[REGRESSION_FEATURE_COLUMNS]
  # The target column is the true future price for the selected horizon.
  target = evaluation_data[target_column]

  # Keep prediction indexes aligned with the validation rows.
  predictions = pd.Series(model.predict(features), index=evaluation_data.index)

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def build_elastic_net_regression_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  alpha: float = ELASTIC_NET_ALPHA,
  l1_ratio: float = ELASTIC_NET_L1_RATIO,
  max_iter: int = ELASTIC_NET_MAX_ITER,
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for Elastic Net Regression."""
  # Store alpha and l1_ratio because both control Elastic Net behavior.
  return build_model_result_row(
    model_name="elastic_net_regression",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=f"alpha={alpha}; l1_ratio={l1_ratio}; max_iter={max_iter}",
    notes="Elastic Net Regression trained on the chronological train set.",
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

  elastic_net_model = train_elastic_net_regression_model(train_data)
  validation_scores = evaluate_elastic_net_regression_model(
    model=elastic_net_model,
    evaluation_data=validation_data,
  )

  elastic_net_result = build_elastic_net_regression_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
  )

  written_results_path = append_model_result(
    result=elastic_net_result,
    output_path=results_path,
  )

  print("Elastic Net Regression")
  print("======================")
  print(f"Alpha: {ELASTIC_NET_ALPHA}")
  print(f"L1 ratio: {ELASTIC_NET_L1_RATIO}")
  print(f"Max iterations: {ELASTIC_NET_MAX_ITER}")
  print(f"Evaluation split: validation")
  print(f"Evaluation rows: {len(validation_data):,}")
  print(f"MAE: {validation_scores['mae']:.2f}")
  print(f"RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")
