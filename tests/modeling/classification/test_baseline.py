import pandas as pd
import pytest

from electricity_predictor.modeling.classification.baseline.naive_spike_baseline import (
  build_classification_baseline_result,
  evaluate_classification_baseline,
  predict_spike_persistence,
)


def test_predict_spike_persistence_uses_previous_hour_price():
  data = pd.DataFrame({
    "actual_price_lag_1h": [50.0, 165.0, 200.0],
  })

  prediction = predict_spike_persistence(
    data=data,
    threshold=165.0,
  )

  assert prediction.tolist() == [0, 0, 1]


def test_predict_spike_persistence_rejects_missing_prediction_column():
  data = pd.DataFrame({
    "actual_price": [10.0, 20.0],
  })

  with pytest.raises(ValueError, match="Missing prediction column"):
    predict_spike_persistence(
      data=data,
      threshold=100.0,
    )


def test_evaluate_classification_baseline_returns_expected_metrics():
  data = pd.DataFrame({
    "actual_price_lag_1h": [200.0, 180.0, 50.0, 40.0],
    "is_spike_target_3h": [1, 0, 1, 0],
  })

  scores = evaluate_classification_baseline(
    data=data,
    target_column="is_spike_target_3h",
    threshold=165.0,
  )

  assert scores["accuracy"] == pytest.approx(0.5)
  assert scores["precision"] == pytest.approx(0.5)
  assert scores["recall"] == pytest.approx(0.5)
  assert scores["f1"] == pytest.approx(0.5)


def test_evaluate_classification_baseline_rejects_missing_target():
  data = pd.DataFrame({
    "actual_price_lag_1h": [50.0, 100.0],
  })

  with pytest.raises(ValueError, match="Missing classification target column"):
    evaluate_classification_baseline(
      data=data,
      target_column="is_spike_target_1h",
      threshold=165.0,
    )


def test_build_classification_baseline_result_uses_shared_schema():
  result = build_classification_baseline_result(
    scores={
      "accuracy": 0.9,
      "precision": 0.8,
      "recall": 0.7,
      "f1": 0.75,
    },
    row_count=100,
    horizon_hours=6,
    threshold=165.0,
  )

  assert result["model_name"] == "naive_spike_baseline"
  assert result["task"] == "classification"
  assert result["horizon_hours"] == 6
  assert result["split"] == "validation"
  assert result["evaluation_rows"] == 100
  assert result["mae"] is None
  assert result["rmse"] is None
  assert result["accuracy"] == 0.9
