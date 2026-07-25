import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.extra_trees.extra_trees_tuning import (
  build_tuned_extra_trees_result,
  evaluate_extra_trees_parameters_with_time_series_cv,
  tune_extra_trees,
)


def make_time_series_data(
  row_count: int = 240,
) -> pd.DataFrame:
  """Create ordered synthetic classification data."""
  data = pd.DataFrame({
    column: [
      float((index * (column_index + 1)) % 29)
      for index in range(row_count)
    ]
    for column_index, column in enumerate(
      MODEL_FEATURE_COLUMNS
    )
  })

  data["is_spike_target_1h"] = [
    1 if index % 5 == 0 else 0
    for index in range(row_count)
  ]

  return data


def test_evaluate_extra_trees_parameters_returns_cv_metrics():
  data = make_time_series_data()

  scores = evaluate_extra_trees_parameters_with_time_series_cv(
    train_data=data,
    target_column="is_spike_target_1h",
    parameters={
      "n_estimators": 10,
      "max_depth": 10,
      "min_samples_leaf": 2,
      "max_features": "sqrt",
    },
    n_splits=3,
  )

  assert set(scores) == {
    "cv_accuracy",
    "cv_precision",
    "cv_recall",
    "cv_f1",
    "cv_pr_auc",
  }

  assert all(
    0.0 <= value <= 1.0
    for value in scores.values()
  )


def test_tune_extra_trees_prioritizes_pr_auc_then_f1(
  monkeypatch,
):
  data = make_time_series_data()

  candidates = [
    {
      "n_estimators": 100,
      "max_depth": None,
      "min_samples_leaf": 1,
      "max_features": "sqrt",
    },
    {
      "n_estimators": 200,
      "max_depth": 20,
      "min_samples_leaf": 2,
      "max_features": "sqrt",
    },
    {
      "n_estimators": 300,
      "max_depth": 10,
      "min_samples_leaf": 5,
      "max_features": "sqrt",
    },
  ]

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification."
    "extra_trees.extra_trees_tuning.EXTRA_TREES_CANDIDATES",
    candidates,
  )

  scores_by_estimators = {
    100: {
      "cv_accuracy": 0.80,
      "cv_precision": 0.70,
      "cv_recall": 0.80,
      "cv_f1": 0.90,
      "cv_pr_auc": 0.60,
    },
    200: {
      "cv_accuracy": 0.82,
      "cv_precision": 0.72,
      "cv_recall": 0.75,
      "cv_f1": 0.70,
      "cv_pr_auc": 0.75,
    },
    300: {
      "cv_accuracy": 0.83,
      "cv_precision": 0.73,
      "cv_recall": 0.78,
      "cv_f1": 0.74,
      "cv_pr_auc": 0.75,
    },
  }

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification."
    "extra_trees.extra_trees_tuning."
    "evaluate_extra_trees_parameters_with_time_series_cv",
    lambda **kwargs: scores_by_estimators[
      kwargs["parameters"]["n_estimators"]
    ],
  )

  best_result = tune_extra_trees(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  # The first candidate has higher F1 but lower PR-AUC.
  # The last two tie on PR-AUC, so the higher F1 wins.
  assert best_result["n_estimators"] == 300


def test_build_tuned_extra_trees_result_uses_schema():
  result = build_tuned_extra_trees_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
      "pr_auc": 0.79,
    },
    row_count=100,
    horizon_hours=12,
    best_parameters={
      "n_estimators": 300,
      "max_depth": 20,
      "min_samples_leaf": 5,
      "max_features": "sqrt",
      "cv_accuracy": 0.85,
      "cv_precision": 0.75,
      "cv_recall": 0.70,
      "cv_f1": 0.72,
      "cv_pr_auc": 0.76,
    },
    decision_threshold=0.60,
  )

  assert result["model_name"] == (
    "extra_trees_classifier_tuned"
  )
  assert result["f1"] == pytest.approx(0.75)
  assert "cv_pr_auc=0.760000" in result["model_parameters"]
  assert "decision_threshold=0.6000" in (
    result["model_parameters"]
  )
