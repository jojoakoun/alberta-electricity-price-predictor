from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.regression.baseline import (
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
