from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

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
from electricity_predictor.modeling.regression.random_forest.random_forest import (
  RANDOM_FOREST_RANDOM_STATE,
  evaluate_random_forest_model,
  train_random_forest_model,
)
from electricity_predictor.modeling.split import split_time_series_data


RANDOM_FOREST_TUNING_SPLITS = 3
TARGET_COLUMN = "actual_price"

RANDOM_FOREST_CONFIGS = [
  {"n_estimators": 100, "max_depth": None, "min_samples_leaf": 1},
  {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 1},
  {"n_estimators": 100, "max_depth": 20, "min_samples_leaf": 1},
  {"n_estimators": 100, "max_depth": 20, "min_samples_leaf": 5},
  {"n_estimators": 200, "max_depth": 20, "min_samples_leaf": 5},
]


def format_random_forest_parameters(config: dict, random_state: int) -> str:
  """Create a readable parameter string for model comparison."""
  return (
    f"n_estimators={config['n_estimators']}; "
    f"max_depth={config['max_depth']}; "
    f"min_samples_leaf={config['min_samples_leaf']}; "
    f"random_state={random_state}"
  )


def evaluate_random_forest_config_with_time_series_cv(
  train_data: pd.DataFrame,
  config: dict,
  n_splits: int = RANDOM_FOREST_TUNING_SPLITS,
) -> dict[str, float]:
  """Evaluate one Random Forest configuration using chronological cross-validation."""
  # TimeSeriesSplit evaluates tree settings without mixing future rows into training.
  time_series_split = TimeSeriesSplit(n_splits=n_splits)

  fold_mae_scores = []
  fold_rmse_scores = []

  for fold_number, (train_index, validation_index) in enumerate(
    time_series_split.split(train_data),
    start=1,
  ):
    # Each fold simulates training on the past and validating on the next time block.
    fold_train_data = train_data.iloc[train_index]
    fold_validation_data = train_data.iloc[validation_index]

    print(
      f"  Fold {fold_number}: "
      f"{format_random_forest_parameters(config, RANDOM_FOREST_RANDOM_STATE)}"
    )

    model = train_random_forest_model(
      train_data=fold_train_data,
      n_estimators=config["n_estimators"],
      max_depth=config["max_depth"],
      min_samples_leaf=config["min_samples_leaf"],
      random_state=RANDOM_FOREST_RANDOM_STATE,
    )

    fold_features = fold_validation_data[REGRESSION_FEATURE_COLUMNS]
    fold_target = fold_validation_data[TARGET_COLUMN]
    # Align predictions with the fold validation rows before calculating errors.
    fold_predictions = pd.Series(
      model.predict(fold_features),
      index=fold_validation_data.index,
    )

    fold_mae_scores.append(mean_absolute_error_value(fold_target, fold_predictions))
    fold_rmse_scores.append(root_mean_squared_error_value(fold_target, fold_predictions))

  return {
    "cv_mae": sum(fold_mae_scores) / len(fold_mae_scores),
    "cv_rmse": sum(fold_rmse_scores) / len(fold_rmse_scores),
  }


def tune_random_forest_config(train_data: pd.DataFrame) -> dict:
  """Find the Random Forest configuration with the lowest time-series CV MAE."""
  tuning_results = []

  for config in RANDOM_FOREST_CONFIGS:
    print(
      "Testing Random Forest "
      f"{format_random_forest_parameters(config, RANDOM_FOREST_RANDOM_STATE)} "
      "with TimeSeriesSplit"
    )
    scores = evaluate_random_forest_config_with_time_series_cv(
      train_data=train_data,
      config=config,
    )

    tuning_results.append(
      {
        "config": config,
        "cv_mae": scores["cv_mae"],
        "cv_rmse": scores["cv_rmse"],
      }
    )

  # Lower MAE is better, so the first sorted result is the selected configuration.
  # Lower CV MAE is better, so the first sorted result is the selected configuration.
  return sorted(tuning_results, key=lambda result: result["cv_mae"])[0]


def build_tuned_random_forest_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  best_config: dict,
  cv_mae: float,
  cv_rmse: float,
) -> dict:
  """Build the model result row for tuned Random Forest."""
  return build_model_result_row(
    model_name="random_forest_regressor_tuned",
    task="regression",
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"{format_random_forest_parameters(best_config, RANDOM_FOREST_RANDOM_STATE)}; "
      f"cv_splits={RANDOM_FOREST_TUNING_SPLITS}; "
      f"cv_mae={cv_mae:.6f}; "
      f"cv_rmse={cv_rmse:.6f}"
    ),
    notes="Random Forest parameters selected with TimeSeriesSplit on the chronological train set.",
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

  best_result = tune_random_forest_config(train_data)
  best_config = best_result["config"]

  # After tuning, retrain once on the full train split with the best tree settings.
  tuned_model = train_random_forest_model(
    train_data=train_data,
    n_estimators=best_config["n_estimators"],
    max_depth=best_config["max_depth"],
    min_samples_leaf=best_config["min_samples_leaf"],
    random_state=RANDOM_FOREST_RANDOM_STATE,
  )
  validation_scores = evaluate_random_forest_model(
    model=tuned_model,
    evaluation_data=validation_data,
  )

  tuned_result = build_tuned_random_forest_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    best_config=best_config,
    cv_mae=best_result["cv_mae"],
    cv_rmse=best_result["cv_rmse"],
  )

  written_results_path = append_model_result(
    result=tuned_result,
    output_path=results_path,
  )

  print("Tuned Random Forest Regressor")
  print("============================")
  print(f"Best parameters: {format_random_forest_parameters(best_config, RANDOM_FOREST_RANDOM_STATE)}")
  print(f"CV MAE: {best_result['cv_mae']:.2f}")
  print(f"CV RMSE: {best_result['cv_rmse']:.2f}")
  print(f"Validation rows: {len(validation_data):,}")
  print(f"Validation MAE: {validation_scores['mae']:.2f}")
  print(f"Validation RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")
