import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingClassifier

from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_classifier import (
  CLASSIFICATION_FEATURE_COLUMNS,
  build_gradient_boosting_result,
  evaluate_gradient_boosting_classifier,
  train_gradient_boosting_classifier,
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


def test_train_gradient_boosting_classifier_returns_fitted_model():
  data = make_classification_data()

  model = train_gradient_boosting_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    n_estimators=20,
  )

  assert isinstance(model, GradientBoostingClassifier)
  assert model.random_state == 42
  assert hasattr(model, "classes_")


def test_train_gradient_boosting_classifier_rejects_missing_target():
  data = make_classification_data()

  with pytest.raises(ValueError, match="Missing classification target column"):
    train_gradient_boosting_classifier(
      train_data=data,
      target_column="is_spike_target_24h",
    )


def test_evaluate_gradient_boosting_classifier_returns_metrics():
  data = make_classification_data()

  model = train_gradient_boosting_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    n_estimators=20,
  )

  scores = evaluate_gradient_boosting_classifier(
    model=model,
    evaluation_data=data,
    target_column="is_spike_target_1h",
  )

  assert set(scores) == {"accuracy", "precision", "recall", "f1"}
  assert all(0.0 <= value <= 1.0 for value in scores.values())


def test_build_gradient_boosting_result_uses_shared_schema():
  result = build_gradient_boosting_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
    },
    row_count=100,
    horizon_hours=6,
    n_estimators=200,
    learning_rate=0.05,
    max_depth=2,
  )

  assert result["model_name"] == "gradient_boosting_classifier"
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 6
  assert result["f1"] == pytest.approx(0.75)
  assert result["mae"] is None
  assert "n_estimators=200" in result["model_parameters"]
  assert "learning_rate=0.05" in result["model_parameters"]
  assert "max_depth=2" in result["model_parameters"]
