import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

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
from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting import (
  HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  HIST_GRADIENT_BOOSTING_LOSS,
  HIST_GRADIENT_BOOSTING_RANDOM_STATE,
  evaluate_hist_gradient_boosting_model,
  train_hist_gradient_boosting_model,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  get_time_series_cv_gap_hours,
  load_training_dataset,
  split_time_series_data_from_config,
)


HIST_GRADIENT_BOOSTING_TUNING_SPLITS = 3
TIME_SERIES_CV_GAP_HOURS = get_time_series_cv_gap_hours(
  load_configuration()["modeling"]
)
TARGET_COLUMN = "actual_price"

# This curated grid changes one or two complexity controls at a time so that
# the tuning result remains understandable and reasonably fast to reproduce.
HIST_GRADIENT_BOOSTING_CONFIGS = [
  {
    "learning_rate": 0.05,
    "max_iter": 200,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 20,
    "l2_regularization": 0.0,
  },
  {
    "learning_rate": 0.05,
    "max_iter": 200,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 0.0,
  },
  {
    "learning_rate": 0.05,
    "max_iter": 200,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 50,
    "l2_regularization": 0.0,
  },
  {
    "learning_rate": 0.1,
    "max_iter": 100,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
  },
  {
    "learning_rate": 0.1,
    "max_iter": 200,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 50,
    "l2_regularization": 1.0,
  },
]


def format_hist_gradient_boosting_tuning_parameters(config: dict) -> str:
  """Create the stable parameter string used in logs and reports."""
  return (
    f"loss={HIST_GRADIENT_BOOSTING_LOSS}; "
    f"learning_rate={config['learning_rate']}; "
    f"max_iter={config['max_iter']}; "
    f"max_leaf_nodes={config['max_leaf_nodes']}; "
    f"min_samples_leaf={config['min_samples_leaf']}; "
    f"l2_regularization={config['l2_regularization']}; "
    f"early_stopping={HIST_GRADIENT_BOOSTING_EARLY_STOPPING}; "
    f"random_state={HIST_GRADIENT_BOOSTING_RANDOM_STATE}"
  )


def evaluate_hist_gradient_boosting_config_with_time_series_cv(
  train_data: pd.DataFrame,
  config: dict,
  n_splits: int = HIST_GRADIENT_BOOSTING_TUNING_SPLITS,
  target_column: str = TARGET_COLUMN,
) -> dict[str, float]:
  """Evaluate one HistGradientBoosting configuration chronologically."""
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
    fold_train_data = train_data.iloc[train_index]
    fold_validation_data = train_data.iloc[validation_index]

    print(
      f"  Fold {fold_number}: "
      f"{format_hist_gradient_boosting_tuning_parameters(config)}"
    )

    model = train_hist_gradient_boosting_model(
      train_data=fold_train_data,
      loss=HIST_GRADIENT_BOOSTING_LOSS,
      learning_rate=config["learning_rate"],
      max_iter=config["max_iter"],
      max_leaf_nodes=config["max_leaf_nodes"],
      min_samples_leaf=config["min_samples_leaf"],
      l2_regularization=config["l2_regularization"],
      early_stopping=HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
      random_state=HIST_GRADIENT_BOOSTING_RANDOM_STATE,
      target_column=target_column,
    )

    fold_features = fold_validation_data[MODEL_FEATURE_COLUMNS]
    fold_target = fold_validation_data[target_column]
    fold_predictions = pd.Series(
      model.predict(fold_features),
      index=fold_validation_data.index,
    )

    fold_mae_scores.append(
      mean_absolute_error_value(fold_target, fold_predictions)
    )
    fold_rmse_scores.append(
      root_mean_squared_error_value(fold_target, fold_predictions)
    )

  return {
    "cv_mae": sum(fold_mae_scores) / len(fold_mae_scores),
    "cv_rmse": sum(fold_rmse_scores) / len(fold_rmse_scores),
  }


def tune_hist_gradient_boosting_config(
  train_data: pd.DataFrame,
  target_column: str = TARGET_COLUMN,
) -> dict:
  """Select the configuration with the lowest chronological CV MAE."""
  tuning_results = []

  for config in HIST_GRADIENT_BOOSTING_CONFIGS:
    print(
      "Testing HistGradientBoosting "
      f"{format_hist_gradient_boosting_tuning_parameters(config)} "
      "with TimeSeriesSplit"
    )
    scores = evaluate_hist_gradient_boosting_config_with_time_series_cv(
      train_data=train_data,
      config=config,
      target_column=target_column,
    )

    tuning_results.append(
      {
        "config": config,
        "cv_mae": scores["cv_mae"],
        "cv_rmse": scores["cv_rmse"],
      }
    )

  return sorted(tuning_results, key=lambda result: result["cv_mae"])[0]


def build_tuned_hist_gradient_boosting_result(
  scores: dict[str, float],
  row_count: int,
  split: str,
  best_config: dict,
  cv_mae: float,
  cv_rmse: float,
  horizon_hours: int | None = None,
) -> dict:
  """Build the validation-report row for the tuned model."""
  return build_model_result_row(
    model_name="hist_gradient_boosting_regressor_tuned",
    task="regression",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"{format_hist_gradient_boosting_tuning_parameters(best_config)}; "
      f"cv_splits={HIST_GRADIENT_BOOSTING_TUNING_SPLITS}; "
      f"cv_mae={cv_mae:.6f}; "
      f"cv_rmse={cv_rmse:.6f}"
    ),
    notes=(
      "HistGradientBoosting parameters selected with TimeSeriesSplit on the "
      "chronological train set; internal early stopping remained disabled."
    ),
  )


def main() -> None:
  """Run the standalone HistGradientBoosting tuning workflow."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
  )

  best_result = tune_hist_gradient_boosting_config(train_data)
  best_config = best_result["config"]

  tuned_model = train_hist_gradient_boosting_model(
    train_data=train_data,
    loss=HIST_GRADIENT_BOOSTING_LOSS,
    learning_rate=best_config["learning_rate"],
    max_iter=best_config["max_iter"],
    max_leaf_nodes=best_config["max_leaf_nodes"],
    min_samples_leaf=best_config["min_samples_leaf"],
    l2_regularization=best_config["l2_regularization"],
    early_stopping=HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
    random_state=HIST_GRADIENT_BOOSTING_RANDOM_STATE,
  )
  validation_scores = evaluate_hist_gradient_boosting_model(
    model=tuned_model,
    evaluation_data=validation_data,
  )

  tuned_result = build_tuned_hist_gradient_boosting_result(
    scores=validation_scores,
    row_count=len(validation_data),
    split="validation",
    best_config=best_config,
    cv_mae=best_result["cv_mae"],
    cv_rmse=best_result["cv_rmse"],
  )

  written_results_path = append_model_result(
    result=tuned_result,
    output_path=REGRESSION_VALIDATION_RESULTS_PATH,
  )

  print("Tuned HistGradientBoosting Regressor")
  print("====================================")
  print(
    "Best parameters: "
    f"{format_hist_gradient_boosting_tuning_parameters(best_config)}"
  )
  print(f"CV MAE: {best_result['cv_mae']:.2f}")
  print(f"CV RMSE: {best_result['cv_rmse']:.2f}")
  print(f"Validation rows: {len(validation_data):,}")
  print(f"Validation MAE: {validation_scores['mae']:.2f}")
  print(f"Validation RMSE: {validation_scores['rmse']:.2f}")
  print(f"Results written to: {written_results_path}")


if __name__ == "__main__":
  main()
