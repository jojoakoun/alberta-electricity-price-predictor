import pandas as pd
import pytest
from sklearn.ensemble import HistGradientBoostingClassifier

from electricity_predictor.modeling.classification.hist_gradient_boosting.hist_gradient_boosting_classifier import (
  CLASSIFICATION_FEATURE_COLUMNS,
  build_hist_gradient_boosting_result,
  evaluate_hist_gradient_boosting_classifier,
  train_hist_gradient_boosting_classifier,
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


def test_train_hist_gradient_boosting_returns_fitted_model():
  data = make_classification_data()

  model = train_hist_gradient_boosting_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    max_iter=20,
    min_samples_leaf=5,
  )

  assert isinstance(model, HistGradientBoostingClassifier)
  assert model.early_stopping is False
  assert model.random_state == 42
  assert hasattr(model, "classes_")


def test_train_hist_gradient_boosting_rejects_missing_target():
  data = make_classification_data()

  with pytest.raises(
    ValueError,
    match="Missing classification target column",
  ):
    train_hist_gradient_boosting_classifier(
      train_data=data,
      target_column="is_spike_target_24h",
    )


def test_evaluate_hist_gradient_boosting_returns_metrics():
  data = make_classification_data()

  model = train_hist_gradient_boosting_classifier(
    train_data=data,
    target_column="is_spike_target_1h",
    max_iter=20,
    min_samples_leaf=5,
  )

  scores = evaluate_hist_gradient_boosting_classifier(
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


def test_build_hist_gradient_boosting_result_records_cutoff():
  result = build_hist_gradient_boosting_result(
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

  assert result["model_name"] == (
    "hist_gradient_boosting_classifier"
  )
  assert result["horizon_hours"] == 6
  assert result["f1"] == pytest.approx(0.75)
  assert "max_leaf_nodes=31" in result["model_parameters"]
  assert "decision_threshold=0.4500" in (
    result["model_parameters"]
  )
