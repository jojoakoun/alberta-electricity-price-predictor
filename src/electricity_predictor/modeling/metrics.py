import numpy as np
import pandas as pd
from sklearn.metrics import (
  accuracy_score,
  average_precision_score,
  f1_score,
  precision_score,
  recall_score,
)


def mean_absolute_error_value(
  target: pd.Series,
  prediction: pd.Series,
) -> float:
  """Calculate the average absolute error between actual and predicted values."""
  errors = target - prediction

  # Absolute errors prevent positive and negative errors from cancelling each other.
  absolute_errors = errors.abs()

  return float(absolute_errors.mean())


def root_mean_squared_error_value(
  target: pd.Series,
  prediction: pd.Series,
) -> float:
  """Calculate RMSE to penalize large prediction errors more strongly."""
  errors = target - prediction

  # Squaring makes large errors count more than small errors.
  squared_errors = errors ** 2

  return float(np.sqrt(squared_errors.mean()))


def calculate_classification_metrics(
  target,
  prediction,
  probability=None,
) -> dict[str, float | None]:
  """Calculate reusable binary classification metrics."""
  pr_auc = None

  # PR-AUC requires continuous positive-class scores, not only 0/1 labels.
  if probability is not None:
    pr_auc = float(average_precision_score(target, probability))

  return {
    "accuracy": float(accuracy_score(target, prediction)),
    "precision": float(
      precision_score(
        target,
        prediction,
        zero_division=0,
      )
    ),
    "recall": float(
      recall_score(
        target,
        prediction,
        zero_division=0,
      )
    ),
    "f1": float(
      f1_score(
        target,
        prediction,
        zero_division=0,
      )
    ),
    "pr_auc": pr_auc,
  }
