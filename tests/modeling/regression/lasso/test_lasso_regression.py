import pandas as pd
from sklearn.linear_model import Lasso

from electricity_predictor.modeling.regression.lasso.lasso_regression import (
  LASSO_ALPHA,
  LASSO_MAX_ITER,
  build_lasso_regression_result,
  evaluate_lasso_regression_model,
  train_lasso_regression_model,
)


def make_regression_training_data() -> pd.DataFrame:
  return pd.DataFrame(
    {
      "actual_price": [25.0, 30.0, 35.0, 40.0],
      "forecast_price": [24.0, 31.0, 34.0, 39.0],
      "hour": [1, 2, 3, 4],
      "day_of_week": [0, 0, 0, 0],
      "month": [1, 1, 1, 1],
      "is_weekend": [0, 0, 0, 0],
      "actual_price_lag_1h": [24.0, 25.0, 30.0, 35.0],
      "actual_price_lag_24h": [20.0, 22.0, 24.0, 26.0],
      "forecast_price_lag_1h": [23.0, 24.0, 31.0, 34.0],
      "actual_price_rolling_24h_mean": [23.0, 25.0, 28.0, 31.0],
      "actual_price_rolling_24h_max": [28.0, 30.0, 35.0, 40.0],
      "actual_price_rolling_7d_mean": [24.0, 26.0, 29.0, 32.0],
    }
  )


def test_train_lasso_regression_model_returns_fitted_model() -> None:
  data = make_regression_training_data()

  model = train_lasso_regression_model(data)

  assert isinstance(model, Lasso)
  assert model.alpha == LASSO_ALPHA
  assert model.max_iter == LASSO_MAX_ITER


def test_evaluate_lasso_regression_model_returns_mae_and_rmse() -> None:
  data = make_regression_training_data()
  model = train_lasso_regression_model(data)

  scores = evaluate_lasso_regression_model(model, data)

  assert set(scores.keys()) == {"mae", "rmse"}
  assert scores["mae"] >= 0
  assert scores["rmse"] >= 0


def test_build_lasso_regression_result_returns_model_summary_row() -> None:
  scores = {"mae": 12.5, "rmse": 20.0}

  result = build_lasso_regression_result(
    scores=scores,
    row_count=8544,
    split="validation",
  )

  assert result["model_name"] == "lasso_regression"
  assert result["model_parameters"] == "alpha=1.0; max_iter=10000"
  assert result["mae"] == 12.5
  assert result["rmse"] == 20.0
