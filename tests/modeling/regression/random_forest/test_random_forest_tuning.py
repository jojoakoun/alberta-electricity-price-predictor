import pandas as pd

from electricity_predictor.modeling.regression.random_forest.random_forest_tuning import (
  RANDOM_FOREST_TUNING_SPLITS,
  build_tuned_random_forest_result,
  evaluate_random_forest_config_with_time_series_cv,
  format_random_forest_parameters,
  tune_random_forest_config,
)


def make_random_forest_tuning_data() -> pd.DataFrame:
  """Create enough chronological rows for TimeSeriesSplit tuning."""
  rows = []

  for hour in range(36):
    rows.append(
      {
        "actual_price": 25.0 + (hour * 0.5),
        "forecast_price": 24.0 + (hour * 0.5),
        "hour": hour % 24,
        "day_of_week": hour % 7,
        "month": 1,
        "is_weekend": 1 if hour % 7 in [5, 6] else 0,
        "actual_price_lag_1h": 24.0 + (hour * 0.5),
        "actual_price_lag_24h": 20.0 + (hour * 0.5),
        "forecast_price_lag_1h": 23.0 + (hour * 0.5),
        "actual_price_rolling_24h_mean": 23.0 + (hour * 0.5),
        "actual_price_rolling_24h_max": 28.0 + (hour * 0.5),
        "actual_price_rolling_7d_mean": 24.0 + (hour * 0.5),
      }
    )

  return pd.DataFrame(rows)


def test_format_random_forest_parameters_returns_readable_string() -> None:
  config = {
    "n_estimators": 100,
    "max_depth": 20,
    "min_samples_leaf": 5,
  }

  parameters = format_random_forest_parameters(
    config=config,
    random_state=42,
  )

  assert parameters == (
    "n_estimators=100; max_depth=20; min_samples_leaf=5; random_state=42; n_jobs=-1"
  )


def test_evaluate_random_forest_config_with_time_series_cv_returns_cv_metrics() -> None:
  data = make_random_forest_tuning_data()
  config = {
    "n_estimators": 5,
    "max_depth": 3,
    "min_samples_leaf": 1,
  }

  scores = evaluate_random_forest_config_with_time_series_cv(
    train_data=data,
    config=config,
    n_splits=3,
  )

  assert set(scores.keys()) == {"cv_mae", "cv_rmse"}
  assert scores["cv_mae"] >= 0
  assert scores["cv_rmse"] >= 0


def test_tune_random_forest_config_returns_best_config_result() -> None:
  data = make_random_forest_tuning_data()

  best_result = tune_random_forest_config(data)

  assert set(best_result.keys()) == {"config", "cv_mae", "cv_rmse"}
  assert set(best_result["config"].keys()) == {
    "n_estimators",
    "max_depth",
    "min_samples_leaf",
  }
  assert best_result["cv_mae"] >= 0
  assert best_result["cv_rmse"] >= 0


def test_build_tuned_random_forest_result_returns_model_summary_row() -> None:
  scores = {
    "mae": 12.5,
    "rmse": 20.0,
  }
  best_config = {
    "n_estimators": 200,
    "max_depth": 20,
    "min_samples_leaf": 5,
  }

  result = build_tuned_random_forest_result(
    scores=scores,
    row_count=8544,
    split="validation",
    best_config=best_config,
    cv_mae=28.49,
    cv_rmse=62.07,
  )

  assert result["model_name"] == "random_forest_regressor_tuned"
  assert result["task"] == "regression"
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8544
  assert result["model_parameters"] == (
    f"n_estimators=200; max_depth=20; min_samples_leaf=5; random_state=42; n_jobs=-1; "
    f"cv_splits={RANDOM_FOREST_TUNING_SPLITS}; "
    "cv_mae=28.490000; cv_rmse=62.070000"
  )
  assert result["mae"] == 12.5
  assert result["rmse"] == 20.0
  assert result["notes"] == (
    "Random Forest parameters selected with TimeSeriesSplit on the chronological train set."
  )
