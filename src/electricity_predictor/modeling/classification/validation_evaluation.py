"""Evaluate learned classifiers with a validation-selected decision threshold."""

import numpy as np
import pandas as pd

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.decision_threshold import (
  evaluate_at_best_f1_threshold,
)


def extract_positive_class_probability(
  model,
  data: pd.DataFrame,
) -> np.ndarray:
  """Return positive-class probabilities for the official model features."""
  if not hasattr(model, "predict_proba"):
    raise ValueError(
      "Classification model must provide predict_proba."
    )

  probability_matrix = np.asarray(
    model.predict_proba(data[MODEL_FEATURE_COLUMNS]),
    dtype=float,
  )

  if probability_matrix.ndim != 2:
    raise ValueError(
      "predict_proba must return a two-dimensional array."
    )

  if probability_matrix.shape[0] != len(data):
    raise ValueError(
      "predict_proba row count must match evaluation data."
    )

  if probability_matrix.shape[1] < 2:
    raise ValueError(
      "predict_proba must contain the positive class column."
    )

  return probability_matrix[:, 1]


def evaluate_classifier_on_validation(
  model,
  validation_data: pd.DataFrame,
  target_column: str,
) -> tuple[dict[str, float | None], float]:
  """Evaluate one classifier using its best validation F1 cutoff."""
  if target_column not in validation_data.columns:
    raise ValueError(
      f"Missing classification target column: {target_column}"
    )

  probability = extract_positive_class_probability(
    model=model,
    data=validation_data,
  )

  return evaluate_at_best_f1_threshold(
    target=validation_data[target_column],
    probability=probability,
  )


def add_decision_threshold_to_parameters(
  parameter_text: str,
  decision_threshold: float,
) -> str:
  """Persist the validation-selected cutoff in model parameters."""
  base_parameters = (
    parameter_text.strip().strip(";")
    if isinstance(parameter_text, str)
    else ""
  )

  threshold_parameter = (
    f"decision_threshold={decision_threshold:.4f}"
  )

  if not base_parameters:
    return threshold_parameter

  return f"{base_parameters}; {threshold_parameter}"
