from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestRegressor

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
RANDOM_FOREST_N_ESTIMATORS = 100
RANDOM_FOREST_MAX_DEPTH = None
RANDOM_FOREST_MIN_SAMPLES_LEAF = 1
RANDOM_FOREST_RANDOM_STATE = 42


def train_random_forest_model(
  train_data: pd.DataFrame,
  n_estimators: int = RANDOM_FOREST_N_ESTIMATORS,
  max_depth: int | None = RANDOM_FOREST_MAX_DEPTH,
  min_samples_leaf: int = RANDOM_FOREST_MIN_SAMPLES_LEAF,
  random_state: int = RANDOM_FOREST_RANDOM_STATE,
  target_column: str = TARGET_COLUMN,
) -> RandomForestRegressor:
  """Train a Random Forest Regressor for one regression target column."""
  # Use the same input columns as the linear models for fair model comparison.
  features = train_data[REGRESSION_FEATURE_COLUMNS]
  # The target column controls which future horizon this model learns to predict.
  target = train_data[target_column]

  # Random Forest averages many decision trees to capture non-linear price patterns.
  model = RandomForestRegressor(
    n_estimators=n_estimators,
    max_depth=max_depth,
    min_samples_leaf=min_samples_leaf,
    random_state=random_state,
  )
  model.fit(features, target)

  return model


def evaluate_random_forest_model(
  model: RandomForestRegressor,
  evaluation_data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate a trained Random Forest Regressor against one target column."""
  features = evaluation_data[REGRESSION_FEATURE_COLUMNS]
  # The target column is the true future price for the selected horizon.
  target = evaluation_data[target_column]

  # Keep predictions aligned with validation rows before scoring.
  predictions = pd.Series(model.predict(features), index=evaluation_data.index)

  return {
    "mae": mean_absolute_error_value(target, predictions),
    "rmse": root_mean_squared_error_value(target, predictions),
  }


def build_random_forest_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  n_estimators: int = RANDOM_FOREST_N_ESTIMATORS,
  max_depth: int | None = RANDOM_FOREST_MAX_DEPTH,
  min_samples_leaf: int = RANDOM_FOREST_MIN_SAMPLES_LEAF,
  random_state: int = RANDOM_FOREST_RANDOM_STATE,
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for Random Forest."""
  # Store tree parameters so different Random Forest runs can be compared.
  return build_model_result_row(
    model_name="random_forest_regressor",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"n_estimators={n_estimators}; "
      f"max_depth={max_depth}; "
      f"min_samples_leaf={min_samples_leaf}; "
      f"random_state={random_state}"
    ),
    notes="Random Forest Regressor trained on the chronological train set.",
  )


def print_random_forest_summary(
  scores: dict[str, float],
  row_count: int,
  split: str,
  results_path: Path,
  n_estimators: int = RANDOM_FOREST_N_ESTIMATORS,
  max_depth: int | None = RANDOM_FOREST_MAX_DEPTH,
  min_samples_leaf: int = RANDOM_FOREST_MIN_SAMPLES_LEAF,
  random_state: int = RANDOM_FOREST_RANDOM_STATE,
) -> None:
  """Print a readable summary of Random Forest performance."""
  print("Random Forest Regressor")
  print("=======================")
  print(f"N estimators: {n_estimators}")
  print(f"Max depth: {max_depth}")
  print(f"Min samples leaf: {min_samples_leaf}")
  print(f"Random state: {random_state}")
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

  random_forest_model = train_random_forest_model(
    train_data=train_data,
    n_estimators=RANDOM_FOREST_N_ESTIMATORS,
    max_depth=RANDOM_FOREST_MAX_DEPTH,
    min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
    random_state=RANDOM_FOREST_RANDOM_STATE,
  )
  validation_scores = evaluate_random_forest_model(
    model=random_forest_model,
    evaluation_data=validation_data,
  )

  random_forest_result = build_random_forest_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    n_estimators=RANDOM_FOREST_N_ESTIMATORS,
    max_depth=RANDOM_FOREST_MAX_DEPTH,
    min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
    random_state=RANDOM_FOREST_RANDOM_STATE,
  )

  written_results_path = append_model_result(
    result=random_forest_result,
    output_path=results_path,
  )

  print_random_forest_summary(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    results_path=written_results_path,
    n_estimators=RANDOM_FOREST_N_ESTIMATORS,
    max_depth=RANDOM_FOREST_MAX_DEPTH,
    min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
    random_state=RANDOM_FOREST_RANDOM_STATE,
  )
