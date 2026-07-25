import pandas as pd

from electricity_predictor.modeling.regression.hist_gradient_boosting import (
  hist_gradient_boosting_tuning as tuning_module,
)
from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting_tuning import (
  HIST_GRADIENT_BOOSTING_TUNING_SPLITS,
  build_tuned_hist_gradient_boosting_result,
  evaluate_hist_gradient_boosting_config_with_time_series_cv,
  format_hist_gradient_boosting_tuning_parameters,
  tune_hist_gradient_boosting_config,
)


def make_hist_gradient_boosting_tuning_data(row_count: int = 200) -> pd.DataFrame:
  """Create enough chronological rows for TimeSeriesSplit tuning."""
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


def make_small_config(
  learning_rate: float = 0.1,
  max_iter: int = 20,
  max_leaf_nodes: int = 15,
  min_samples_leaf: int = 10,
  l2_regularization: float = 0.0,
) -> dict:
  return {
    "learning_rate": learning_rate,
    "max_iter": max_iter,
    "max_leaf_nodes": max_leaf_nodes,
    "min_samples_leaf": min_samples_leaf,
    "l2_regularization": l2_regularization,
  }


def test_format_hist_gradient_boosting_tuning_parameters_is_stable() -> None:
  parameters = format_hist_gradient_boosting_tuning_parameters(make_small_config())

  assert parameters == (
    "loss=absolute_error; learning_rate=0.1; max_iter=20; "
    "max_leaf_nodes=15; min_samples_leaf=10; l2_regularization=0.0; "
    "early_stopping=False; random_state=42"
  )


def test_evaluate_hist_gradient_boosting_config_returns_cv_metrics() -> None:
  data = make_hist_gradient_boosting_tuning_data()

  scores = evaluate_hist_gradient_boosting_config_with_time_series_cv(
    train_data=data,
    config=make_small_config(),
    n_splits=3,
  )

  assert set(scores) == {"cv_mae", "cv_rmse"}
  assert scores["cv_mae"] >= 0
  assert scores["cv_rmse"] >= 0


def test_tune_hist_gradient_boosting_config_returns_best_result(
  monkeypatch,
) -> None:
  data = make_hist_gradient_boosting_tuning_data()
  configs = [
    make_small_config(learning_rate=0.05),
    make_small_config(learning_rate=0.1),
  ]
  monkeypatch.setattr(
    tuning_module,
    "HIST_GRADIENT_BOOSTING_CONFIGS",
    configs,
  )

  best_result = tune_hist_gradient_boosting_config(data)

  assert set(best_result) == {"config", "cv_mae", "cv_rmse"}
  assert best_result["config"] in configs
  assert best_result["cv_mae"] >= 0
  assert best_result["cv_rmse"] >= 0


def test_build_tuned_hist_gradient_boosting_result_returns_summary_row() -> None:
  best_config = make_small_config(
    learning_rate=0.05,
    max_iter=200,
    max_leaf_nodes=31,
    min_samples_leaf=20,
    l2_regularization=1.0,
  )

  result = build_tuned_hist_gradient_boosting_result(
    scores={"mae": 12.5, "rmse": 20.0},
    row_count=8760,
    split="validation",
    best_config=best_config,
    cv_mae=28.49,
    cv_rmse=62.07,
    horizon_hours=6,
  )

  assert result["model_name"] == "hist_gradient_boosting_regressor_tuned"
  assert result["task"] == "regression"
  assert result["horizon_hours"] == 6
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8760
  assert result["mae"] == 12.5
  assert result["rmse"] == 20.0
  assert result["model_parameters"] == (
    "loss=absolute_error; learning_rate=0.05; max_iter=200; "
    "max_leaf_nodes=31; min_samples_leaf=20; l2_regularization=1.0; "
    "early_stopping=False; random_state=42; "
    f"cv_splits={HIST_GRADIENT_BOOSTING_TUNING_SPLITS}; "
    "cv_mae=28.490000; cv_rmse=62.070000"
  )
  assert result["notes"] == (
    "HistGradientBoosting parameters selected with TimeSeriesSplit on the "
    "chronological train set; internal early stopping remained disabled."
  )
