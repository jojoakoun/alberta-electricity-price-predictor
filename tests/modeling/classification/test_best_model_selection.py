from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.classification.best_model_selection import (
  add_selection_metadata,
  load_model_results,
  select_best_classification_models_by_horizon,
  validate_selection_metric,
)


def make_results() -> pd.DataFrame:
  """Create classification and regression rows for selection tests."""
  return pd.DataFrame([
    {
      "model_name": "logistic_regression",
      "task": "classification",
      "horizon_hours": 1,
      "split": "validation",
      "accuracy": 0.90,
      "precision": 0.60,
      "recall": 0.70,
      "f1": 0.65,
      "model_parameters": "C=1.0",
    },
    {
      "model_name": "random_forest_classifier",
      "task": "classification",
      "horizon_hours": 1,
      "split": "validation",
      "accuracy": 0.92,
      "precision": 0.70,
      "recall": 0.75,
      "f1": 0.72,
      "model_parameters": "n_estimators=100",
    },
    {
      "model_name": "logistic_regression",
      "task": "classification",
      "horizon_hours": 3,
      "split": "validation",
      "accuracy": 0.88,
      "precision": 0.50,
      "recall": 0.80,
      "f1": 0.62,
      "model_parameters": "C=1.0",
    },
    {
      "model_name": "naive_baseline",
      "task": "regression",
      "horizon_hours": 1,
      "split": "validation",
      "accuracy": None,
      "precision": None,
      "recall": None,
      "f1": None,
      "model_parameters": "",
    },
  ])


def test_select_best_classification_models_by_horizon():
  selected = select_best_classification_models_by_horizon(
    results=make_results(),
  )

  assert len(selected) == 2
  assert selected[0]["model_name"] == "random_forest_classifier"
  assert selected[1]["model_name"] == "logistic_regression"


def test_add_selection_metadata_uses_highest_f1_rule():
  selected = add_selection_metadata(
    selected_model=make_results().iloc[0].to_dict(),
  )

  assert selected["selection_metric"] == "f1"
  assert selected["selection_rule"] == (
    "highest_validation_f1_within_horizon"
  )


def test_validate_selection_metric_rejects_regression_metric():
  with pytest.raises(ValueError, match="Selection metric"):
    validate_selection_metric("mae")


def test_load_model_results_rejects_missing_file(
  tmp_path: Path,
):
  with pytest.raises(FileNotFoundError):
    load_model_results(tmp_path / "missing.csv")
