"""Tune and evaluate live-contract spike classifiers on validation only."""

from __future__ import annotations

import argparse
import json
from itertools import product
from pathlib import Path

import pandas as pd
from sklearn.ensemble import (
  GradientBoostingClassifier,
  HistGradientBoostingClassifier,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)
from electricity_predictor.modeling.classification.decision_threshold import (
  evaluate_at_best_f1_threshold,
)
from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_tuning import (
  GRADIENT_BOOSTING_LEARNING_RATES,
  GRADIENT_BOOSTING_MAX_DEPTHS,
  GRADIENT_BOOSTING_N_ESTIMATORS,
)
from electricity_predictor.modeling.classification.hist_gradient_boosting.hist_gradient_boosting_tuning import (
  HIST_GRADIENT_BOOSTING_CANDIDATES,
)
from electricity_predictor.modeling.classification.spike_definition import (
  calculate_iqr_spike_threshold,
  classify_spikes,
)
from electricity_predictor.modeling.live_contract.regression_validation import (
  load_live_training_dataset,
)
from electricity_predictor.modeling.live_contract.validation_comparison import (
  build_validation_only_splits,
)
from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
)
from electricity_predictor.modeling.split import (
  get_time_series_cv_gap_hours,
)


CV_SPLITS = 3

CLASSIFICATION_METRIC_NAMES = [
  "accuracy",
  "precision",
  "recall",
  "f1",
  "pr_auc",
]


def build_candidate_configurations() -> list[dict]:
  """Return the established HGB and GB classification search spaces."""
  candidates = []

  for parameters in HIST_GRADIENT_BOOSTING_CANDIDATES:
    candidates.append({
      "model_family":
        "hist_gradient_boosting",
      "model_name":
        "hist_gradient_boosting_classifier_tuned",
      **parameters,
    })

  for (
    n_estimators,
    learning_rate,
    max_depth,
  ) in product(
    GRADIENT_BOOSTING_N_ESTIMATORS,
    GRADIENT_BOOSTING_LEARNING_RATES,
    GRADIENT_BOOSTING_MAX_DEPTHS,
  ):
    candidates.append({
      "model_family":
        "gradient_boosting",
      "model_name":
        "gradient_boosting_classifier_tuned",
      "n_estimators":
        n_estimators,
      "learning_rate":
        learning_rate,
      "max_depth":
        max_depth,
    })

  return candidates


def build_classifier(
  candidate: dict,
):
  """Build one classifier for the selected live feature contract."""
  model_family = candidate[
    "model_family"
  ]

  if model_family == (
    "hist_gradient_boosting"
  ):
    return HistGradientBoostingClassifier(
      loss="log_loss",
      learning_rate=float(
        candidate["learning_rate"]
      ),
      max_iter=int(
        candidate["max_iter"]
      ),
      max_leaf_nodes=int(
        candidate["max_leaf_nodes"]
      ),
      min_samples_leaf=int(
        candidate["min_samples_leaf"]
      ),
      l2_regularization=float(
        candidate["l2_regularization"]
      ),
      early_stopping=False,
      random_state=42,
    )

  if model_family == (
    "gradient_boosting"
  ):
    return GradientBoostingClassifier(
      n_estimators=int(
        candidate["n_estimators"]
      ),
      learning_rate=float(
        candidate["learning_rate"]
      ),
      max_depth=int(
        candidate["max_depth"]
      ),
      random_state=42,
    )

  raise ValueError(
    f"Unsupported model family: {model_family}"
  )


def add_spike_targets(
  data: pd.DataFrame,
  spike_threshold: float,
) -> pd.DataFrame:
  """Add all five spike labels with one frozen train-derived threshold."""
  labeled_data = data.copy()

  for horizon_hours in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    price_target_column = (
      f"actual_price_target_{horizon_hours}h"
    )

    spike_target_column = (
      f"is_spike_target_{horizon_hours}h"
    )

    labeled_data[
      spike_target_column
    ] = classify_spikes(
      prices=labeled_data[
        price_target_column
      ],
      threshold=spike_threshold,
    )

  return labeled_data


def prepare_live_classification_splits(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
) -> tuple[
  pd.DataFrame,
  pd.DataFrame,
  float,
]:
  """Fit the spike definition on train and apply it to both periods."""
  spike_threshold = (
    calculate_iqr_spike_threshold(
      train_data["actual_price"]
    )
  )

  prepared_train = add_spike_targets(
    data=train_data,
    spike_threshold=spike_threshold,
  )

  prepared_validation = add_spike_targets(
    data=validation_data,
    spike_threshold=spike_threshold,
  )

  return (
    prepared_train,
    prepared_validation,
    spike_threshold,
  )


def fit_classifier(
  candidate: dict,
  train_data: pd.DataFrame,
  target_column: str,
):
  """Fit one balanced classifier."""
  model = build_classifier(
    candidate
  )

  sample_weight = compute_sample_weight(
    class_weight="balanced",
    y=train_data[target_column],
  )

  model.fit(
    train_data[
      SELECTED_LIVE_FEATURE_COLUMNS
    ],
    train_data[target_column],
    sample_weight=sample_weight,
  )

  return model


def evaluate_candidate_with_cv(
  candidate: dict,
  train_data: pd.DataFrame,
  target_column: str,
  gap_hours: int,
  n_splits: int = CV_SPLITS,
) -> dict:
  """Evaluate one candidate with chronological training folds."""
  splitter = TimeSeriesSplit(
    n_splits=n_splits,
    gap=gap_hours,
  )

  fold_metrics = {
    metric_name: []
    for metric_name in (
      CLASSIFICATION_METRIC_NAMES
    )
  }

  for (
    fold_number,
    (
      fold_train_index,
      fold_validation_index,
    ),
  ) in enumerate(
    splitter.split(train_data),
    start=1,
  ):
    fold_train = train_data.iloc[
      fold_train_index
    ]

    fold_validation = train_data.iloc[
      fold_validation_index
    ]

    model = fit_classifier(
      candidate=candidate,
      train_data=fold_train,
      target_column=target_column,
    )

    features = fold_validation[
      SELECTED_LIVE_FEATURE_COLUMNS
    ]

    prediction = model.predict(
      features
    )

    probability = model.predict_proba(
      features
    )[:, 1]

    scores = calculate_classification_metrics(
      target=fold_validation[
        target_column
      ],
      prediction=prediction,
      probability=probability,
    )

    if scores["pr_auc"] is None:
      raise ValueError(
        "Chronological classification fold "
        "does not contain both classes."
      )

    for metric_name in (
      CLASSIFICATION_METRIC_NAMES
    ):
      fold_metrics[
        metric_name
      ].append(
        float(
          scores[metric_name]
        )
      )

    print(
      f"    fold={fold_number} "
      f"f1={scores['f1']:.6f} "
      f"pr_auc={scores['pr_auc']:.6f}"
    )

  return {
    f"cv_{metric_name}": (
      sum(values) / len(values)
    )
    for (
      metric_name,
      values,
    ) in fold_metrics.items()
  }


def select_best_candidate(
  candidate_results: list[dict],
) -> dict:
  """Select highest CV PR-AUC, then CV F1 and deterministic model name."""
  if not candidate_results:
    raise ValueError(
      "Classification tuning produced no results."
    )

  return sorted(
    candidate_results,
    key=lambda result: (
      -result["cv_pr_auc"],
      -result["cv_f1"],
      -result["cv_recall"],
      result["model_name"],
      json.dumps(
        result["candidate"],
        sort_keys=True,
      ),
    ),
  )[0]


def tune_horizon(
  train_data: pd.DataFrame,
  target_column: str,
  gap_hours: int,
) -> dict:
  """Tune both shortlisted classifier families on the train period."""
  candidate_results = []

  for (
    candidate_number,
    candidate,
  ) in enumerate(
    build_candidate_configurations(),
    start=1,
  ):
    print(
      f"  candidate={candidate_number} "
      f"family={candidate['model_family']} "
      f"parameters="
      f"{json.dumps(candidate, sort_keys=True)}"
    )

    scores = evaluate_candidate_with_cv(
      candidate=candidate,
      train_data=train_data,
      target_column=target_column,
      gap_hours=gap_hours,
    )

    candidate_results.append({
      "candidate":
        candidate,
      "model_name":
        candidate["model_name"],
      **scores,
    })

  return select_best_candidate(
    candidate_results
  )


def evaluate_horizon(
  horizon_hours: int,
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  spike_threshold: float,
  gap_hours: int,
) -> dict:
  """Tune one horizon and select its validation decision threshold."""
  target_column = (
    f"is_spike_target_{horizon_hours}h"
  )

  print("")
  print(
    f"HORIZON {horizon_hours}H"
  )
  print("=" * 48)

  best_result = tune_horizon(
    train_data=train_data,
    target_column=target_column,
    gap_hours=gap_hours,
  )

  selected_candidate = best_result[
    "candidate"
  ]

  model = fit_classifier(
    candidate=selected_candidate,
    train_data=train_data,
    target_column=target_column,
  )

  validation_probability = (
    model.predict_proba(
      validation_data[
        SELECTED_LIVE_FEATURE_COLUMNS
      ]
    )[:, 1]
  )

  (
    validation_scores,
    decision_threshold,
  ) = evaluate_at_best_f1_threshold(
    target=validation_data[
      target_column
    ],
    probability=validation_probability,
  )

  print(
    "selected_model_family="
    f"{selected_candidate['model_family']}"
  )

  print(
    "selected_cv_pr_auc="
    f"{best_result['cv_pr_auc']:.6f}"
  )

  print(
    "selected_cv_f1="
    f"{best_result['cv_f1']:.6f}"
  )

  print(
    "validation_f1="
    f"{validation_scores['f1']:.6f}"
  )

  print(
    "validation_pr_auc="
    f"{validation_scores['pr_auc']:.6f}"
  )

  print(
    "decision_threshold="
    f"{decision_threshold:.4f}"
  )

  return {
    "contract":
      SELECTED_LIVE_FEATURE_CONTRACT,
    "horizon_hours":
      horizon_hours,
    "target_column":
      target_column,
    "feature_count":
      len(SELECTED_LIVE_FEATURE_COLUMNS),
    "train_rows":
      len(train_data),
    "validation_rows":
      len(validation_data),
    "spike_threshold":
      spike_threshold,
    "model_family":
      selected_candidate[
        "model_family"
      ],
    "model_name":
      selected_candidate[
        "model_name"
      ],
    "model_parameters":
      json.dumps(
        selected_candidate,
        sort_keys=True,
      ),
    "cv_splits":
      CV_SPLITS,
    "cv_gap_hours":
      gap_hours,
    "cv_accuracy":
      best_result["cv_accuracy"],
    "cv_precision":
      best_result["cv_precision"],
    "cv_recall":
      best_result["cv_recall"],
    "cv_f1":
      best_result["cv_f1"],
    "cv_pr_auc":
      best_result["cv_pr_auc"],
    "decision_threshold":
      decision_threshold,
    "validation_accuracy":
      validation_scores["accuracy"],
    "validation_precision":
      validation_scores["precision"],
    "validation_recall":
      validation_scores["recall"],
    "validation_f1":
      validation_scores["f1"],
    "validation_pr_auc":
      validation_scores["pr_auc"],
  }


def run_live_classification_validation() -> pd.DataFrame:
  """Run train-CV tuning and validation evaluation for all horizons."""
  configuration = load_configuration()

  modeling_config = configuration[
    "modeling"
  ]

  dataset = load_live_training_dataset()

  train_data, validation_data = (
    build_validation_only_splits(
      data=dataset,
      modeling_config=modeling_config,
    )
  )

  (
    prepared_train,
    prepared_validation,
    spike_threshold,
  ) = prepare_live_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
  )

  gap_hours = (
    get_time_series_cv_gap_hours(
      modeling_config
    )
  )

  results = []

  for horizon_hours in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    results.append(
      evaluate_horizon(
        horizon_hours=horizon_hours,
        train_data=prepared_train,
        validation_data=prepared_validation,
        spike_threshold=spike_threshold,
        gap_hours=gap_hours,
      )
    )

  return pd.DataFrame(
    results
  )


def print_summary(
  results: pd.DataFrame,
) -> None:
  """Print the selected model and validation metrics per horizon."""
  print("")
  print(
    "LIVE CLASSIFICATION VALIDATION SUMMARY"
  )
  print(
    "======================================"
  )

  columns = [
    "horizon_hours",
    "model_family",
    "train_rows",
    "validation_rows",
    "spike_threshold",
    "cv_f1",
    "cv_pr_auc",
    "validation_f1",
    "validation_pr_auc",
    "decision_threshold",
  ]

  print(
    results[columns]
    .sort_values(
      "horizon_hours"
    )
    .to_string(
      index=False,
      float_format=lambda value:
        f"{value:.6f}",
    )
  )

  print("")
  print(
    "selected_live_contract="
    f"{SELECTED_LIVE_FEATURE_CONTRACT}"
  )

  print(
    "selected_live_feature_count="
    f"{len(SELECTED_LIVE_FEATURE_COLUMNS)}"
  )

  print("protected_test_used=False")
  print("models_saved=False")
  print("active_registry_modified=False")


def main() -> None:
  """Run classification validation and write an isolated result table."""
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "--output",
    required=True,
    type=Path,
  )

  arguments = parser.parse_args()

  results = (
    run_live_classification_validation()
  )

  arguments.output.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  results.to_csv(
    arguments.output,
    index=False,
  )

  print_summary(
    results
  )

  print("")
  print(
    f"validation_results_path="
    f"{arguments.output}"
  )


if __name__ == "__main__":
  main()
