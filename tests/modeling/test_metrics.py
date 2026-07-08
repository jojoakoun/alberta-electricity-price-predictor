import pandas as pd

from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)


def test_mean_absolute_error_value_calculates_average_absolute_error():
  target = pd.Series([60.0, 80.0, 70.0])
  prediction = pd.Series([55.0, 60.0, 80.0])

  result = mean_absolute_error_value(target, prediction)

  # Absolute errors are 5, 20, and 10. The average is 11.6667.
  assert round(result, 2) == 11.67


def test_root_mean_squared_error_value_penalizes_larger_errors():
  target = pd.Series([60.0, 80.0, 70.0])
  prediction = pd.Series([55.0, 60.0, 80.0])

  result = root_mean_squared_error_value(target, prediction)

  # Squared errors are 25, 400, and 100. The square root of their average is 13.2288.
  assert round(result, 2) == 13.23