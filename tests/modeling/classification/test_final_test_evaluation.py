import pytest

from electricity_predictor.modeling.classification.final_test_evaluation import (
  build_confusion_matrix_row,
  evaluate_selected_classification_model,
  build_f1_confidence_interval_row,
  write_confusion_matrices,
  write_confidence_intervals,
  get_float_parameter,
  get_int_parameter,
  get_optional_int_parameter,
  parse_model_parameters,
  select_model_decision_threshold,
  train_selected_classification_model,
  validate_tuned_model_parameters,
)


def test_parse_model_parameters():
  parameters = parse_model_parameters(
    "n_estimators=200; max_depth=None; learning_rate=0.05"
  )

  assert parameters["n_estimators"] == "200"
  assert parameters["max_depth"] == "None"
  assert parameters["learning_rate"] == "0.05"


def test_parameter_helpers_convert_saved_values():
  parameters = {
    "C": "10.0",
    "n_estimators": "200",
    "max_depth": "None",
  }

  assert get_float_parameter(parameters, ["C"], 1.0) == 10.0
  assert get_int_parameter(
    parameters,
    ["n_estimators"],
    100,
  ) == 200
  assert get_optional_int_parameter(
    parameters,
    ["max_depth"],
    5,
  ) is None


def test_validate_tuned_model_parameters_rejects_missing_values():
  with pytest.raises(ValueError, match="missing required parameters"):
    validate_tuned_model_parameters(
      model_name="logistic_regression_tuned",
      parameters={},
    )


def test_build_confusion_matrix_row_returns_binary_counts():
  import pandas as pd

  row = build_confusion_matrix_row(
    selected_model={
      "model_name": "random_forest_classifier_tuned",
      "horizon_hours": 6,
    },
    target=pd.Series([0, 0, 1, 1]),
    prediction=pd.Series([0, 1, 0, 1]),
  )

  assert row == {
    "model_name": "random_forest_classifier_tuned",
    "horizon_hours": 6,
    "split": "test",
    "true_negative": 1,
    "false_positive": 1,
    "false_negative": 1,
    "true_positive": 1,
  }


def test_write_confusion_matrices_persists_expected_columns(tmp_path):
  import pandas as pd

  output_path = tmp_path / "confusion_matrices.csv"

  written_path = write_confusion_matrices(
    rows=[
      {
        "model_name": "logistic_regression",
        "horizon_hours": 1,
        "split": "test",
        "true_negative": 90,
        "false_positive": 5,
        "false_negative": 3,
        "true_positive": 2,
      }
    ],
    output_path=output_path,
  )

  report = pd.read_csv(written_path)

  assert report.columns.tolist() == [
    "model_name",
    "horizon_hours",
    "split",
    "true_negative",
    "false_positive",
    "false_negative",
    "true_positive",
  ]
  assert report.loc[0, "true_positive"] == 2


def test_select_model_decision_threshold_uses_validation_probabilities(
  monkeypatch,
):
  import numpy as np
  import pandas as pd

  class FakeModel:
    def predict_proba(self, features):
      return np.array([
        [0.9, 0.1],
        [0.6, 0.4],
        [0.4, 0.6],
        [0.1, 0.9],
      ])

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification."
    "final_test_evaluation.train_selected_classification_model",
    lambda **kwargs: FakeModel(),
  )

  validation_data = pd.DataFrame({
    "forecast_price": [1.0] * 4,
    "hour": [1] * 4,
    "day_of_week": [1] * 4,
    "month": [1] * 4,
    "is_weekend": [0] * 4,
    "actual_price_lag_1h": [1.0] * 4,
    "actual_price_lag_24h": [1.0] * 4,
    "forecast_price_lag_1h": [1.0] * 4,
    "actual_price_rolling_24h_mean": [1.0] * 4,
    "actual_price_rolling_24h_max": [1.0] * 4,
    "actual_price_rolling_7d_mean": [1.0] * 4,
    "is_spike_target_1h": [0, 0, 1, 1],
  })

  result = select_model_decision_threshold(
    selected_model={
      "model_name": "logistic_regression",
      "model_parameters": "",
    },
    train_data=validation_data,
    validation_data=validation_data,
    target_column="is_spike_target_1h",
  )

  assert 0.0 <= result["decision_threshold"] <= 1.0
  assert result["validation_f1"] == pytest.approx(1.0)


def test_build_f1_confidence_interval_row_returns_bootstrap_metadata():
  import pandas as pd

  row = build_f1_confidence_interval_row(
    selected_model={
      "model_name": "random_forest_classifier_tuned",
      "horizon_hours": 3,
    },
    target=pd.Series(
      [0, 0, 1, 1] * 10
    ),
    prediction=pd.Series(
      [0, 1, 1, 1] * 10
    ),
  )

  assert row["model_name"] == "random_forest_classifier_tuned"
  assert row["horizon_hours"] == 3
  assert row["metric"] == "f1"
  assert row["confidence_level"] == 0.95
  assert row["block_size"] == 24
  assert row["iterations"] == 1000
  assert 0.0 <= row["ci_lower"] <= row["ci_upper"] <= 1.0


def test_write_confidence_intervals_persists_expected_columns(tmp_path):
  import pandas as pd

  output_path = tmp_path / "confidence_intervals.csv"

  written_path = write_confidence_intervals(
    rows=[
      {
        "model_name": "logistic_regression",
        "horizon_hours": 1,
        "split": "test",
        "metric": "f1",
        "estimate": 0.40,
        "confidence_level": 0.95,
        "ci_lower": 0.30,
        "ci_upper": 0.50,
        "block_size": 24,
        "iterations": 1000,
      }
    ],
    output_path=output_path,
  )

  report = pd.read_csv(written_path)

  assert report.columns.tolist() == [
    "model_name",
    "horizon_hours",
    "split",
    "metric",
    "estimate",
    "confidence_level",
    "ci_lower",
    "ci_upper",
    "block_size",
    "iterations",
  ]
  assert report.loc[0, "ci_upper"] == 0.50


def test_evaluate_selected_classification_model_supports_baseline_path():
  import pandas as pd

  data = pd.DataFrame({
    "actual_price_lag_1h": [50.0, 200.0, 100.0, 300.0],
    "is_spike_target_1h": [0, 1, 0, 1],
  })

  scores, prediction, decision_threshold = (
    evaluate_selected_classification_model(
      selected_model={
        "model_name": "naive_spike_baseline",
        "horizon_hours": 1,
        "model_parameters": "",
      },
      train_data=data,
      validation_data=data,
      evaluation_data=data,
      target_column="is_spike_target_1h",
      threshold=170.77,
    )
  )

  assert prediction.tolist() == [0, 1, 0, 1]
  assert scores["f1"] == pytest.approx(1.0)
  assert decision_threshold is None


def test_train_selected_classification_model_rejects_unknown_model():
  import pandas as pd

  with pytest.raises(
    ValueError,
    match="Unsupported selected classification model",
  ):
    train_selected_classification_model(
      selected_model={
        "model_name": "unknown_classifier",
        "model_parameters": "",
      },
      train_data=pd.DataFrame(),
      target_column="is_spike_target_1h",
    )


def test_train_selected_classification_model_applies_tuned_parameters(
  monkeypatch,
):
  import pandas as pd

  captured = {}

  def fake_train_random_forest_classifier(**kwargs):
    captured.update(kwargs)
    return object()

  monkeypatch.setattr(
    "electricity_predictor.modeling.classification."
    "final_test_evaluation.train_random_forest_classifier",
    fake_train_random_forest_classifier,
  )

  train_selected_classification_model(
    selected_model={
      "model_name": "random_forest_classifier_tuned",
      "model_parameters": (
        "n_estimators=200; "
        "max_depth=10; "
        "min_samples_leaf=5"
      ),
    },
    train_data=pd.DataFrame(),
    target_column="is_spike_target_6h",
  )

  assert captured["n_estimators"] == 200
  assert captured["max_depth"] == 10
  assert captured["min_samples_leaf"] == 5
  assert captured["target_column"] == "is_spike_target_6h"
