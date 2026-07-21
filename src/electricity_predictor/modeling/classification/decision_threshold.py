"""Select and apply a classification probability decision threshold."""

import numpy as np
from sklearn.metrics import f1_score


DEFAULT_THRESHOLD_GRID = np.arange(0.05, 1.00, 0.05)


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
    raise ValueError("Decision-threshold selection requires non-empty data.")

  candidates = []

  for threshold in thresholds:
    prediction = (np.asarray(probability) >= threshold).astype(int)

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

  # Prefer the larger cutoff when F1 ties to reduce false-positive pressure.
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
    raise ValueError("Decision threshold must be between 0 and 1.")

  return (np.asarray(probability) >= threshold).astype(int)
