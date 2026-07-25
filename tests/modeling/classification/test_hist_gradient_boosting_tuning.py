import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.hist_gradient_boosting.hist_gradient_boosting_tuning import (
  build_tuned_hist_gradient_boosting_result,
  evaluate_hist_gradient_boosting_parameters_with_time_series_cv,
  tune_hist_gradient_boosting,
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


def test_evaluate_hist_gradient_boosting_parameters_returns_metrics():
  data = make_time_series_data()

  scores = (
    evaluate_hist_gradient_boosting_parameters_with_time_series_cv(
      train_data=data,
      target_column="is_spike_target_1h",
      parameters={
        "learning_rate": 0.1,
        "max_iter": 20,
        "max_leaf_nodes": 15,
        "min_samples_leaf": 5,
        "l2_regularization": 0.0,
      },
      n_splits=3,
    )
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


def test_tune_hist_gradient_boosting_prioritizes_pr_auc_then_f1(
  monkeypatch,
):
  data = make_time_series_data()

  candidates = [
    {
      "learning_rate": 0.05,
      "max_iter": 100,
      "max_leaf_nodes": 15,
      "min_samples_leaf": 20,
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

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification."
    "hist_gradient_boosting.hist_gradient_boosting_tuning."
    "HIST_GRADIENT_BOOSTING_CANDIDATES",
    candidates,
  )

  scores_by_max_iter = {
    100: {
      "cv_accuracy": 0.80,
      "cv_precision": 0.70,
      "cv_recall": 0.80,
      "cv_f1": 0.90,
      "cv_pr_auc": 0.60,
    },
    200: {
      "cv_accuracy": 0.83,
      "cv_precision": 0.73,
      "cv_recall": 0.78,
      "cv_f1": 0.74,
      "cv_pr_auc": 0.75,
    },
  }

  call_number = {"value": 0}

  def fake_evaluation(**kwargs):
    parameters = kwargs["parameters"]

    if parameters["max_iter"] == 100:
      call_number["value"] += 1

      if call_number["value"] == 1:
        return scores_by_max_iter[100]

      return {
        "cv_accuracy": 0.82,
        "cv_precision": 0.72,
        "cv_recall": 0.75,
        "cv_f1": 0.70,
        "cv_pr_auc": 0.75,
      }

    return scores_by_max_iter[200]

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification."
    "hist_gradient_boosting.hist_gradient_boosting_tuning."
    "evaluate_hist_gradient_boosting_parameters_with_time_series_cv",
    fake_evaluation,
  )

  best_result = tune_hist_gradient_boosting(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  # The first candidate has better F1 but weaker PR-AUC.
  # The last two tie on PR-AUC, so the higher F1 wins.
  assert best_result["max_iter"] == 200


def test_build_tuned_hist_gradient_boosting_result_uses_schema():
  result = build_tuned_hist_gradient_boosting_result(
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
      "learning_rate": 0.05,
      "max_iter": 200,
      "max_leaf_nodes": 31,
      "min_samples_leaf": 20,
      "l2_regularization": 1.0,
      "cv_accuracy": 0.85,
      "cv_precision": 0.75,
      "cv_recall": 0.70,
      "cv_f1": 0.72,
      "cv_pr_auc": 0.76,
    },
    decision_threshold=0.60,
  )

  assert result["model_name"] == (
    "hist_gradient_boosting_classifier_tuned"
  )
  assert result["f1"] == pytest.approx(0.75)
  assert "cv_pr_auc=0.760000" in result["model_parameters"]
  assert "decision_threshold=0.6000" in (
    result["model_parameters"]
  )
