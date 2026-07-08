from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.regression.best_model_selection import (
  DEFAULT_SELECTION_METRIC,
  add_selection_metadata,
  filter_validation_regression_results,
  load_model_results,
  select_best_regression_model,
  write_best_regression_model,
)


def make_model_results() -> pd.DataFrame:
  """Create mixed model results for selection tests."""
  return pd.DataFrame(
    [
      {
        "model_name": "naive_baseline",
        "task": "regression",
        "split": "test",
        "evaluation_rows": 100,
        "model_parameters": "prediction_column=actual_price_lag_1h",
        "mae": 17.0,
        "rmse": 70.0,
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "notes": "Baseline test row.",
      },
      {
        "model_name": "linear_regression",
        "task": "regression",
        "split": "validation",
        "evaluation_rows": 100,
        "model_parameters": "fit_intercept=True",
        "mae": 13.0,
        "rmse": 42.0,
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "notes": "Linear validation row.",
      },
      {
        "model_name": "random_forest_regressor_tuned",
        "task": "regression",
        "split": "validation",
        "evaluation_rows": 100,
        "model_parameters": "n_estimators=200",
        "mae": 12.5,
        "rmse": 41.8,
        "accuracy": None,
        "precision": None,
        "recall": None,
        "f1": None,
        "notes": "Tuned random forest validation row.",
      },
      {
        "model_name": "logistic_regression",
        "task": "classification",
        "split": "validation",
        "evaluation_rows": 100,
        "model_parameters": "class_weight=balanced",
        "mae": None,
        "rmse": None,
        "accuracy": 0.8,
        "precision": 0.7,
        "recall": 0.6,
        "f1": 0.65,
        "notes": "Classification row.",
      },
    ]
  )


def test_load_model_results_rejects_missing_file() -> None:
  with pytest.raises(FileNotFoundError):
    load_model_results(Path("missing_model_results.csv"))


def test_filter_validation_regression_results_keeps_only_validation_regression_rows() -> None:
  results = make_model_results()

  filtered_results = filter_validation_regression_results(results)

  # The test baseline row and classification row should not be used for regression selection.
  assert filtered_results["model_name"].tolist() == [
    "linear_regression",
    "random_forest_regressor_tuned",
  ]


def test_select_best_regression_model_uses_lowest_validation_mae() -> None:
  results = make_model_results()

  best_model = select_best_regression_model(results, metric="mae")

  # The best model is the validation regression row with the lowest MAE.
  assert best_model["model_name"] == "random_forest_regressor_tuned"
  assert best_model["mae"] == 12.5


def test_default_selection_metric_is_mae() -> None:
  assert DEFAULT_SELECTION_METRIC == "mae"


def test_select_best_regression_model_rejects_invalid_metric() -> None:
  results = make_model_results()

  with pytest.raises(ValueError, match="Selection metric must be one of"):
    select_best_regression_model(results, metric="accuracy")


def test_select_best_regression_model_rejects_empty_validation_results() -> None:
  results = pd.DataFrame(
    [
      {
        "model_name": "naive_baseline",
        "task": "regression",
        "split": "test",
        "mae": 17.0,
        "rmse": 70.0,
        "model_parameters": "prediction_column=actual_price_lag_1h",
      }
    ]
  )

  with pytest.raises(ValueError, match="No validation regression results"):
    select_best_regression_model(results)


def test_add_selection_metadata_explains_selection_rule() -> None:
  best_model = {
    "model_name": "random_forest_regressor_tuned",
    "task": "regression",
    "split": "validation",
    "mae": 12.5,
    "rmse": 41.8,
    "model_parameters": "n_estimators=200",
  }

  result = add_selection_metadata(best_model, metric="mae")

  assert result["selection_metric"] == "mae"
  assert result["selection_rule"] == "lowest_validation_mae"
  assert result["selection_reason"] == (
    "Selected because it has the lowest validation MAE among regression models."
  )


def test_write_best_regression_model_creates_one_row_file(tmp_path) -> None:
  best_model = {
    "model_name": "random_forest_regressor_tuned",
    "task": "regression",
    "split": "validation",
    "mae": 12.5,
    "rmse": 41.8,
    "model_parameters": "n_estimators=200",
    "selection_metric": "mae",
    "selection_rule": "lowest_validation_mae",
    "selection_reason": "Selected because it has the lowest validation MAE among regression models.",
  }
  output_path = tmp_path / "best_regression_model.csv"

  written_path = write_best_regression_model(best_model, output_path)

  saved_data = pd.read_csv(written_path)

  assert written_path == output_path
  assert len(saved_data) == 1
  assert saved_data.loc[0, "model_name"] == "random_forest_regressor_tuned"
  assert saved_data.loc[0, "selection_rule"] == "lowest_validation_mae"
