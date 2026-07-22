from itertools import product
from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.split import get_time_series_cv_gap_hours
from electricity_predictor.modeling.classification.random_forest.random_forest_classifier import (
  evaluate_random_forest_classifier,
  train_random_forest_classifier,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_splits,
)
from electricity_predictor.modeling.metrics import calculate_classification_metrics
from electricity_predictor.modeling.model_results import (
  CLASSIFICATION_VALIDATION_RESULTS_PATH,
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


RANDOM_FOREST_N_ESTIMATORS = [100, 200]
RANDOM_FOREST_MAX_DEPTHS = [5, 10, None]
RANDOM_FOREST_MIN_SAMPLES_LEAF = [1, 5]
RANDOM_FOREST_TUNING_SPLITS = 3
TIME_SERIES_CV_GAP_HOURS = get_time_series_cv_gap_hours(
  load_configuration()["modeling"]
)


def evaluate_random_forest_parameters_with_time_series_cv(
  train_data: pd.DataFrame,
  target_column: str,
  n_estimators: int,
  max_depth: int | None,
  min_samples_leaf: int,
  n_splits: int = RANDOM_FOREST_TUNING_SPLITS,
) -> dict[str, float]:
  """Evaluate one Random Forest parameter set with chronological CV."""
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

    print(
      f"  Fold {fold_number}: "
      f"n_estimators={n_estimators}, "
      f"max_depth={max_depth}, "
      f"min_samples_leaf={min_samples_leaf}"
    )

    model = train_random_forest_classifier(
      train_data=fold_train_data,
      target_column=target_column,
      n_estimators=n_estimators,
      max_depth=max_depth,
      min_samples_leaf=min_samples_leaf,
    )

    fold_features = fold_validation_data[MODEL_FEATURE_COLUMNS]
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


def tune_random_forest(
  train_data: pd.DataFrame,
  target_column: str,
) -> dict:
  """Select the Random Forest parameters with the highest CV F1."""
  tuning_results = []

  parameter_combinations = product(
    RANDOM_FOREST_N_ESTIMATORS,
    RANDOM_FOREST_MAX_DEPTHS,
    RANDOM_FOREST_MIN_SAMPLES_LEAF,
  )

  for n_estimators, max_depth, min_samples_leaf in parameter_combinations:
    print(
      "Testing Random Forest: "
      f"n_estimators={n_estimators}, "
      f"max_depth={max_depth}, "
      f"min_samples_leaf={min_samples_leaf}"
    )

    scores = evaluate_random_forest_parameters_with_time_series_cv(
      train_data=train_data,
      target_column=target_column,
      n_estimators=n_estimators,
      max_depth=max_depth,
      min_samples_leaf=min_samples_leaf,
    )

    tuning_results.append(
      {
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "min_samples_leaf": min_samples_leaf,
        **scores,
      }
    )

  return sorted(
    tuning_results,
    key=lambda result: result["cv_f1"],
    reverse=True,
  )[0]


def build_tuned_random_forest_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  best_parameters: dict,
  split: str = "validation",
) -> dict:
  """Build one result row for tuned Random Forest classification."""
  return build_model_result_row(
    model_name="random_forest_classifier_tuned",
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"n_estimators={best_parameters['n_estimators']}; "
      f"max_depth={best_parameters['max_depth']}; "
      f"min_samples_leaf={best_parameters['min_samples_leaf']}; "
      f"cv_splits={RANDOM_FOREST_TUNING_SPLITS}; "
      f"cv_accuracy={best_parameters['cv_accuracy']:.6f}; "
      f"cv_precision={best_parameters['cv_precision']:.6f}; "
      f"cv_recall={best_parameters['cv_recall']:.6f}; "
      f"cv_f1={best_parameters['cv_f1']:.6f}; "
      "class_weight=balanced; random_state=42; n_jobs=-1"
    ),
    notes=(
      "Random Forest parameters selected by highest TimeSeriesSplit F1 "
      "on the chronological train split."
    ),
  )


def run_tuned_random_forest(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Tune and evaluate Random Forest for every forecast horizon."""
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
    print(f"Tuning Random Forest: {horizon_hours}h")
    print("=" * 38)

    best_parameters = tune_random_forest(
      train_data=prepared_train,
      target_column=target_column,
    )

    tuned_model = train_random_forest_classifier(
      train_data=prepared_train,
      target_column=target_column,
      n_estimators=best_parameters["n_estimators"],
      max_depth=best_parameters["max_depth"],
      min_samples_leaf=best_parameters["min_samples_leaf"],
    )

    validation_scores = evaluate_random_forest_classifier(
      model=tuned_model,
      evaluation_data=prepared_validation,
      target_column=target_column,
    )

    result = build_tuned_random_forest_result(
      scores=validation_scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
      best_parameters=best_parameters,
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print(f"Best n_estimators: {best_parameters['n_estimators']}")
    print(f"Best max_depth: {best_parameters['max_depth']}")
    print(f"Best min_samples_leaf: {best_parameters['min_samples_leaf']}")
    print(f"Spike threshold: {threshold:.4f}")
    print(f"CV F1: {best_parameters['cv_f1']:.4f}")
    print(f"Validation accuracy: {validation_scores['accuracy']:.4f}")
    print(f"Validation precision: {validation_scores['precision']:.4f}")
    print(f"Validation recall: {validation_scores['recall']:.4f}")
    print(f"Validation F1: {validation_scores['f1']:.4f}")

  return results_path


if __name__ == "__main__":
  written_path = run_tuned_random_forest()

  print("")
  print(f"Results written to: {written_path}")
