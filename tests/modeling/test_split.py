import pandas as pd
import pytest
from pathlib import Path
from electricity_predictor.modeling.split import (
  load_training_dataset,
  split_time_series_data,
  validate_split_ratios,
)

def make_sample_time_series_data(row_count: int = 100) -> pd.DataFrame:
  """Create simple ordered hourly data for split tests."""

  # Ordered timestamps let us prove that the split keeps past rows before future rows.
  return pd.DataFrame(
    {
      "datetime_universal_time": pd.date_range(
        start="2024-01-01 00:00:00",
        periods=row_count,
        freq="h",
      ),
      "actual_price": range(row_count),
    }
  )


def test_validate_split_ratios_accepts_ratios_that_sum_to_one():
  # A valid split must allocate 100% of the available data.
  validate_split_ratios(
    train_ratio=0.70,
    validation_ratio=0.15,
    test_ratio=0.15,
  )


def test_validate_split_ratios_rejects_ratios_that_do_not_sum_to_one():
  # Ratios above or below 1.0 would create an invalid evaluation setup.
  with pytest.raises(ValueError, match="must sum to 1.0"):
    validate_split_ratios(
      train_ratio=0.70,
      validation_ratio=0.20,
      test_ratio=0.20,
    )


def test_validate_split_ratios_rejects_zero_or_negative_ratios():
  # Each split must exist so the project can train, tune, and test honestly.
  with pytest.raises(ValueError, match="must be greater than 0"):
    validate_split_ratios(
      train_ratio=0.70,
      validation_ratio=0.30,
      test_ratio=0.00,
    )


def test_split_time_series_data_rejects_empty_dataset():
  empty_data = pd.DataFrame()

  # Empty data cannot produce meaningful train, validation, or test sets.
  with pytest.raises(ValueError, match="Cannot split an empty dataset"):
    split_time_series_data(
      data=empty_data,
      train_ratio=0.70,
      validation_ratio=0.15,
      test_ratio=0.15,
    )


def test_split_time_series_data_creates_expected_split_sizes():
  data = make_sample_time_series_data(row_count=100)

  train_data, validation_data, test_data = split_time_series_data(
    data=data,
    train_ratio=0.70,
    validation_ratio=0.15,
    test_ratio=0.15,
  )

  assert len(train_data) == 70
  assert len(validation_data) == 15
  assert len(test_data) == 15


def test_split_time_series_data_preserves_chronological_order():
  data = make_sample_time_series_data(row_count=100)

  train_data, validation_data, test_data = split_time_series_data(
    data=data,
    train_ratio=0.70,
    validation_ratio=0.15,
    test_ratio=0.15,
  )

  # Train must stay before validation so the model learns only from older data.
  assert (
    train_data["datetime_universal_time"].max()
    < validation_data["datetime_universal_time"].min()
  )

  # Validation must stay before test so the final test represents the newest data.
  assert (
    validation_data["datetime_universal_time"].max()
    < test_data["datetime_universal_time"].min()
  )


def test_split_time_series_data_keeps_oldest_rows_in_train_and_newest_rows_in_test():
  data = make_sample_time_series_data(row_count=100)

  train_data, validation_data, test_data = split_time_series_data(
    data=data,
    train_ratio=0.70,
    validation_ratio=0.15,
    test_ratio=0.15,
  )

  # These checks prove that shuffle=False kept the time-series order intact.
  assert train_data["actual_price"].tolist() == list(range(0, 70))
  assert validation_data["actual_price"].tolist() == list(range(70, 85))
  assert test_data["actual_price"].tolist() == list(range(85, 100))
  

def test_load_training_dataset_rejects_missing_file():
  missing_file = Path("missing_training_dataset.csv")

  with pytest.raises(FileNotFoundError):
    load_training_dataset(missing_file)