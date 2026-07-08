import pandas as pd

from electricity_predictor.modeling.regression.ridge.ridge_tuning import (
  RIDGE_TUNING_SPLITS,
  build_tuned_ridge_result,
  evaluate_ridge_alpha_with_time_series_cv,
  tune_ridge_alpha,
)


def make_ridge_tuning_data() -> pd.DataFrame:
  """Create enough chronological rows for TimeSeriesSplit tuning."""
  rows = []

  for hour in range(24):
    rows.append(
      {
        "actual_price": 25.0 + hour,
        "forecast_price": 24.0 + hour,
        "hour": hour % 24,
        "day_of_week": hour % 7,
        "month": 1,
        "is_weekend": 1 if hour % 7 in [5, 6] else 0,
        "actual_price_lag_1h": 24.0 + hour,
        "actual_price_lag_24h": 20.0 + hour,
        "forecast_price_lag_1h": 23.0 + hour,
        "actual_price_rolling_24h_mean": 23.0 + hour,
        "actual_price_rolling_24h_max": 28.0 + hour,
        "actual_price_rolling_7d_mean": 24.0 + hour,
      }
    )

  return pd.DataFrame(rows)


def test_evaluate_ridge_alpha_with_time_series_cv_returns_cv_metrics() -> None:
  data = make_ridge_tuning_data()

  scores = evaluate_ridge_alpha_with_time_series_cv(
    train_data=data,
    alpha=1.0,
    n_splits=3,
  )

  assert set(scores.keys()) == {"cv_mae", "cv_rmse"}
  assert scores["cv_mae"] >= 0
  assert scores["cv_rmse"] >= 0


def test_tune_ridge_alpha_returns_best_alpha_result() -> None:
  data = make_ridge_tuning_data()

  best_result = tune_ridge_alpha(data)

  assert set(best_result.keys()) == {"alpha", "cv_mae", "cv_rmse"}
  assert best_result["alpha"] in [0.1, 1.0, 10.0, 100.0]
  assert best_result["cv_mae"] >= 0
  assert best_result["cv_rmse"] >= 0


def test_build_tuned_ridge_result_returns_model_summary_row() -> None:
  scores = {
    "mae": 12.5,
    "rmse": 20.0,
  }

  result = build_tuned_ridge_result(
    scores=scores,
    row_count=8544,
    split="validation",
    best_alpha=100.0,
    cv_mae=28.49,
    cv_rmse=62.07,
  )

  assert result["model_name"] == "ridge_regression_tuned"
  assert result["task"] == "regression"
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8544
  assert result["model_parameters"] == (
    f"best_alpha=100.0; cv_splits={RIDGE_TUNING_SPLITS}; "
    "cv_mae=28.490000; cv_rmse=62.070000"
  )
  assert result["mae"] == 12.5
  assert result["rmse"] == 20.0
  assert result["notes"] == (
    "Ridge alpha selected with TimeSeriesSplit on the chronological train set."
  )
