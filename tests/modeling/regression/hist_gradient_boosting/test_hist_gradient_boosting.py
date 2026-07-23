import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting import (
  HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
  HIST_GRADIENT_BOOSTING_LEARNING_RATE,
  HIST_GRADIENT_BOOSTING_LOSS,
  HIST_GRADIENT_BOOSTING_MAX_ITER,
  HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
  HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
  HIST_GRADIENT_BOOSTING_RANDOM_STATE,
  build_hist_gradient_boosting_result,
  evaluate_hist_gradient_boosting_model,
  format_hist_gradient_boosting_parameters,
  train_hist_gradient_boosting_model,
)


def make_hist_gradient_boosting_data(row_count: int = 96) -> pd.DataFrame:
  """Create chronological rows containing every shared regression feature."""
  rows = []

  for hour_index in range(row_count):
    base_price = 25.0 + (hour_index * 0.4)
    rows.append(
      {
        "actual_price": base_price + ((hour_index % 6) * 0.25),
        "forecast_price": base_price - 1.0,
        "hour": hour_index % 24,
        "day_of_week": hour_index % 7,
        "month": 1,
        "is_weekend": 1 if hour_index % 7 in [5, 6] else 0,
        "actual_price_lag_1h": base_price - 0.4,
        "actual_price_lag_24h": base_price - 9.6,
        "forecast_price_lag_1h": base_price - 1.4,
        "actual_price_rolling_24h_mean": base_price - 4.8,
        "actual_price_rolling_24h_max": base_price + 2.0,
        "actual_price_rolling_7d_mean": base_price - 8.0,
      }
    )

  return pd.DataFrame(rows)


def test_train_hist_gradient_boosting_model_returns_fitted_model() -> None:
  data = make_hist_gradient_boosting_data()

  model = train_hist_gradient_boosting_model(data)

  assert isinstance(model, HistGradientBoostingRegressor)
  assert model.loss == HIST_GRADIENT_BOOSTING_LOSS
  assert model.learning_rate == HIST_GRADIENT_BOOSTING_LEARNING_RATE
  assert model.max_iter == HIST_GRADIENT_BOOSTING_MAX_ITER
  assert model.max_leaf_nodes == HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES
  assert model.min_samples_leaf == HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF
  assert model.l2_regularization == HIST_GRADIENT_BOOSTING_L2_REGULARIZATION
  assert model.early_stopping is HIST_GRADIENT_BOOSTING_EARLY_STOPPING
  assert model.random_state == HIST_GRADIENT_BOOSTING_RANDOM_STATE


def test_evaluate_hist_gradient_boosting_model_returns_metrics() -> None:
  data = make_hist_gradient_boosting_data()
  model = train_hist_gradient_boosting_model(data)

  scores = evaluate_hist_gradient_boosting_model(model, data)

  assert set(scores) == {"mae", "rmse"}
  assert scores["mae"] >= 0
  assert scores["rmse"] >= 0


def test_format_hist_gradient_boosting_parameters_is_stable() -> None:
  parameters = format_hist_gradient_boosting_parameters()

  assert parameters == (
    "loss=absolute_error; learning_rate=0.1; max_iter=100; "
    "max_leaf_nodes=31; min_samples_leaf=20; l2_regularization=0.0; "
    "early_stopping=False; random_state=42"
  )


def test_build_hist_gradient_boosting_result_returns_summary_row() -> None:
  result = build_hist_gradient_boosting_result(
    scores={"mae": 12.5, "rmse": 20.0},
    row_count=8760,
    split="validation",
    horizon_hours=6,
  )

  assert result["model_name"] == "hist_gradient_boosting_regressor"
  assert result["task"] == "regression"
  assert result["horizon_hours"] == 6
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8760
  assert result["mae"] == 12.5
  assert result["rmse"] == 20.0
  assert "loss=absolute_error" in result["model_parameters"]
  assert "early_stopping=False" in result["model_parameters"]
  assert result["notes"] == (
    "HistGradientBoostingRegressor trained on the chronological train set "
    "with internal early stopping disabled."
  )
