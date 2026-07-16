import numpy as np
import pytest

from electricity_predictor.modeling.classification.decision_threshold import (
  apply_decision_threshold,
  select_f1_decision_threshold,
)


def test_select_f1_decision_threshold_selects_best_validation_cutoff():
  result = select_f1_decision_threshold(
    target=[0, 0, 1, 1],
    probability=[0.10, 0.40, 0.45, 0.90],
    thresholds=np.array([0.30, 0.50, 0.70]),
  )

  assert result["decision_threshold"] == pytest.approx(0.30)
  assert result["validation_f1"] == pytest.approx(0.8)


def test_select_f1_decision_threshold_prefers_larger_cutoff_on_tie():
  result = select_f1_decision_threshold(
    target=[0, 1],
    probability=[0.10, 0.90],
    thresholds=np.array([0.30, 0.70]),
  )

  assert result["validation_f1"] == pytest.approx(1.0)
  assert result["decision_threshold"] == pytest.approx(0.70)


def test_select_f1_decision_threshold_rejects_mismatched_lengths():
  with pytest.raises(ValueError, match="same number of rows"):
    select_f1_decision_threshold(
      target=[0, 1],
      probability=[0.25],
    )


def test_apply_decision_threshold_returns_binary_predictions():
  prediction = apply_decision_threshold(
    probability=[0.20, 0.50, 0.80],
    threshold=0.50,
  )

  assert prediction.tolist() == [0, 1, 1]


def test_apply_decision_threshold_rejects_invalid_cutoff():
  with pytest.raises(ValueError, match="between 0 and 1"):
    apply_decision_threshold(
      probability=[0.20, 0.80],
      threshold=1.20,
    )
