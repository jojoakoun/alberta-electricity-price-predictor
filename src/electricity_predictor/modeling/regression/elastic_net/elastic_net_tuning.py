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
from electricity_predictor.modeling.regression.elastic_net.elastic_net_regression import (
  ELASTIC_NET_MAX_ITER,
  evaluate_elastic_net_regression_model,
  train_elastic_net_regression_model,
)
from electricity_predictor.modeling.regression.feature_columns import REGRESSION_FEATURE_COLUMNS
from electricity_predictor.modeling.split import split_time_series_data


ELASTIC_NET_CONFIGS = [
  {"alpha": 0.001, "l1_ratio": 0.2},
  {"alpha": 0.001, "l1_ratio": 0.5},
  {"alpha": 0.001, "l1_ratio": 0.8},
  {"alpha": 0.01, "l1_ratio": 0.2},
  {"alpha": 0.01, "l1_ratio": 0.5},
  {"alpha": 0.01, "l1_ratio": 0.8},
  {"alpha": 0.1, "l1_ratio": 0.2},
  {"alpha": 0.1, "l1_ratio": 0.5},
  {"alpha": 0.1, "l1_ratio": 0.8},
  {"alpha": 1.0, "l1_ratio": 0.5},
]
ELASTIC_NET_TUNING_SPLITS = 3
TARGET_COLUMN = "actual_price"


def format_elastic_net_parameters(config: dict) -> str:
  """Create a readable Elastic Net parameter string."""
  return f"alpha={config['alpha']}; l1_ratio={config['l1_ratio']}; max_iter={ELASTIC_NET_MAX_ITER}"


def evaluate_elastic_net_config_with_time_series_cv(
  train_data: pd.DataFrame,
  config: dict,
  n_splits: int = ELASTIC_NET_TUNING_SPLITS,
) -> dict[str, float]:
  """Evaluate one Elastic Net configuration using chronological cross-validation."""
  # TimeSeriesSplit prevents future rows from leaking into older validation folds.
  time_series_split = TimeSeriesSplit(n_splits=n_splits)

  fold_mae_scores = []
  fold_rmse_scores = []

  for fold_number, (train_index, validation_index) in enumerate(
    time_series_split.split(train_data),
    start=1,
  ):
    # Each fold respects time order: older rows train, newer rows validate.
    fold_train_data = train_data.iloc[train_index]
    fold_validation_data = train_data.iloc[validation_index]

    print(f"  Fold {fold_number}: {format_elastic_net_parameters(config)}")

    model = train_elastic_net_regression_model(
      train_data=fold_train_data,
      alpha=config["alpha"],
      l1_ratio=config["l1_ratio"],
    )

    fold_features = fold_validation_data[REGRESSION_FEATURE_COLUMNS]
    fold_target = fold_validation_data[TARGET_COLUMN]
    # Align predictions with fold validation rows before calculating MAE and RMSE.
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


def tune_elastic_net_config(train_data: pd.DataFrame) -> dict:
  """Find the Elastic Net configuration with the lowest time-series CV MAE."""
  tuning_results = []

  for config in ELASTIC_NET_CONFIGS:
    print(f"Testing Elastic Net {format_elastic_net_parameters(config)} with TimeSeriesSplit")
    scores = evaluate_elastic_net_config_with_time_series_cv(
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

  # Lower CV MAE is better, so the first sorted result is the selected configuration.
  return sorted(tuning_results, key=lambda result: result["cv_mae"])[0]


def build_tuned_elastic_net_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  best_config: dict,
  cv_mae: float,
  cv_rmse: float,
) -> dict:
  """Build the model result row for tuned Elastic Net Regression."""
  return build_model_result_row(
    model_name="elastic_net_regression_tuned",
    task="regression",
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"{format_elastic_net_parameters(best_config)}; "
      f"cv_splits={ELASTIC_NET_TUNING_SPLITS}; "
      f"cv_mae={cv_mae:.6f}; "
      f"cv_rmse={cv_rmse:.6f}"
    ),
    notes="Elastic Net parameters selected with TimeSeriesSplit on the chronological train set.",
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

  best_result = tune_elastic_net_config(train_data)
  best_config = best_result["config"]

  # After tuning, retrain once on the full train split with the best parameters.
  tuned_model = train_elastic_net_regression_model(
    train_data=train_data,
    alpha=best_config["alpha"],
    l1_ratio=best_config["l1_ratio"],
  )
  validation_scores = evaluate_elastic_net_regression_model(
    model=tuned_model,
    evaluation_data=validation_data,
  )

  tuned_result = build_tuned_elastic_net_result(
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

  print("Tuned Elastic Net Regression")
  print("============================")
  print(f"Best parameters: {format_elastic_net_parameters(best_config)}")
  print(f"CV MAE: {best_result['cv_mae']:.2f}")
  print(f"CV RMSE: {best_result['cv_rmse']:.2f}")
  print(f"Validation rows: {len(validation_data):,}")
  print(f"Validation MAE: {validation_scores['mae']:.2f}")
  print(f"Validation RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")
