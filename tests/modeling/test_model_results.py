import pandas as pd

from electricity_predictor.modeling.model_results import (
  MODEL_RESULT_COLUMNS,
  append_model_result,
  build_model_result_row,
  write_model_results,
)


def test_build_model_result_row_fills_regression_metrics():
  result = build_model_result_row(
    model_name="naive_baseline",
    task="regression",
    split="test",
    evaluation_rows=8542,
    metrics={
      "mae": 17.92,
      "rmse": 70.89,
    },
    model_parameters="prediction_column=actual_price_lag_1h",
    notes="Previous hour price baseline",
  )

  assert result["model_name"] == "naive_baseline"
  assert result["task"] == "regression"
  assert result["split"] == "test"
  assert result["evaluation_rows"] == 8542
  assert result["model_parameters"] == "prediction_column=actual_price_lag_1h"
  assert result["mae"] == 17.92
  assert result["rmse"] == 70.89

  # Classification metrics stay empty for regression models.
  assert result["accuracy"] is None
  assert result["precision"] is None
  assert result["recall"] is None
  assert result["f1"] is None


def test_build_model_result_row_fills_classification_metrics():
  result = build_model_result_row(
    model_name="logistic_regression",
    task="classification",
    split="validation",
    evaluation_rows=1000,
    metrics={
      "accuracy": 0.85,
      "precision": 0.80,
      "recall": 0.75,
      "f1": 0.77,
    },
    model_parameters="class_weight=balanced",
    notes="First classification model",
  )

  assert result["model_name"] == "logistic_regression"
  assert result["task"] == "classification"
  assert result["model_parameters"] == "class_weight=balanced"
  assert result["accuracy"] == 0.85
  assert result["precision"] == 0.80
  assert result["recall"] == 0.75
  assert result["f1"] == 0.77

  # Regression metrics stay empty for classification models.
  assert result["mae"] is None
  assert result["rmse"] is None


def test_append_model_result_creates_results_file(tmp_path):
  output_path = tmp_path / "model_results.csv"

  result = build_model_result_row(
    model_name="naive_baseline",
    task="regression",
    split="test",
    evaluation_rows=8542,
    metrics={
      "mae": 17.92,
      "rmse": 70.89,
    },
  )

  written_path = append_model_result(result, output_path)

  assert written_path == output_path
  assert output_path.exists()

  saved_data = pd.read_csv(output_path)

  assert saved_data.columns.tolist() == MODEL_RESULT_COLUMNS
  assert len(saved_data) == 1
  assert saved_data.loc[0, "model_name"] == "naive_baseline"

  # Empty CSV fields are read back by pandas as NaN.
  assert pd.isna(saved_data.loc[0, "model_parameters"])

  assert saved_data.loc[0, "mae"] == 17.92
  assert saved_data.loc[0, "rmse"] == 70.89


def test_append_model_result_keeps_existing_results(tmp_path):
  output_path = tmp_path / "model_results.csv"

  first_result = build_model_result_row(
    model_name="naive_baseline",
    task="regression",
    split="test",
    evaluation_rows=8542,
    metrics={
      "mae": 17.92,
      "rmse": 70.89,
    },
  )

  second_result = build_model_result_row(
    model_name="linear_regression",
    task="regression",
    split="validation",
    evaluation_rows=8541,
    metrics={
      "mae": 15.00,
      "rmse": 60.00,
    },
  )

  append_model_result(first_result, output_path)
  append_model_result(second_result, output_path)

  saved_data = pd.read_csv(output_path)

  # The summary file should keep earlier evaluations and append the new one.
  assert len(saved_data) == 2
  assert saved_data["model_name"].tolist() == [
    "naive_baseline",
    "linear_regression",
  ]

def test_write_model_results_rebuilds_summary_file(tmp_path):
  output_path = tmp_path / "model_results.csv"

  old_result = build_model_result_row(
    model_name="old_model",
    task="regression",
    split="validation",
    evaluation_rows=10,
    metrics={
      "mae": 99.0,
      "rmse": 100.0,
    },
  )

  new_result = build_model_result_row(
    model_name="linear_regression",
    task="regression",
    split="validation",
    evaluation_rows=8541,
    metrics={
      "mae": 12.99,
      "rmse": 42.64,
    },
  )

  append_model_result(old_result, output_path)
  written_path = write_model_results([new_result], output_path)

  saved_data = pd.read_csv(output_path)

  assert written_path == output_path

  # A fresh summary should replace older rows instead of appending duplicates.
  assert len(saved_data) == 1
  assert saved_data.loc[0, "model_name"] == "linear_regression"
  assert saved_data.loc[0, "mae"] == 12.99
  assert saved_data.loc[0, "rmse"] == 42.64

