import numpy as np
import pandas as pd


def mean_absolute_error_value(target: pd.Series, prediction: pd.Series) -> float:
  """Calculate the average absolute error between actual and predicted values."""
  errors = target - prediction

  # Absolute errors prevent positive and negative errors from cancelling each other.
  absolute_errors = errors.abs()

  return float(absolute_errors.mean())


def root_mean_squared_error_value(target: pd.Series, prediction: pd.Series) -> float:
  """Calculate RMSE to penalize large prediction errors more strongly."""
  errors = target - prediction

  # Squaring makes large errors count more than small errors.
  squared_errors = errors ** 2

  return float(np.sqrt(squared_errors.mean()))