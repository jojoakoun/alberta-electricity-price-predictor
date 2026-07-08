from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  build_naive_baseline_result,
  evaluate_naive_baseline,
  load_training_dataset,
)


def test_evaluate_naive_baseline_returns_mae_and_rmse():
  data = pd.DataFrame({
    "actual_price": [60.0, 80.0, 70.0],
    "actual_price_lag_1h": [55.0, 60.0, 80.0],
  })

  result = evaluate_naive_baseline(data)

  # This baseline predicts the current price using the previous hour price.
  assert round(result["mae"], 2) == 11.67
  assert round(result["rmse"], 2) == 13.23


def test_load_training_dataset_rejects_missing_file():
  missing_file = Path("missing_training_dataset.csv")

  with pytest.raises(FileNotFoundError):
    load_training_dataset(missing_file)

def test_build_naive_baseline_result_returns_model_summary_row():
  scores = {
    "mae": 17.92,
    "rmse": 70.89,
  }

  result = build_naive_baseline_result(
    scores=scores,
    row_count=8542,
  )

  assert result["model_name"] == "naive_baseline"
  assert result["task"] == "regression"
  assert result["split"] == "test"
  assert result["evaluation_rows"] == 8542
  assert result["model_parameters"] == "prediction_column=actual_price_lag_1h"
  assert result["mae"] == 17.92
  assert result["rmse"] == 70.89
  assert result["notes"] == "Previous hour price baseline evaluated on the chronological test set."

