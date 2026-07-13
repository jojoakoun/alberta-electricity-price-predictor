from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.classification.run_classification_models import (
  remove_existing_classification_results,
)


def test_remove_existing_classification_results_preserves_regression_rows(
  tmp_path: Path,
):
  results_path = tmp_path / "model_results.csv"

  results = pd.DataFrame([
    {
      "model_name": "naive_baseline",
      "task": "regression",
      "horizon_hours": 1,
      "split": "validation",
      "evaluation_rows": 100,
      "model_parameters": "",
      "mae": 20.0,
      "rmse": 30.0,
      "accuracy": None,
      "precision": None,
      "recall": None,
      "f1": None,
      "notes": "",
    },
    {
      "model_name": "naive_spike_baseline",
      "task": "classification",
      "horizon_hours": 1,
      "split": "validation",
      "evaluation_rows": 100,
      "model_parameters": "",
      "mae": None,
      "rmse": None,
      "accuracy": 0.90,
      "precision": 0.40,
      "recall": 0.40,
      "f1": 0.40,
      "notes": "",
    },
  ])

  results.to_csv(results_path, index=False)

  remove_existing_classification_results(results_path)

  written_results = pd.read_csv(results_path)

  assert len(written_results) == 1
  assert written_results.iloc[0]["task"] == "regression"
  assert written_results.iloc[0]["model_name"] == "naive_baseline"


def test_remove_existing_classification_results_accepts_missing_file(
  tmp_path: Path,
):
  results_path = tmp_path / "missing_model_results.csv"

  remove_existing_classification_results(results_path)

  assert not results_path.exists()
