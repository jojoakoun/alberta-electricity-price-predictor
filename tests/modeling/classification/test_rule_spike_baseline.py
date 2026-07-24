import pandas as pd
import pytest

from electricity_predictor.modeling.classification.baseline.rule_spike_baseline import (
  AESO_FORECAST_BASELINE_NAME,
  AESO_FORECAST_COLUMN,
  PREVIOUS_DAY_BASELINE_NAME,
  PREVIOUS_DAY_PRICE_COLUMN,
  build_rule_spike_baseline_result,
  evaluate_rule_spike_baseline,
  predict_spikes_from_price_column,
)


def test_predict_spikes_from_price_column_uses_selected_signal():
  data = pd.DataFrame({
    "forecast_price": [100.0, 170.77, 200.0],
  })

  prediction = predict_spikes_from_price_column(
    data=data,
    price_column="forecast_price",
    threshold=170.77,
  )

  assert prediction.tolist() == [0, 0, 1]


def test_predict_spikes_from_price_column_rejects_missing_column():
  data = pd.DataFrame({
    "actual_price": [10.0, 20.0],
  })

  with pytest.raises(
    ValueError,
    match="Missing baseline price column",
  ):
    predict_spikes_from_price_column(
      data=data,
      price_column="forecast_price",
      threshold=170.77,
    )


def test_evaluate_rule_spike_baseline_returns_expected_metrics():
  data = pd.DataFrame({
    "actual_price_lag_24h": [200.0, 180.0, 50.0, 40.0],
    "is_spike_target_6h": [1, 0, 1, 0],
  })

  scores = evaluate_rule_spike_baseline(
    data=data,
    target_column="is_spike_target_6h",
    price_column="actual_price_lag_24h",
    threshold=170.77,
  )

  assert scores["accuracy"] == pytest.approx(0.5)
  assert scores["precision"] == pytest.approx(0.5)
  assert scores["recall"] == pytest.approx(0.5)
  assert scores["f1"] == pytest.approx(0.5)


def test_build_aeso_baseline_result_uses_shared_schema():
  result = build_rule_spike_baseline_result(
    model_name=AESO_FORECAST_BASELINE_NAME,
    price_column=AESO_FORECAST_COLUMN,
    scores={
      "accuracy": 0.90,
      "precision": 0.80,
      "recall": 0.70,
      "f1": 0.75,
    },
    row_count=100,
    horizon_hours=3,
    threshold=170.77,
  )

  assert result["model_name"] == AESO_FORECAST_BASELINE_NAME
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 3
  assert result["f1"] == pytest.approx(0.75)
  assert "prediction_column=forecast_price" in (
    result["model_parameters"]
  )


def test_build_previous_day_baseline_result_uses_expected_column():
  result = build_rule_spike_baseline_result(
    model_name=PREVIOUS_DAY_BASELINE_NAME,
    price_column=PREVIOUS_DAY_PRICE_COLUMN,
    scores={
      "accuracy": 0.85,
      "precision": 0.65,
      "recall": 0.60,
      "f1": 0.62,
    },
    row_count=100,
    horizon_hours=24,
    threshold=170.77,
  )

  assert result["model_name"] == PREVIOUS_DAY_BASELINE_NAME
  assert "prediction_column=actual_price_lag_24h" in (
    result["model_parameters"]
  )
