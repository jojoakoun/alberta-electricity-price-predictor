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
from electricity_predictor.modeling.regression.ridge.ridge_regression import (
  evaluate_ridge_regression_model,
  train_ridge_regression_model,
)
from electricity_predictor.modeling.split import split_time_series_data


RIDGE_ALPHAS = [0.1, 1.0, 10.0, 100.0]
RIDGE_TUNING_SPLITS = 3
TARGET_COLUMN = "actual_price"


def evaluate_ridge_alpha_with_time_series_cv(
  train_data: pd.DataFrame,
  alpha: float,
  n_splits: int = RIDGE_TUNING_SPLITS,
) -> dict[str, float]:
  """Evaluate one Ridge alpha using chronological cross-validation."""
  # TimeSeriesSplit keeps Ridge tuning honest for time-series data.
  time_series_split = TimeSeriesSplit(n_splits=n_splits)

  fold_mae_scores = []
  fold_rmse_scores = []

  for fold_number, (train_index, validation_index) in enumerate(
    time_series_split.split(train_data),
    start=1,
  ):
    # Each fold trains on older rows and validates on newer rows.
    fold_train_data = train_data.iloc[train_index]
    fold_validation_data = train_data.iloc[validation_index]

    print(f"  Fold {fold_number}: alpha={alpha}")

    model = train_ridge_regression_model(
      train_data=fold_train_data,
      alpha=alpha,
    )

    fold_features = fold_validation_data[REGRESSION_FEATURE_COLUMNS]
    fold_target = fold_validation_data[TARGET_COLUMN]
    # Align predictions with the fold validation rows before calculating metrics.
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


def tune_ridge_alpha(train_data: pd.DataFrame) -> dict:
  """Find the Ridge alpha with the lowest time-series CV MAE."""
  tuning_results = []

  for alpha in RIDGE_ALPHAS:
    print(f"Testing Ridge alpha={alpha} with TimeSeriesSplit")
    scores = evaluate_ridge_alpha_with_time_series_cv(
      train_data=train_data,
      alpha=alpha,
    )

    tuning_results.append(
      {
        "alpha": alpha,
        "cv_mae": scores["cv_mae"],
        "cv_rmse": scores["cv_rmse"],
      }
    )

  # Lower MAE is better, so the first sorted result is the selected alpha.
  # Lower CV MAE is better, so the first sorted result is the selected alpha.
  return sorted(tuning_results, key=lambda result: result["cv_mae"])[0]


def build_tuned_ridge_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  best_alpha: float,
  cv_mae: float,
  cv_rmse: float,
) -> dict:
  """Build the model result row for tuned Ridge Regression."""
  return build_model_result_row(
    model_name="ridge_regression_tuned",
    task="regression",
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"best_alpha={best_alpha}; "
      f"cv_splits={RIDGE_TUNING_SPLITS}; "
      f"cv_mae={cv_mae:.6f}; "
      f"cv_rmse={cv_rmse:.6f}"
    ),
    notes="Ridge alpha selected with TimeSeriesSplit on the chronological train set.",
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

  best_result = tune_ridge_alpha(train_data)
  best_alpha = best_result["alpha"]

  # After tuning, retrain once on the full train split with the selected alpha.
  tuned_model = train_ridge_regression_model(
    train_data=train_data,
    alpha=best_alpha,
  )
  validation_scores = evaluate_ridge_regression_model(
    model=tuned_model,
    evaluation_data=validation_data,
  )

  tuned_result = build_tuned_ridge_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    best_alpha=best_alpha,
    cv_mae=best_result["cv_mae"],
    cv_rmse=best_result["cv_rmse"],
  )

  written_results_path = append_model_result(
    result=tuned_result,
    output_path=results_path,
  )

  print("Tuned Ridge Regression")
  print("======================")
  print(f"Best alpha: {best_alpha}")
  print(f"CV MAE: {best_result['cv_mae']:.2f}")
  print(f"CV RMSE: {best_result['cv_rmse']:.2f}")
  print(f"Validation rows: {len(validation_data):,}")
  print(f"Validation MAE: {validation_scores['mae']:.2f}")
  print(f"Validation RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")
