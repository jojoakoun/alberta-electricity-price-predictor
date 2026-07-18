from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.split import get_time_series_cv_gap_hours
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.model_results import (
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.split import load_training_dataset
from electricity_predictor.features.feature_columns import MODEL_FEATURE_COLUMNS
from electricity_predictor.modeling.regression.lasso.lasso_regression import (
  LASSO_MAX_ITER,
  evaluate_lasso_regression_model,
  train_lasso_regression_model,
)
from electricity_predictor.modeling.split import split_time_series_data_from_config


LASSO_ALPHAS = [0.001, 0.01, 0.1, 1.0, 10.0]
LASSO_TUNING_SPLITS = 3
TIME_SERIES_CV_GAP_HOURS = get_time_series_cv_gap_hours(
  load_configuration()["modeling"]
)
TARGET_COLUMN = "actual_price"


def evaluate_lasso_alpha_with_time_series_cv(
  train_data: pd.DataFrame,
  alpha: float,
  n_splits: int = LASSO_TUNING_SPLITS,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate one Lasso alpha using chronological cross-validation."""
  # TimeSeriesSplit keeps each validation fold newer than its training fold.
  time_series_split = TimeSeriesSplit(
    n_splits=n_splits,
    gap=TIME_SERIES_CV_GAP_HOURS,
  )

  fold_mae_scores = []
  fold_rmse_scores = []

  for fold_number, (train_index, validation_index) in enumerate(
    time_series_split.split(train_data),
    start=1,
  ):
    # Each fold trains on older rows and validates on the next chronological block.
    fold_train_data = train_data.iloc[train_index]
    fold_validation_data = train_data.iloc[validation_index]

    print(f"  Fold {fold_number}: alpha={alpha}")

    model = train_lasso_regression_model(
      train_data=fold_train_data,
      alpha=alpha,
      target_column=target_column,
    )

    fold_features = fold_validation_data[MODEL_FEATURE_COLUMNS]
    fold_target = fold_validation_data[target_column]
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


def tune_lasso_alpha(train_data: pd.DataFrame, target_column: str = TARGET_COLUMN) -> dict:
  """Find the Lasso alpha with the lowest time-series CV MAE."""
  tuning_results = []

  for alpha in LASSO_ALPHAS:
    print(f"Testing Lasso alpha={alpha} with TimeSeriesSplit")
    scores = evaluate_lasso_alpha_with_time_series_cv(
      train_data=train_data,
      alpha=alpha,
      target_column=target_column,
    )

    tuning_results.append(
      {
        "alpha": alpha,
        "cv_mae": scores["cv_mae"],
        "cv_rmse": scores["cv_rmse"],
      }
    )

  # Lower CV MAE is better, so the first sorted result is the selected alpha.
  return sorted(tuning_results, key=lambda result: result["cv_mae"])[0]


def build_tuned_lasso_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  best_alpha: float,
  cv_mae: float,
  cv_rmse: float,
  horizon_hours: int | None = None,
) -> dict:
  """Build the model result row for tuned Lasso Regression."""
  return build_model_result_row(
    model_name="lasso_regression_tuned",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"best_alpha={best_alpha}; "
      f"max_iter={LASSO_MAX_ITER}; "
      f"cv_splits={LASSO_TUNING_SPLITS}; "
      f"cv_mae={cv_mae:.6f}; "
      f"cv_rmse={cv_rmse:.6f}"
    ),
    notes="Lasso alpha selected with TimeSeriesSplit on the chronological train set.",
  )


if __name__ == "__main__":
  configuration = load_configuration()

  results_path = Path("reports/model_results.csv")
  modeling_config = configuration["modeling"]

  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  best_result = tune_lasso_alpha(train_data)
  best_alpha = best_result["alpha"]

  # After tuning, retrain once on the full train split with the selected alpha.
  tuned_model = train_lasso_regression_model(
    train_data=train_data,
    alpha=best_alpha,
  )
  validation_scores = evaluate_lasso_regression_model(
    model=tuned_model,
    evaluation_data=validation_data,
  )

  tuned_result = build_tuned_lasso_result(
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

  print("Tuned Lasso Regression")
  print("======================")
  print(f"Best alpha: {best_alpha}")
  print(f"CV MAE: {best_result['cv_mae']:.2f}")
  print(f"CV RMSE: {best_result['cv_rmse']:.2f}")
  print(f"Validation rows: {len(validation_data):,}")
  print(f"Validation MAE: {validation_scores['mae']:.2f}")
  print(f"Validation RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")
