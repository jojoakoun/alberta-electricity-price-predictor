import pandas as pd
from sklearn.linear_model import LinearRegression

from electricity_predictor.modeling.regression.feature_columns import REGRESSION_FEATURE_COLUMNS
from electricity_predictor.modeling.regression.linear.linear_regression import (
  build_linear_regression_result,
  evaluate_linear_regression_model,
  train_linear_regression_model,
)


def make_regression_training_data() -> pd.DataFrame:
  """Create simple complete regression data for model tests."""
  data = pd.DataFrame({
    "actual_price": [30.0, 40.0, 50.0, 60.0],
    "actual_price_target_1h": [40.0, 50.0, 60.0, 70.0],
    "actual_price_target_3h": [60.0, 70.0, 80.0, 90.0],
    "forecast_price": [28.0, 38.0, 48.0, 58.0],
    "hour": [0, 1, 2, 3],
    "day_of_week": [0, 0, 0, 0],
    "month": [1, 1, 1, 1],
    "is_weekend": [0, 0, 0, 0],
    "actual_price_lag_1h": [25.0, 30.0, 40.0, 50.0],
    "actual_price_lag_24h": [20.0, 30.0, 40.0, 50.0],
    "forecast_price_lag_1h": [24.0, 28.0, 38.0, 48.0],
    "actual_price_rolling_24h_mean": [22.0, 28.0, 36.0, 46.0],
    "actual_price_rolling_24h_max": [30.0, 35.0, 45.0, 55.0],
    "actual_price_rolling_7d_mean": [21.0, 27.0, 35.0, 45.0],
  })

  return data


def test_train_linear_regression_model_returns_fitted_model():
  data = make_regression_training_data()

  model = train_linear_regression_model(
    train_data=data,
    target_column="actual_price_target_1h",
  )

  assert isinstance(model, LinearRegression)

  # A fitted Linear Regression model stores one coefficient per input feature.
  assert len(model.coef_) == len(REGRESSION_FEATURE_COLUMNS)


def test_evaluate_linear_regression_model_returns_mae_and_rmse():
  data = make_regression_training_data()
  model = train_linear_regression_model(
    train_data=data,
    target_column="actual_price_target_1h",
  )

  scores = evaluate_linear_regression_model(
    model=model,
    evaluation_data=data,
    target_column="actual_price_target_1h",
  )

  assert "mae" in scores
  assert "rmse" in scores
  assert scores["mae"] >= 0
  assert scores["rmse"] >= 0


def test_linear_regression_can_train_on_different_horizon_targets():
  data = make_regression_training_data()

  model_1h = train_linear_regression_model(
    train_data=data,
    target_column="actual_price_target_1h",
  )
  model_3h = train_linear_regression_model(
    train_data=data,
    target_column="actual_price_target_3h",
  )

  scores_1h = evaluate_linear_regression_model(
    model=model_1h,
    evaluation_data=data,
    target_column="actual_price_target_1h",
  )
  scores_3h = evaluate_linear_regression_model(
    model=model_3h,
    evaluation_data=data,
    target_column="actual_price_target_3h",
  )

  # Both horizons should produce valid regression metrics.
  assert scores_1h["mae"] >= 0
  assert scores_3h["mae"] >= 0


def test_build_linear_regression_result_returns_model_summary_row():
  scores = {
    "mae": 12.99,
    "rmse": 42.64,
  }

  result = build_linear_regression_result(
    scores=scores,
    row_count=8541,
    split="validation",
    horizon_hours=3,
  )

  assert result["model_name"] == "linear_regression"
  assert result["task"] == "regression"
  assert result["horizon_hours"] == 3
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8541
  assert result["mae"] == 12.99
  assert result["rmse"] == 42.64
  assert result["notes"] == "Linear Regression trained on the chronological train set."
