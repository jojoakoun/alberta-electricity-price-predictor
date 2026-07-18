import pandas as pd
import pytest

from electricity_predictor.modeling.classification.random_forest.random_forest_tuning import (
  build_tuned_random_forest_result,
  evaluate_random_forest_parameters_with_time_series_cv,
  tune_random_forest,
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
    1 if index % 4 == 0 else 0
    for index in range(row_count)
  ]

  return data


def test_evaluate_random_forest_parameters_returns_expected_metrics():
  data = make_time_series_classification_data()

  scores = evaluate_random_forest_parameters_with_time_series_cv(
    train_data=data,
    target_column="is_spike_target_1h",
    n_estimators=10,
    max_depth=5,
    min_samples_leaf=1,
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


def test_tune_random_forest_returns_best_parameter_set(monkeypatch):
  data = make_time_series_classification_data()

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification.random_forest."
    "random_forest_tuning.RANDOM_FOREST_N_ESTIMATORS",
    [10],
  )
  monkeypatch.setattr(
    "electricity_predictor.modeling.classification.random_forest."
    "random_forest_tuning.RANDOM_FOREST_MAX_DEPTHS",
    [5],
  )
  monkeypatch.setattr(
    "electricity_predictor.modeling.classification.random_forest."
    "random_forest_tuning.RANDOM_FOREST_MIN_SAMPLES_LEAF",
    [1],
  )

  best_result = tune_random_forest(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  assert best_result["n_estimators"] == 10
  assert best_result["max_depth"] == 5
  assert best_result["min_samples_leaf"] == 1
  assert "cv_f1" in best_result


def test_build_tuned_random_forest_result_uses_shared_schema():
  result = build_tuned_random_forest_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
    },
    row_count=100,
    horizon_hours=6,
    best_parameters={
      "n_estimators": 200,
      "max_depth": 10,
      "min_samples_leaf": 5,
      "cv_accuracy": 0.85,
      "cv_precision": 0.75,
      "cv_recall": 0.70,
      "cv_f1": 0.72,
    },
  )

  assert result["model_name"] == "random_forest_classifier_tuned"
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 6
  assert result["f1"] == pytest.approx(0.75)
  assert result["mae"] is None
  assert "n_estimators=200" in result["model_parameters"]
  assert "max_depth=10" in result["model_parameters"]
