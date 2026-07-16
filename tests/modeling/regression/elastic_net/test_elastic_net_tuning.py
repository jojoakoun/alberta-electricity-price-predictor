import pandas as pd

from electricity_predictor.modeling.regression.elastic_net.elastic_net_tuning import (
  ELASTIC_NET_TUNING_SPLITS,
  build_tuned_elastic_net_result,
  evaluate_elastic_net_config_with_time_series_cv,
  format_elastic_net_parameters,
  tune_elastic_net_config,
)


def make_elastic_net_tuning_data() -> pd.DataFrame:
  rows = []

  for hour in range(200):
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


def test_format_elastic_net_parameters_returns_readable_string() -> None:
  config = {"alpha": 0.01, "l1_ratio": 0.5}

  parameters = format_elastic_net_parameters(config)

  assert parameters == "alpha=0.01; l1_ratio=0.5; max_iter=10000"


def test_evaluate_elastic_net_config_with_time_series_cv_returns_cv_metrics() -> None:
  data = make_elastic_net_tuning_data()
  config = {"alpha": 0.01, "l1_ratio": 0.5}

  scores = evaluate_elastic_net_config_with_time_series_cv(
    train_data=data,
    config=config,
    n_splits=3,
  )

  assert set(scores.keys()) == {"cv_mae", "cv_rmse"}
  assert scores["cv_mae"] >= 0
  assert scores["cv_rmse"] >= 0


def test_tune_elastic_net_config_returns_best_config_result() -> None:
  data = make_elastic_net_tuning_data()

  best_result = tune_elastic_net_config(data)

  assert set(best_result.keys()) == {"config", "cv_mae", "cv_rmse"}
  assert set(best_result["config"].keys()) == {"alpha", "l1_ratio"}
  assert best_result["cv_mae"] >= 0
  assert best_result["cv_rmse"] >= 0


def test_build_tuned_elastic_net_result_returns_model_summary_row() -> None:
  scores = {"mae": 12.5, "rmse": 20.0}
  best_config = {"alpha": 0.01, "l1_ratio": 0.5}

  result = build_tuned_elastic_net_result(
    scores=scores,
    row_count=8544,
    split="validation",
    best_config=best_config,
    cv_mae=28.49,
    cv_rmse=62.07,
  )

  assert result["model_name"] == "elastic_net_regression_tuned"
  assert result["model_parameters"] == (
    f"alpha=0.01; l1_ratio=0.5; max_iter=10000; "
    f"cv_splits={ELASTIC_NET_TUNING_SPLITS}; "
    "cv_mae=28.490000; cv_rmse=62.070000"
  )
