import numpy as np
import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.validation_evaluation import (
  add_decision_threshold_to_parameters,
  evaluate_classifier_on_validation,
  extract_positive_class_probability,
)


def make_validation_data() -> pd.DataFrame:
  """Create validation rows with every official classification feature."""
  data = pd.DataFrame({
    column: [1.0, 2.0, 3.0, 4.0]
    for column in MODEL_FEATURE_COLUMNS
  })

  data["is_spike_target_1h"] = [0, 0, 1, 1]

  return data


class FakeClassifier:
  def predict_proba(self, features):
    assert list(features.columns) == MODEL_FEATURE_COLUMNS

    return np.array([
      [0.90, 0.10],
      [0.60, 0.40],
      [0.55, 0.45],
      [0.10, 0.90],
    ])


def test_extract_positive_class_probability_returns_second_column():
  probability = extract_positive_class_probability(
    model=FakeClassifier(),
    data=make_validation_data(),
  )

  assert probability.tolist() == pytest.approx([
    0.10,
    0.40,
    0.45,
    0.90,
  ])


def test_evaluate_classifier_on_validation_selects_best_f1_cutoff():
  scores, threshold = evaluate_classifier_on_validation(
    model=FakeClassifier(),
    validation_data=make_validation_data(),
    target_column="is_spike_target_1h",
  )

  assert threshold == pytest.approx(0.45)
  assert scores["f1"] == pytest.approx(1.0)
  assert set(scores) == {
    "accuracy",
    "precision",
    "recall",
    "f1",
    "pr_auc",
  }


def test_evaluate_classifier_on_validation_rejects_missing_target():
  with pytest.raises(
    ValueError,
    match="Missing classification target column",
  ):
    evaluate_classifier_on_validation(
      model=FakeClassifier(),
      validation_data=make_validation_data(),
      target_column="is_spike_target_24h",
    )


def test_extract_positive_class_probability_requires_predict_proba():
  with pytest.raises(
    ValueError,
    match="must provide predict_proba",
  ):
    extract_positive_class_probability(
      model=object(),
      data=make_validation_data(),
    )


def test_extract_positive_class_probability_rejects_invalid_shape():
  class InvalidClassifier:
    def predict_proba(self, features):
      return np.array([0.10, 0.20, 0.30, 0.40])

  with pytest.raises(
    ValueError,
    match="two-dimensional",
  ):
    extract_positive_class_probability(
      model=InvalidClassifier(),
      data=make_validation_data(),
    )


def test_add_decision_threshold_to_parameters_appends_cutoff():
  parameters = add_decision_threshold_to_parameters(
    parameter_text="n_estimators=200; max_depth=10",
    decision_threshold=0.45,
  )

  assert parameters == (
    "n_estimators=200; max_depth=10; "
    "decision_threshold=0.4500"
  )


def test_add_decision_threshold_to_parameters_supports_empty_text():
  parameters = add_decision_threshold_to_parameters(
    parameter_text="",
    decision_threshold=0.70,
  )

  assert parameters == "decision_threshold=0.7000"
