import pandas as pd
from sklearn.linear_model import Ridge

from electricity_predictor.features.feature_columns import MODEL_FEATURE_COLUMNS
from electricity_predictor.modeling.regression.ridge.ridge_regression import (
  build_ridge_regression_result,
  evaluate_ridge_regression_model,
  train_ridge_regression_model,
)


def make_regression_training_data() -> pd.DataFrame:
  """Create simple complete regression data for model tests."""
  data = pd.DataFrame({
    "actual_price": [30.0, 40.0, 50.0, 60.0],
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


def test_train_ridge_regression_model_returns_fitted_model():
  data = make_regression_training_data()

  model = train_ridge_regression_model(data)

  assert isinstance(model, Ridge)

  # A fitted Ridge model stores one coefficient per input feature.
  assert len(model.coef_) == len(MODEL_FEATURE_COLUMNS)


def test_evaluate_ridge_regression_model_returns_mae_and_rmse():
  data = make_regression_training_data()
  model = train_ridge_regression_model(data)

  scores = evaluate_ridge_regression_model(
    model=model,
    evaluation_data=data,
  )

  assert "mae" in scores
  assert "rmse" in scores
  assert scores["mae"] >= 0
  assert scores["rmse"] >= 0


def test_build_ridge_regression_result_returns_model_summary_row():
  scores = {
    "mae": 12.98,
    "rmse": 42.63,
  }

  result = build_ridge_regression_result(
    scores=scores,
    row_count=8544,
    split="validation",
  )

  assert result["model_name"] == "ridge_regression"
  assert result["task"] == "regression"
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8544
  assert result["model_parameters"] == "alpha=1.0"
  assert result["mae"] == 12.98
  assert result["rmse"] == 42.63
  assert result["notes"] == "Ridge Regression trained on the chronological train set."
