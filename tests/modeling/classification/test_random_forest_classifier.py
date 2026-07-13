import pandas as pd
import pytest
from sklearn.ensemble import RandomForestClassifier

from electricity_predictor.modeling.classification.random_forest.random_forest_classifier import (
  CLASSIFICATION_FEATURE_COLUMNS,
  build_random_forest_result,
  evaluate_random_forest_classifier,
  train_random_forest_classifier,
)


def make_classification_data() -> pd.DataFrame:
  """Create a small dataset with every required classification feature."""
  row_count = 20

  data = pd.DataFrame({
    column: [float(index % 10) for index in range(row_count)]
    for column in CLASSIFICATION_FEATURE_COLUMNS
  })

  data["is_spike_target_1h"] = [0] * 10 + [1] * 10

  return data


def test_train_random_forest_classifier_returns_fitted_model():
  data = make_classification_data()

  model = train_random_forest_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  assert isinstance(model, RandomForestClassifier)
  assert model.class_weight == "balanced"
  assert model.n_jobs == -1
  assert hasattr(model, "classes_")


def test_train_random_forest_classifier_rejects_missing_target():
  data = make_classification_data()

  with pytest.raises(ValueError, match="Missing classification target column"):
    train_random_forest_classifier(
      train_data=data,
      target_column="is_spike_target_24h",
    )


def test_evaluate_random_forest_classifier_returns_metrics():
  data = make_classification_data()

  model = train_random_forest_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    n_estimators=20,
  )

  scores = evaluate_random_forest_classifier(
    model=model,
    evaluation_data=data,
    target_column="is_spike_target_1h",
  )

  assert set(scores) == {"accuracy", "precision", "recall", "f1"}
  assert all(0.0 <= value <= 1.0 for value in scores.values())


def test_build_random_forest_result_uses_shared_schema():
  result = build_random_forest_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
    },
    row_count=100,
    horizon_hours=6,
    n_estimators=200,
    max_depth=10,
    min_samples_leaf=5,
  )

  assert result["model_name"] == "random_forest_classifier"
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 6
  assert result["f1"] == pytest.approx(0.75)
  assert result["mae"] is None
  assert "n_estimators=200" in result["model_parameters"]
  assert "max_depth=10" in result["model_parameters"]
