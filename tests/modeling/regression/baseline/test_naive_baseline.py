from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  REGRESSION_BASELINE_CONFIGS,
  build_naive_baseline_result,
  build_rule_baseline_result,
  evaluate_naive_baseline,
  evaluate_rule_baseline,
  load_training_dataset,
)


def test_regression_baseline_contract_contains_unique_rules() -> None:
  model_names = [
    config["model_name"]
    for config in REGRESSION_BASELINE_CONFIGS
  ]
  prediction_columns = [
    config["prediction_column"]
    for config in REGRESSION_BASELINE_CONFIGS
  ]

  assert model_names == [
    "naive_baseline",
    "previous_day_baseline",
    "aeso_forecast_baseline",
    "previous_aeso_forecast_baseline",
    "rolling_24h_mean_baseline",
    "rolling_7d_mean_baseline",
  ]
  assert len(model_names) == len(set(model_names))
  assert len(prediction_columns) == len(set(prediction_columns))


def test_evaluate_rule_baseline_uses_requested_prediction_column() -> None:
  data = pd.DataFrame({
    "actual_price": [60.0, 80.0, 70.0],
    "actual_price_lag_1h": [55.0, 60.0, 80.0],
    "actual_price_rolling_24h_mean": [60.0, 70.0, 75.0],
  })

  result = evaluate_rule_baseline(
    data=data,
    prediction_column="actual_price_rolling_24h_mean",
  )

  assert round(result["mae"], 2) == 5.0
  assert round(result["rmse"], 2) == 6.45


def test_evaluate_rule_baseline_rejects_missing_columns() -> None:
  data = pd.DataFrame({"actual_price": [60.0]})

  with pytest.raises(
    ValueError,
    match="Missing baseline prediction column",
  ):
    evaluate_rule_baseline(
      data=data,
      prediction_column="missing_prediction",
    )


def test_evaluate_naive_baseline_preserves_previous_hour_behavior() -> None:
  data = pd.DataFrame({
    "actual_price": [60.0, 80.0, 70.0],
    "actual_price_lag_1h": [55.0, 60.0, 80.0],
  })

  result = evaluate_naive_baseline(data)

  assert round(result["mae"], 2) == 11.67
  assert round(result["rmse"], 2) == 13.23


def test_load_training_dataset_rejects_missing_file() -> None:
  missing_file = Path("missing_training_dataset.csv")

  with pytest.raises(FileNotFoundError):
    load_training_dataset(missing_file)


def test_build_rule_baseline_result_records_explicit_rule() -> None:
  result = build_rule_baseline_result(
    scores={"mae": 12.5, "rmse": 25.0},
    row_count=8760,
    model_name="rolling_24h_mean_baseline",
    prediction_column="actual_price_rolling_24h_mean",
    description="Trailing 24-hour observed-price mean",
    split="validation",
    horizon_hours=6,
  )

  assert result["model_name"] == "rolling_24h_mean_baseline"
  assert result["task"] == "regression"
  assert result["horizon_hours"] == 6
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8760
  assert result["model_parameters"] == (
    "prediction_column=actual_price_rolling_24h_mean"
  )
  assert result["mae"] == 12.5
  assert result["rmse"] == 25.0
  assert result["notes"] == (
    "Trailing 24-hour observed-price mean baseline evaluated on the "
    "chronological validation split."
  )


def test_build_naive_baseline_result_preserves_historical_contract() -> None:
  result = build_naive_baseline_result(
    scores={"mae": 17.92, "rmse": 70.89},
    row_count=8542,
    split="validation",
  )

  assert result["model_name"] == "naive_baseline"
  assert result["task"] == "regression"
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 8542
  assert result["model_parameters"] == (
    "prediction_column=actual_price_lag_1h"
  )
  assert result["mae"] == 17.92
  assert result["rmse"] == 70.89
  assert result["notes"] == (
    "Previous hour price baseline evaluated on the chronological "
    "validation split."
  )
