import pytest

from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
)


def test_calculate_classification_metrics_returns_expected_values():
  metrics = calculate_classification_metrics(
    target=[1, 1, 0, 0],
    prediction=[1, 0, 0, 0],
  )

  assert metrics["accuracy"] == pytest.approx(0.75)
  assert metrics["precision"] == pytest.approx(1.0)
  assert metrics["recall"] == pytest.approx(0.5)
  assert metrics["f1"] == pytest.approx(2 / 3)


def test_calculate_classification_metrics_handles_no_positive_predictions():
  metrics = calculate_classification_metrics(
    target=[1, 0, 1, 0],
    prediction=[0, 0, 0, 0],
  )

  assert metrics["precision"] == 0.0
  assert metrics["recall"] == 0.0
  assert metrics["f1"] == 0.0


def test_calculate_classification_metrics_returns_pr_auc_from_probabilities():
  metrics = calculate_classification_metrics(
    target=[1, 0, 1, 0],
    prediction=[1, 0, 0, 0],
    probability=[0.9, 0.2, 0.6, 0.1],
  )

  assert metrics["pr_auc"] == pytest.approx(1.0)


def test_calculate_classification_metrics_returns_none_without_probabilities():
  metrics = calculate_classification_metrics(
    target=[1, 0, 1, 0],
    prediction=[1, 0, 0, 0],
  )

  assert metrics["pr_auc"] is None
