from unittest.mock import patch

import pandas as pd

from electricity_predictor.modeling.regression.final_test_evaluation import (
  build_final_test_result,
  evaluate_selected_regression_model,
)


def make_regression_data() -> pd.DataFrame:
  """Create complete regression rows for final-evaluation tests."""
  rows = []

  for hour in range(8):
    rows.append(
      {
        "actual_price": 30.0 + hour,
        "actual_price_target_1h": 31.0 + hour,
        "forecast_price": 29.0 + hour,
        "hour": hour,
        "day_of_week": hour % 7,
        "month": 1,
        "is_weekend": 1 if hour % 7 in [5, 6] else 0,
        "actual_price_lag_1h": 29.0 + hour,
        "actual_price_lag_24h": 25.0 + hour,
        "forecast_price_lag_1h": 28.0 + hour,
        "actual_price_rolling_24h_mean": 27.0 + hour,
        "actual_price_rolling_24h_max": 35.0 + hour,
        "actual_price_rolling_7d_mean": 26.0 + hour,
      }
    )

  return pd.DataFrame(rows)


def test_evaluate_selected_regression_model_returns_test_scores() -> None:
  data = make_regression_data()
  selected_model = {
    "model_name": "linear_regression",
    "horizon_hours": 1,
    "model_parameters": "fit_intercept=True",
  }

  evaluation_data = data.iloc[6:]
  predictions = evaluation_data["actual_price_target_1h"].copy()

  with patch(
    "electricity_predictor.modeling.regression.final_test_evaluation."
    "train_selected_regression_model",
    return_value=object(),
  ) as train_model, patch(
    "electricity_predictor.modeling.regression.final_test_evaluation."
    "predict_selected_regression_model",
    return_value=predictions,
  ) as predict_model:
    scores = evaluate_selected_regression_model(
      selected_model=selected_model,
      train_data=data.iloc[:6],
      evaluation_data=evaluation_data,
      target_column="actual_price_target_1h",
    )

  assert set(scores.keys()) == {"mae", "rmse"}
  assert scores == {"mae": 0.0, "rmse": 0.0}
  train_model.assert_called_once()
  predict_model.assert_called_once()


def test_build_final_test_result_uses_test_split_and_horizon() -> None:
  selected_model = {
    "model_name": "lasso_regression_tuned",
    "horizon_hours": 24,
    "model_parameters": "best_alpha=10.0; max_iter=10000",
  }

  result = build_final_test_result(
    selected_model=selected_model,
    scores={"mae": 12.5, "rmse": 25.0},
    row_count=8541,
  )

  assert result["model_name"] == "lasso_regression_tuned"
  assert result["task"] == "regression"
  assert result["horizon_hours"] == 24
  assert result["split"] == "test"
  assert result["evaluation_rows"] == 8541
  assert result["mae"] == 12.5
  assert result["rmse"] == 25.0
  assert result["notes"] == (
    "Final protected test evaluation after validation selection for the 24h horizon."
  )

def test_evaluate_selected_regression_model_uses_baseline_without_training() -> None:
  data = make_regression_data()
  selected_model = {
    "model_name": "naive_baseline",
    "horizon_hours": 1,
    "model_parameters": "prediction_column=actual_price_lag_1h",
  }

  # Empty train data proves the baseline path never trains anything:
  # any attempt to fit a model on zero rows would raise.
  with patch(
    "electricity_predictor.modeling.regression.final_test_evaluation."
    "train_selected_regression_model"
  ) as train_model:
    scores = evaluate_selected_regression_model(
      selected_model=selected_model,
      train_data=data.iloc[0:0],
      evaluation_data=data,
      target_column="actual_price_target_1h",
    )

  assert set(scores.keys()) == {"mae", "rmse"}
  train_model.assert_not_called()
