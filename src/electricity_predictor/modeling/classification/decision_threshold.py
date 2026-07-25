"""Select, validate, and apply classification probability thresholds."""

import numpy as np
from sklearn.metrics import f1_score

from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
)


DEFAULT_THRESHOLD_GRID = np.arange(0.05, 1.00, 0.05)


def validate_probabilities(probability) -> np.ndarray:
  """Validate positive-class probabilities."""
  values = np.asarray(probability, dtype=float)

  if values.ndim != 1:
    raise ValueError(
      "Probabilities must be one-dimensional."
    )

  if not np.isfinite(values).all():
    raise ValueError(
      "Probabilities must be finite."
    )

  if ((values < 0.0) | (values > 1.0)).any():
    raise ValueError(
      "Probabilities must be between 0 and 1."
    )

  return values


def validate_threshold_grid(thresholds) -> np.ndarray:
  """Validate candidate decision thresholds."""
  values = np.asarray(thresholds, dtype=float)

  if values.ndim != 1 or len(values) == 0:
    raise ValueError(
      "Threshold grid must be a non-empty "
      "one-dimensional sequence."
    )

  if not np.isfinite(values).all():
    raise ValueError(
      "Threshold grid values must be finite."
    )

  if ((values < 0.0) | (values > 1.0)).any():
    raise ValueError(
      "Threshold grid values must be between 0 and 1."
    )

  return values


def select_f1_decision_threshold(
  target,
  probability,
  thresholds=DEFAULT_THRESHOLD_GRID,
) -> dict[str, float]:
  """Select the probability cutoff with the highest validation F1."""
  if len(target) != len(probability):
    raise ValueError(
      "Target and probability must contain the same number of rows."
    )

  if len(target) == 0:
    raise ValueError(
      "Decision-threshold selection requires non-empty data."
    )

  probability_values = validate_probabilities(probability)
  threshold_values = validate_threshold_grid(thresholds)

  candidates = []

  for threshold in threshold_values:
    prediction = (
      probability_values >= threshold
    ).astype(int)

    candidates.append({
      "decision_threshold": float(threshold),
      "validation_f1": float(
        f1_score(
          target,
          prediction,
          zero_division=0,
        )
      ),
    })

  # Prefer the larger cutoff on an exact F1 tie to reduce false positives.
  return max(
    candidates,
    key=lambda result: (
      result["validation_f1"],
      result["decision_threshold"],
    ),
  )


def apply_decision_threshold(
  probability,
  threshold: float,
) -> np.ndarray:
  """Convert positive-class probabilities into binary predictions."""
  if not 0.0 <= threshold <= 1.0:
    raise ValueError(
      "Decision threshold must be between 0 and 1."
    )

  probability_values = validate_probabilities(probability)

  return (
    probability_values >= threshold
  ).astype(int)


def evaluate_at_best_f1_threshold(
  target,
  probability,
  thresholds=DEFAULT_THRESHOLD_GRID,
) -> tuple[dict[str, float | None], float]:
  """Select a validation cutoff and evaluate its predictions."""
  probability_values = validate_probabilities(probability)

  threshold_result = select_f1_decision_threshold(
    target=target,
    probability=probability_values,
    thresholds=thresholds,
  )

  decision_threshold = threshold_result[
    "decision_threshold"
  ]

  prediction = apply_decision_threshold(
    probability=probability_values,
    threshold=decision_threshold,
  )

  scores = calculate_classification_metrics(
    target=target,
    prediction=prediction,
    probability=probability_values,
  )

  return scores, decision_threshold
