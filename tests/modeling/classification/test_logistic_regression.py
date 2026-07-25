import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from electricity_predictor.modeling.classification.logistic.logistic_regression import (
  CLASSIFICATION_FEATURE_COLUMNS,
  build_logistic_regression_result,
  evaluate_logistic_regression_model,
  train_logistic_regression_model,
)


def make_classification_data() -> pd.DataFrame:
  """Create a small balanced dataset with all required predictors."""
  row_count = 20

  data = pd.DataFrame({
    column: [float(index) for index in range(row_count)]
    for column in CLASSIFICATION_FEATURE_COLUMNS
  })

  data["is_spike_target_1h"] = [0] * 10 + [1] * 10

  return data


def test_train_logistic_regression_model_returns_scaled_pipeline():
  data = make_classification_data()

  model = train_logistic_regression_model(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  assert isinstance(model, Pipeline)
  assert isinstance(model.named_steps["scaler"], StandardScaler)
  assert model.named_steps["classifier"].class_weight == "balanced"


def test_train_logistic_regression_model_rejects_missing_target():
  data = make_classification_data()

  with pytest.raises(ValueError, match="Missing classification target column"):
    train_logistic_regression_model(
      train_data=data,
      target_column="is_spike_target_24h",
    )


def test_evaluate_logistic_regression_model_returns_classification_metrics():
  data = make_classification_data()

  model = train_logistic_regression_model(
    train_data=data,
    target_column="is_spike_target_1h",
  )

  scores = evaluate_logistic_regression_model(
    model=model,
    evaluation_data=data,
    target_column="is_spike_target_1h",
  )

  assert set(scores) == {"accuracy", "precision", "recall", "f1", "pr_auc"}
  assert all(0.0 <= value <= 1.0 for value in scores.values())


def test_build_logistic_regression_result_uses_shared_schema():
  result = build_logistic_regression_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
    },
    row_count=100,
    horizon_hours=6,
  )

  assert result["model_name"] == "logistic_regression"
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 6
  assert result["split"] == "validation"
  assert result["accuracy"] == pytest.approx(0.90)
  assert result["mae"] is None
  assert "class_weight=balanced" in result["model_parameters"]
