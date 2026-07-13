import pandas as pd
import pytest

from electricity_predictor.modeling.classification.target_builder import (
  add_spike_targets,
  build_spike_target_column_name,
  prepare_classification_splits,
)


def make_classification_data(
  actual_prices: list[float],
  target_prices: list[float],
) -> pd.DataFrame:
  """Create synthetic data for classification target tests."""
  return pd.DataFrame({
    "actual_price": actual_prices,
    "actual_price_target_1h": target_prices,
  })


def test_build_spike_target_column_name_uses_horizon():
  assert build_spike_target_column_name(1) == "is_spike_target_1h"
  assert build_spike_target_column_name(24) == "is_spike_target_24h"


def test_add_spike_targets_creates_binary_target_column():
  data = make_classification_data(
    actual_prices=[10.0, 20.0, 30.0],
    target_prices=[40.0, 50.0, 60.0],
  )

  result = add_spike_targets(
    data=data,
    threshold=50.0,
    horizons_hours=[1],
  )

  assert result["is_spike_target_1h"].tolist() == [0, 0, 1]


def test_add_spike_targets_does_not_modify_original_dataframe():
  data = make_classification_data(
    actual_prices=[10.0, 20.0],
    target_prices=[60.0, 70.0],
  )

  result = add_spike_targets(
    data=data,
    threshold=50.0,
    horizons_hours=[1],
  )

  assert "is_spike_target_1h" not in data.columns
  assert "is_spike_target_1h" in result.columns


def test_prepare_classification_splits_uses_train_threshold_for_all_splits():
  train_data = make_classification_data(
    actual_prices=[1.0, 2.0, 3.0, 4.0, 100.0],
    target_prices=[1.0, 2.0, 3.0, 4.0, 100.0],
  )

  validation_data = make_classification_data(
    actual_prices=[1000.0, 1100.0],
    target_prices=[6.0, 8.0],
  )

  test_data = make_classification_data(
    actual_prices=[2000.0, 2100.0],
    target_prices=[7.0, 9.0],
  )

  train, validation, test, threshold = prepare_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=[1],
  )

  assert threshold == pytest.approx(7.0)
  assert train["is_spike_target_1h"].tolist() == [0, 0, 0, 0, 1]
  assert validation["is_spike_target_1h"].tolist() == [0, 1]
  assert test["is_spike_target_1h"].tolist() == [0, 1]


def test_prepare_classification_splits_rejects_missing_price_target():
  data = pd.DataFrame({
    "actual_price": [10.0, 20.0],
  })

  with pytest.raises(ValueError, match="Missing target column"):
    prepare_classification_splits(
      train_data=data,
      validation_data=data,
      test_data=data,
      horizons_hours=[1],
    )
