import pandas as pd
import pytest

from electricity_predictor.modeling.classification.logistic.logistic_tuning import (
  build_tuned_logistic_result,
  evaluate_logistic_c_with_time_series_cv,
  tune_logistic_c,
)
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)


def make_time_series_classification_data(row_count: int = 200) -> pd.DataFrame:
  """Create ordered classification data with every required feature."""
  data = pd.DataFrame({
    column: [float(index % 10) for index in range(row_count)]
    for column in MODEL_FEATURE_COLUMNS
  })

  data["is_spike_target_1h"] = [
    0 if index % 4 else 1
    for index in range(row_count)
  ]

  return data


def test_evaluate_logistic_c_with_time_series_cv_returns_expected_metrics():
  data = make_time_series_classification_data()

  scores = evaluate_logistic_c_with_time_series_cv(
    train_data=data,
    c_value=1.0,
    target_column="is_spike_target_1h",
    n_splits=3,
  )

  assert set(scores) == {
    "cv_accuracy",
    "cv_precision",
    "cv_recall",
    "cv_f1",
    "cv_pr_auc",
  }

  assert all(0.0 <= value <= 1.0 for value in scores.values())
  assert 0.0 <= scores["cv_pr_auc"] <= 1.0


def test_tune_logistic_c_selects_one_configured_value():
  data = make_time_series_classification_data()

  best_result = tune_logistic_c(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  assert best_result["c_value"] in [0.01, 0.1, 1.0, 10.0, 100.0]
  assert "cv_f1" in best_result


def test_build_tuned_logistic_result_uses_shared_schema():
  result = build_tuned_logistic_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.75,
      "recall": 0.80,
      "f1": 0.77,
    },
    row_count=100,
    horizon_hours=6,
    best_c=10.0,
    cv_scores={
      "cv_accuracy": 0.85,
      "cv_precision": 0.70,
      "cv_recall": 0.75,
      "cv_f1": 0.72,
      "cv_pr_auc": 0.74,
    },
  )

  assert result["model_name"] == "logistic_regression_tuned"
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 6
  assert result["f1"] == pytest.approx(0.77)
  assert "best_C=10.0" in result["model_parameters"]
  assert result["mae"] is None


def test_tune_logistic_c_prioritizes_pr_auc_then_f1(monkeypatch):
  data = make_time_series_classification_data()

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification.logistic."
    "logistic_tuning.LOGISTIC_C_VALUES",
    [0.1, 1.0, 10.0],
  )

  scores_by_c = {
    0.1: {
      "cv_accuracy": 0.80,
      "cv_precision": 0.70,
      "cv_recall": 0.80,
      "cv_f1": 0.90,
      "cv_pr_auc": 0.60,
    },
    1.0: {
      "cv_accuracy": 0.82,
      "cv_precision": 0.72,
      "cv_recall": 0.75,
      "cv_f1": 0.70,
      "cv_pr_auc": 0.75,
    },
    10.0: {
      "cv_accuracy": 0.83,
      "cv_precision": 0.73,
      "cv_recall": 0.78,
      "cv_f1": 0.74,
      "cv_pr_auc": 0.75,
    },
  }

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification.logistic."
    "logistic_tuning.evaluate_logistic_c_with_time_series_cv",
    lambda **kwargs: scores_by_c[kwargs["c_value"]],
  )

  best_result = tune_logistic_c(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  # C=0.1 has the highest F1 but weaker PR-AUC, so it must not win.
  # C=10 and C=1 tie on PR-AUC; C=10 wins through the F1 tie-break.
  assert best_result["c_value"] == 10.0
