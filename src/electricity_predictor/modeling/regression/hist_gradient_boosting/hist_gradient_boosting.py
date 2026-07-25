from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_columns import MODEL_FEATURE_COLUMNS
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
from electricity_predictor.contracts.columns import (
  TARGET_COLUMN,
)


HIST_GRADIENT_BOOSTING_LOSS = "absolute_error"
HIST_GRADIENT_BOOSTING_LEARNING_RATE = 0.1
HIST_GRADIENT_BOOSTING_MAX_ITER = 100
HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES = 31
HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF = 20
HIST_GRADIENT_BOOSTING_L2_REGULARIZATION = 0.0
HIST_GRADIENT_BOOSTING_EARLY_STOPPING = False
HIST_GRADIENT_BOOSTING_RANDOM_STATE = 42


def train_hist_gradient_boosting_model(
  train_data: pd.DataFrame,
  loss: str = HIST_GRADIENT_BOOSTING_LOSS,
  learning_rate: float = HIST_GRADIENT_BOOSTING_LEARNING_RATE,
  max_iter: int = HIST_GRADIENT_BOOSTING_MAX_ITER,
  max_leaf_nodes: int = HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
  min_samples_leaf: int = HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
  l2_regularization: float = HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
  early_stopping: bool = HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  random_state: int = HIST_GRADIENT_BOOSTING_RANDOM_STATE,
  target_column: str = TARGET_COLUMN,
) -> HistGradientBoostingRegressor:
  """Train one HistGradientBoostingRegressor on chronological training data."""
  features = train_data[MODEL_FEATURE_COLUMNS]
  target = train_data[target_column]

  # External chronological cross-validation controls tuning, so internal
  # validation-based early stopping remains disabled.
  model = HistGradientBoostingRegressor(
    loss=loss,
    learning_rate=learning_rate,
    max_iter=max_iter,
    max_leaf_nodes=max_leaf_nodes,
    min_samples_leaf=min_samples_leaf,
    l2_regularization=l2_regularization,
    early_stopping=early_stopping,
    random_state=random_state,
  )
  model.fit(features, target)

  return model


def evaluate_hist_gradient_boosting_model(
  model: HistGradientBoostingRegressor,
  evaluation_data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate a fitted HistGradientBoostingRegressor on one chronological split."""
  features = evaluation_data[MODEL_FEATURE_COLUMNS]
  target = evaluation_data[target_column]
  predictions = pd.Series(model.predict(features), index=evaluation_data.index)

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def format_hist_gradient_boosting_parameters(
  loss: str = HIST_GRADIENT_BOOSTING_LOSS,
  learning_rate: float = HIST_GRADIENT_BOOSTING_LEARNING_RATE,
  max_iter: int = HIST_GRADIENT_BOOSTING_MAX_ITER,
  max_leaf_nodes: int = HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
  min_samples_leaf: int = HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
  l2_regularization: float = HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
  early_stopping: bool = HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  random_state: int = HIST_GRADIENT_BOOSTING_RANDOM_STATE,
) -> str:
  """Create a stable parameter string for reports and later model recreation."""
  return (
    f"loss={loss}; "
    f"learning_rate={learning_rate}; "
    f"max_iter={max_iter}; "
    f"max_leaf_nodes={max_leaf_nodes}; "
    f"min_samples_leaf={min_samples_leaf}; "
    f"l2_regularization={l2_regularization}; "
    f"early_stopping={early_stopping}; "
    f"random_state={random_state}"
  )


def build_hist_gradient_boosting_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  loss: str = HIST_GRADIENT_BOOSTING_LOSS,
  learning_rate: float = HIST_GRADIENT_BOOSTING_LEARNING_RATE,
  max_iter: int = HIST_GRADIENT_BOOSTING_MAX_ITER,
  max_leaf_nodes: int = HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
  min_samples_leaf: int = HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
  l2_regularization: float = HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
  early_stopping: bool = HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  random_state: int = HIST_GRADIENT_BOOSTING_RANDOM_STATE,
  horizon_hours: int | None = None,
) -> dict:
  """Build one validation-report row for the base HistGradientBoosting model."""
  return build_model_result_row(
    model_name="hist_gradient_boosting_regressor",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=format_hist_gradient_boosting_parameters(
      loss=loss,
      learning_rate=learning_rate,
      max_iter=max_iter,
      max_leaf_nodes=max_leaf_nodes,
      min_samples_leaf=min_samples_leaf,
      l2_regularization=l2_regularization,
      early_stopping=early_stopping,
      random_state=random_state,
    ),
    notes=(
      "HistGradientBoostingRegressor trained on the chronological train set "
      "with internal early stopping disabled."
    ),
  )


def print_hist_gradient_boosting_summary(
  scores: dict[str, float],
  row_count: int,
  split: str,
  results_path: Path,
) -> None:
  """Print a concise standalone research summary."""
  print("HistGradientBoosting Regressor")
  print("==============================")
  print(format_hist_gradient_boosting_parameters())
  print(f"Evaluation split: {split}")
  print(f"Evaluation rows: {row_count:,}")
  print(f"MAE: {scores['mae']:.2f}")
  print(f"RMSE: {scores['rmse']:.2f}")
  print(f"Results written to: {results_path}")


def main() -> None:
  """Run the standalone base HistGradientBoosting research workflow."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
  )

  model = train_hist_gradient_boosting_model(train_data=train_data)
  scores = evaluate_hist_gradient_boosting_model(
    model=model,
    evaluation_data=validation_data,
  )
  result = build_hist_gradient_boosting_result(
    scores=scores,
    row_count=len(validation_data),
    split="validation",
  )
  written_results_path = append_model_result(
    result=result,
    output_path=REGRESSION_VALIDATION_RESULTS_PATH,
  )

  print_hist_gradient_boosting_summary(
    scores=scores,
    row_count=len(validation_data),
    split="validation",
    results_path=written_results_path,
  )


if __name__ == "__main__":
  main()
