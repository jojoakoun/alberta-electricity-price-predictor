from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.split import get_time_series_cv_gap_hours
from electricity_predictor.modeling.classification.logistic.logistic_regression import (
  evaluate_logistic_regression_model,
  train_logistic_regression_model,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_splits,
)
from electricity_predictor.modeling.metrics import calculate_classification_metrics
from electricity_predictor.modeling.model_results import (
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.regression.feature_columns import (
  REGRESSION_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


LOGISTIC_C_VALUES = [0.01, 0.1, 1.0, 10.0, 100.0]
LOGISTIC_TUNING_SPLITS = 3
TIME_SERIES_CV_GAP_HOURS = get_time_series_cv_gap_hours(
  load_configuration()["modeling"]
)
MODEL_RESULTS_PATH = Path("reports/model_results.csv")


def evaluate_logistic_c_with_time_series_cv(
  train_data: pd.DataFrame,
  c_value: float,
  target_column: str,
  n_splits: int = LOGISTIC_TUNING_SPLITS,
) -> dict[str, float]:
  """Evaluate one Logistic Regression C value with chronological CV."""
  time_series_split = TimeSeriesSplit(
    n_splits=n_splits,
    gap=TIME_SERIES_CV_GAP_HOURS,
  )

  fold_accuracy_scores = []
  fold_precision_scores = []
  fold_recall_scores = []
  fold_f1_scores = []
  fold_pr_auc_scores = []

  for fold_number, (train_index, validation_index) in enumerate(
    time_series_split.split(train_data),
    start=1,
  ):
    fold_train_data = train_data.iloc[train_index]
    fold_validation_data = train_data.iloc[validation_index]

    print(f"  Fold {fold_number}: C={c_value}")

    model = train_logistic_regression_model(
      train_data=fold_train_data,
      target_column=target_column,
      c_value=c_value,
    )

    fold_features = fold_validation_data[REGRESSION_FEATURE_COLUMNS]
    fold_target = fold_validation_data[target_column]
    fold_prediction = model.predict(fold_features)
    fold_probability = model.predict_proba(fold_features)[:, 1]

    scores = calculate_classification_metrics(
      target=fold_target,
      prediction=fold_prediction,
      probability=fold_probability,
    )

    fold_accuracy_scores.append(scores["accuracy"])
    fold_precision_scores.append(scores["precision"])
    fold_recall_scores.append(scores["recall"])
    fold_f1_scores.append(scores["f1"])
    fold_pr_auc_scores.append(scores["pr_auc"])

  return {
    "cv_accuracy": sum(fold_accuracy_scores) / len(fold_accuracy_scores),
    "cv_precision": sum(fold_precision_scores) / len(fold_precision_scores),
    "cv_recall": sum(fold_recall_scores) / len(fold_recall_scores),
    "cv_f1": sum(fold_f1_scores) / len(fold_f1_scores),
    "cv_pr_auc": sum(fold_pr_auc_scores) / len(fold_pr_auc_scores),
  }


def tune_logistic_c(
  train_data: pd.DataFrame,
  target_column: str,
) -> dict:
  """Select the Logistic Regression C value with the highest CV F1."""
  tuning_results = []

  for c_value in LOGISTIC_C_VALUES:
    print(f"Testing Logistic Regression C={c_value}")

    scores = evaluate_logistic_c_with_time_series_cv(
      train_data=train_data,
      c_value=c_value,
      target_column=target_column,
    )

    tuning_results.append(
      {
        "c_value": c_value,
        **scores,
      }
    )

  # Higher F1 is better because spike detection must balance precision and recall.
  return sorted(
    tuning_results,
    key=lambda result: result["cv_f1"],
    reverse=True,
  )[0]


def build_tuned_logistic_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  best_c: float,
  cv_scores: dict[str, float],
  split: str = "validation",
) -> dict:
  """Build one result row for tuned Logistic Regression."""
  return build_model_result_row(
    model_name="logistic_regression_tuned",
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"best_C={best_c}; "
      f"cv_splits={LOGISTIC_TUNING_SPLITS}; "
      f"cv_accuracy={cv_scores['cv_accuracy']:.6f}; "
      f"cv_precision={cv_scores['cv_precision']:.6f}; "
      f"cv_recall={cv_scores['cv_recall']:.6f}; "
      f"cv_f1={cv_scores['cv_f1']:.6f}; "
      "class_weight=balanced; scaler=StandardScaler"
    ),
    notes=(
      "Logistic Regression C selected by highest TimeSeriesSplit F1 "
      "on the chronological train split."
    ),
  )


def run_tuned_logistic_regression(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = MODEL_RESULTS_PATH,
) -> Path:
  """Tune and evaluate Logistic Regression for every forecast horizon."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  training_data = load_training_dataset(training_dataset_path)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  prepared_train, prepared_validation, _, threshold = prepare_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=horizons_hours,
  )

  for horizon_hours in horizons_hours:
    target_column = build_spike_target_column_name(horizon_hours)

    print("")
    print(f"Tuning Logistic Regression: {horizon_hours}h")
    print("=" * 40)

    best_result = tune_logistic_c(
      train_data=prepared_train,
      target_column=target_column,
    )

    best_c = best_result["c_value"]

    tuned_model = train_logistic_regression_model(
      train_data=prepared_train,
      target_column=target_column,
      c_value=best_c,
    )

    validation_scores = evaluate_logistic_regression_model(
      model=tuned_model,
      evaluation_data=prepared_validation,
      target_column=target_column,
    )

    result = build_tuned_logistic_result(
      scores=validation_scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
      best_c=best_c,
      cv_scores=best_result,
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print(f"Best C: {best_c}")
    print(f"Spike threshold: {threshold:.4f}")
    print(f"CV F1: {best_result['cv_f1']:.4f}")
    print(f"Validation accuracy: {validation_scores['accuracy']:.4f}")
    print(f"Validation precision: {validation_scores['precision']:.4f}")
    print(f"Validation recall: {validation_scores['recall']:.4f}")
    print(f"Validation F1: {validation_scores['f1']:.4f}")

  return results_path


if __name__ == "__main__":
  written_path = run_tuned_logistic_regression()

  print("")
  print(f"Results written to: {written_path}")
