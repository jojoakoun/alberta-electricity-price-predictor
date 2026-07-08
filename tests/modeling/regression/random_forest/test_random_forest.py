import pandas as pd
from sklearn.ensemble import RandomForestRegressor

from electricity_predictor.modeling.regression.random_forest.random_forest import (
  RANDOM_FOREST_N_ESTIMATORS,
  RANDOM_FOREST_MAX_DEPTH,
  RANDOM_FOREST_MIN_SAMPLES_LEAF,
  RANDOM_FOREST_RANDOM_STATE,
  build_random_forest_result,
  evaluate_random_forest_model,
  train_random_forest_model,
)


def make_regression_training_data() -> pd.DataFrame:
  """Create a small regression dataset with all required feature columns."""
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


def test_train_random_forest_model_returns_fitted_model() -> None:
  data = make_regression_training_data()

  model = train_random_forest_model(data)

  assert isinstance(model, RandomForestRegressor)
  assert model.n_estimators == RANDOM_FOREST_N_ESTIMATORS
  assert model.max_depth == RANDOM_FOREST_MAX_DEPTH
  assert model.min_samples_leaf == RANDOM_FOREST_MIN_SAMPLES_LEAF
  assert model.random_state == RANDOM_FOREST_RANDOM_STATE


def test_evaluate_random_forest_model_returns_mae_and_rmse() -> None:
  data = make_regression_training_data()
  model = train_random_forest_model(data)

  scores = evaluate_random_forest_model(model, data)

  assert set(scores.keys()) == {"mae", "rmse"}
  assert scores["mae"] >= 0
  assert scores["rmse"] >= 0


def test_build_random_forest_result_returns_model_summary_row() -> None:
  scores = {
    "mae": 12.5,
    "rmse": 20.0,
  }

  result = build_random_forest_result(
    scores=scores,
    row_count=8544,
    split="validation",
  )

  assert result["model_name"] == "random_forest_regressor"
  assert result["task"] == "regression"
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8544
  assert result["model_parameters"] == (
    "n_estimators=100; max_depth=None; min_samples_leaf=1; random_state=42"
  )
  assert result["mae"] == 12.5
  assert result["rmse"] == 20.0
  assert result["notes"] == "Random Forest Regressor trained on the chronological train set."
