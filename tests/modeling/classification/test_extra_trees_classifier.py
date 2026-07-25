import pandas as pd
import pytest
from sklearn.ensemble import ExtraTreesClassifier

from electricity_predictor.modeling.classification.extra_trees.extra_trees_classifier import (
  CLASSIFICATION_FEATURE_COLUMNS,
  build_extra_trees_result,
  evaluate_extra_trees_classifier,
  train_extra_trees_classifier,
)


def make_classification_data(
  row_count: int = 120,
) -> pd.DataFrame:
  """Create balanced synthetic classification data."""
  data = pd.DataFrame({
    column: [
      float((index * (column_index + 1)) % 23)
      for index in range(row_count)
    ]
    for column_index, column in enumerate(
      CLASSIFICATION_FEATURE_COLUMNS
    )
  })

  data["is_spike_target_1h"] = [
    1 if index % 4 == 0 else 0
    for index in range(row_count)
  ]

  return data


def test_train_extra_trees_returns_fitted_model():
  data = make_classification_data()

  model = train_extra_trees_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    n_estimators=20,
    min_samples_leaf=2,
  )

  assert isinstance(model, ExtraTreesClassifier)
  assert model.class_weight == "balanced"
  assert model.random_state == 42
  assert hasattr(model, "classes_")


def test_train_extra_trees_rejects_missing_target():
  data = make_classification_data()

  with pytest.raises(
    ValueError,
    match="Missing classification target column",
  ):
    train_extra_trees_classifier(
      train_data=data,
      target_column="is_spike_target_24h",
    )


def test_evaluate_extra_trees_returns_metrics():
  data = make_classification_data()

  model = train_extra_trees_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    n_estimators=20,
    min_samples_leaf=2,
  )

  scores = evaluate_extra_trees_classifier(
    model=model,
    evaluation_data=data,
    target_column="is_spike_target_1h",
  )

  assert set(scores) == {
    "accuracy",
    "precision",
    "recall",
    "f1",
    "pr_auc",
  }

  assert all(
    0.0 <= value <= 1.0
    for value in scores.values()
  )


def test_build_extra_trees_result_records_cutoff():
  result = build_extra_trees_result(
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
      "pr_auc": 0.78,
    },
    row_count=100,
    horizon_hours=6,
    decision_threshold=0.45,
  )

  assert result["model_name"] == "extra_trees_classifier"
  assert result["horizon_hours"] == 6
  assert result["f1"] == pytest.approx(0.75)
  assert "n_estimators=200" in result["model_parameters"]
  assert "decision_threshold=0.4500" in (
    result["model_parameters"]
  )
