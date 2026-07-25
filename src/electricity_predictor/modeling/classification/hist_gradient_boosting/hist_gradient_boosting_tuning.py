"""Tune HistGradientBoosting classifiers with chronological CV."""

from pathlib import Path

import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.hist_gradient_boosting.hist_gradient_boosting_classifier import (
  train_hist_gradient_boosting_classifier,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_training_splits,
)
from electricity_predictor.modeling.classification.validation_evaluation import (
  add_decision_threshold_to_parameters,
  evaluate_classifier_on_validation,
)
from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
)
from electricity_predictor.modeling.model_results import (
  CLASSIFICATION_VALIDATION_RESULTS_PATH,
  append_model_result,
  build_model_result_row,
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

# A targeted grid tests model size, learning speed, leaf support,
# and regularization without creating a large exhaustive search.
HIST_GRADIENT_BOOSTING_CANDIDATES = [
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
    "learning_rate": 0.10,
    "max_iter": 100,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
  },
  {
    "learning_rate": 0.10,
    "max_iter": 200,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 50,
    "l2_regularization": 1.0,
  },
]


def evaluate_hist_gradient_boosting_parameters_with_time_series_cv(
  train_data: pd.DataFrame,
  target_column: str,
  parameters: dict,
  n_splits: int = HIST_GRADIENT_BOOSTING_TUNING_SPLITS,
) -> dict[str, float]:
  """Evaluate one parameter set with leakage-safe chronological CV."""
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
      f"learning_rate={parameters['learning_rate']}, "
      f"max_iter={parameters['max_iter']}, "
      f"max_leaf_nodes={parameters['max_leaf_nodes']}, "
      f"min_samples_leaf={parameters['min_samples_leaf']}, "
      f"l2_regularization={parameters['l2_regularization']}"
    )

    model = train_hist_gradient_boosting_classifier(
      train_data=fold_train_data,
      target_column=target_column,
      **parameters,
    )

    fold_features = fold_validation_data[
      MODEL_FEATURE_COLUMNS
    ]
    fold_target = fold_validation_data[target_column]
    fold_prediction = model.predict(fold_features)
    fold_probability = model.predict_proba(
      fold_features
    )[:, 1]

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
    "cv_accuracy": (
      sum(fold_accuracy_scores) / len(fold_accuracy_scores)
    ),
    "cv_precision": (
      sum(fold_precision_scores) / len(fold_precision_scores)
    ),
    "cv_recall": (
      sum(fold_recall_scores) / len(fold_recall_scores)
    ),
    "cv_f1": (
      sum(fold_f1_scores) / len(fold_f1_scores)
    ),
    "cv_pr_auc": (
      sum(fold_pr_auc_scores) / len(fold_pr_auc_scores)
    ),
  }


def tune_hist_gradient_boosting(
  train_data: pd.DataFrame,
  target_column: str,
) -> dict:
  """Select parameters by highest CV PR-AUC, then CV F1."""
  tuning_results = []

  for parameters in HIST_GRADIENT_BOOSTING_CANDIDATES:
    print(
      "Testing HistGradientBoosting: "
      f"{parameters}"
    )

    scores = (
      evaluate_hist_gradient_boosting_parameters_with_time_series_cv(
        train_data=train_data,
        target_column=target_column,
        parameters=parameters,
      )
    )

    tuning_results.append({
      **parameters,
      **scores,
    })

  return sorted(
    tuning_results,
    key=lambda result: (
      result["cv_pr_auc"],
      result["cv_f1"],
    ),
    reverse=True,
  )[0]


def build_tuned_hist_gradient_boosting_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  best_parameters: dict,
  decision_threshold: float,
  split: str = "validation",
) -> dict:
  """Build one validation result for tuned HistGradientBoosting."""
  parameters = (
    f"learning_rate={best_parameters['learning_rate']}; "
    f"max_iter={best_parameters['max_iter']}; "
    f"max_leaf_nodes={best_parameters['max_leaf_nodes']}; "
    f"min_samples_leaf={best_parameters['min_samples_leaf']}; "
    f"l2_regularization={best_parameters['l2_regularization']}; "
    f"cv_splits={HIST_GRADIENT_BOOSTING_TUNING_SPLITS}; "
    f"cv_accuracy={best_parameters['cv_accuracy']:.6f}; "
    f"cv_precision={best_parameters['cv_precision']:.6f}; "
    f"cv_recall={best_parameters['cv_recall']:.6f}; "
    f"cv_f1={best_parameters['cv_f1']:.6f}; "
    f"cv_pr_auc={best_parameters['cv_pr_auc']:.6f}; "
    "loss=log_loss; sample_weight=balanced; "
    "early_stopping=False; random_state=42"
  )

  return build_model_result_row(
    model_name="hist_gradient_boosting_classifier_tuned",
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=add_decision_threshold_to_parameters(
      parameter_text=parameters,
      decision_threshold=decision_threshold,
    ),
    notes=(
      "HistGradientBoosting parameters selected by highest "
      "TimeSeriesSplit PR-AUC, then F1, on the chronological train split."
    ),
  )


def run_tuned_hist_gradient_boosting(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Tune and evaluate HistGradientBoosting for all horizons."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  training_data = load_training_dataset(
    training_dataset_path
  )

  train_data, validation_data, _ = (
    split_time_series_data_from_config(
      data=training_data,
      modeling_config=modeling_config,
    )
  )

  prepared_train, prepared_validation, spike_threshold = (
    prepare_classification_training_splits(
      train_data=train_data,
      validation_data=validation_data,
      horizons_hours=horizons_hours,
    )
  )

  for horizon_hours in horizons_hours:
    target_column = build_spike_target_column_name(
      horizon_hours
    )

    print("")
    print(f"Tuning HistGradientBoosting: {horizon_hours}h")
    print("=" * 46)

    best_parameters = tune_hist_gradient_boosting(
      train_data=prepared_train,
      target_column=target_column,
    )

    tuned_model = train_hist_gradient_boosting_classifier(
      train_data=prepared_train,
      target_column=target_column,
      learning_rate=best_parameters["learning_rate"],
      max_iter=best_parameters["max_iter"],
      max_leaf_nodes=best_parameters["max_leaf_nodes"],
      min_samples_leaf=best_parameters["min_samples_leaf"],
      l2_regularization=best_parameters[
        "l2_regularization"
      ],
    )

    validation_scores, decision_threshold = (
      evaluate_classifier_on_validation(
        model=tuned_model,
        validation_data=prepared_validation,
        target_column=target_column,
      )
    )

    result = build_tuned_hist_gradient_boosting_result(
      scores=validation_scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
      best_parameters=best_parameters,
      decision_threshold=decision_threshold,
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print(
      f"Best learning_rate: "
      f"{best_parameters['learning_rate']}"
    )
    print(
      f"Best max_iter: "
      f"{best_parameters['max_iter']}"
    )
    print(
      f"Best max_leaf_nodes: "
      f"{best_parameters['max_leaf_nodes']}"
    )
    print(
      f"Best min_samples_leaf: "
      f"{best_parameters['min_samples_leaf']}"
    )
    print(
      f"Best l2_regularization: "
      f"{best_parameters['l2_regularization']}"
    )
    print(f"Spike threshold: {spike_threshold:.4f}")
    print(
      f"Decision threshold: "
      f"{decision_threshold:.4f}"
    )
    print(
      f"CV PR-AUC: "
      f"{best_parameters['cv_pr_auc']:.4f}"
    )
    print(
      f"CV F1: "
      f"{best_parameters['cv_f1']:.4f}"
    )
    print(
      f"Validation F1: "
      f"{validation_scores['f1']:.4f}"
    )
    print(
      f"Validation PR-AUC: "
      f"{validation_scores['pr_auc']:.4f}"
    )

  return results_path


if __name__ == "__main__":
  written_path = run_tuned_hist_gradient_boosting()

  print("")
  print(f"Results written to: {written_path}")
