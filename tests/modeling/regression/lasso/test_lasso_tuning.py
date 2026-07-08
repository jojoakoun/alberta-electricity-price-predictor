import pandas as pd

from electricity_predictor.modeling.regression.lasso.lasso_tuning import (
  LASSO_TUNING_SPLITS,
  build_tuned_lasso_result,
  evaluate_lasso_alpha_with_time_series_cv,
  tune_lasso_alpha,
)


def make_lasso_tuning_data() -> pd.DataFrame:
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


def test_evaluate_lasso_alpha_with_time_series_cv_returns_cv_metrics() -> None:
  data = make_lasso_tuning_data()

  scores = evaluate_lasso_alpha_with_time_series_cv(data, alpha=0.1, n_splits=3)

  assert set(scores.keys()) == {"cv_mae", "cv_rmse"}
  assert scores["cv_mae"] >= 0
  assert scores["cv_rmse"] >= 0


def test_tune_lasso_alpha_returns_best_alpha_result() -> None:
  data = make_lasso_tuning_data()

  best_result = tune_lasso_alpha(data)

  assert set(best_result.keys()) == {"alpha", "cv_mae", "cv_rmse"}
  assert best_result["alpha"] in [0.001, 0.01, 0.1, 1.0, 10.0]
  assert best_result["cv_mae"] >= 0
  assert best_result["cv_rmse"] >= 0


def test_build_tuned_lasso_result_returns_model_summary_row() -> None:
  scores = {"mae": 12.5, "rmse": 20.0}

  result = build_tuned_lasso_result(
    scores=scores,
    row_count=8544,
    split="validation",
    best_alpha=0.1,
    cv_mae=28.49,
    cv_rmse=62.07,
  )

  assert result["model_name"] == "lasso_regression_tuned"
  assert result["model_parameters"] == (
    f"best_alpha=0.1; max_iter=10000; cv_splits={LASSO_TUNING_SPLITS}; "
    "cv_mae=28.490000; cv_rmse=62.070000"
  )
