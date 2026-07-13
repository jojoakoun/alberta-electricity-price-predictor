import pandas as pd
import pytest

from electricity_predictor.modeling.regression.final_test_evaluation import (
  build_final_test_result,
  evaluate_selected_regression_model,
  get_optional_int_parameter,
  parse_model_parameters,
  train_selected_regression_model,
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


def test_parse_model_parameters_returns_key_value_pairs() -> None:
  parameters = parse_model_parameters(
    "best_alpha=10.0; max_iter=10000; cv_splits=3; cv_mae=83.5"
  )

  assert parameters["best_alpha"] == "10.0"
  assert parameters["max_iter"] == "10000"
  assert parameters["cv_splits"] == "3"
  assert parameters["cv_mae"] == "83.5"


def test_get_optional_int_parameter_handles_none_string() -> None:
  parameters = {"max_depth": "None"}

  result = get_optional_int_parameter(
    parameters=parameters,
    names=["max_depth"],
    default=20,
  )

  assert result is None


def test_evaluate_selected_regression_model_returns_test_scores() -> None:
  data = make_regression_data()
  selected_model = {
    "model_name": "linear_regression",
    "horizon_hours": 1,
    "model_parameters": "fit_intercept=True",
  }

  scores = evaluate_selected_regression_model(
    selected_model=selected_model,
    train_data=data.iloc[:6],
    evaluation_data=data.iloc[6:],
    target_column="actual_price_target_1h",
  )

  assert set(scores.keys()) == {"mae", "rmse"}
  assert scores["mae"] >= 0
  assert scores["rmse"] >= 0


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
  scores = evaluate_selected_regression_model(
    selected_model=selected_model,
    train_data=data.iloc[0:0],
    evaluation_data=data,
    target_column="actual_price_target_1h",
  )

  assert set(scores.keys()) == {"mae", "rmse"}


def test_evaluate_selected_regression_model_rejects_unknown_model() -> None:
  data = make_regression_data()
  selected_model = {
    "model_name": "gradient_boosting",
    "horizon_hours": 1,
    "model_parameters": "",
  }

  with pytest.raises(ValueError, match="Unsupported selected regression model"):
    evaluate_selected_regression_model(
      selected_model=selected_model,
      train_data=data,
      evaluation_data=data,
      target_column="actual_price_target_1h",
    )


def test_train_selected_regression_model_applies_tuned_ridge_alpha() -> None:
  data = make_regression_data()
  selected_model = {
    "model_name": "ridge_regression_tuned",
    "model_parameters": "best_alpha=100.0; cv_splits=3; cv_mae=54.8; cv_rmse=107.4",
  }

  model = train_selected_regression_model(
    selected_model=selected_model,
    train_data=data,
    target_column="actual_price_target_1h",
  )

  # The retrained model must carry the selected alpha, not the default 1.0.
  assert model.alpha == 100.0


def test_train_selected_regression_model_rejects_tuned_model_without_tuned_parameters() -> None:
  data = make_regression_data()
  selected_model = {
    "model_name": "ridge_regression_tuned",
    "model_parameters": "cv_splits=3",
  }

  with pytest.raises(ValueError, match="missing required parameters"):
    train_selected_regression_model(
      selected_model=selected_model,
      train_data=data,
      target_column="actual_price_target_1h",
    )
