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

def test_load_training_dataset_loads_and_sorts_by_utc_time(tmp_path):
  import pandas as pd

  from electricity_predictor.modeling.split import load_training_dataset

  # Deliberately unsorted rows: the shared loader must fix the order itself.
  data = pd.DataFrame({
    "datetime_universal_time": [
      "2026-01-01 10:00:00",
      "2026-01-01 08:00:00",
      "2026-01-01 09:00:00",
    ],
    "actual_price": [3.0, 1.0, 2.0],
  })
  file_path = tmp_path / "training_dataset.csv"
  data.to_csv(file_path, index=False)

  loaded = load_training_dataset(file_path)

  # The loader owns two guarantees: real datetimes and chronological order.
  assert str(loaded["datetime_universal_time"].dtype).startswith("datetime64")
  assert loaded["datetime_universal_time"].is_monotonic_increasing
  assert loaded["actual_price"].tolist() == [1.0, 2.0, 3.0]


def test_split_time_series_data_splits_are_disjoint_and_cover_all_rows():
  import pandas as pd

  from electricity_predictor.modeling.split import split_time_series_data

  data = pd.DataFrame({
    "datetime_universal_time": pd.date_range("2026-01-01", periods=20, freq="h"),
    "actual_price": range(20),
  })

  train, validation, test = split_time_series_data(
    data=data,
    train_ratio=0.7,
    validation_ratio=0.15,
    test_ratio=0.15,
  )

  # Coverage: no row lost, no row invented.
  assert len(train) + len(validation) + len(test) == len(data)

  # Disjoint: no timestamp appears in two splits.
  train_times = set(train["datetime_universal_time"])
  validation_times = set(validation["datetime_universal_time"])
  test_times = set(test["datetime_universal_time"])
  assert not train_times & validation_times
  assert not validation_times & test_times
  assert not train_times & test_times

  # Ordered boundaries: past -> validation -> future.
  assert train["datetime_universal_time"].max() < validation["datetime_universal_time"].min()
  assert validation["datetime_universal_time"].max() < test["datetime_universal_time"].min()


def test_split_time_series_data_rejects_invalid_ratios():
  import pandas as pd
  import pytest

  from electricity_predictor.modeling.split import split_time_series_data

  data = pd.DataFrame({
    "datetime_universal_time": pd.date_range("2026-01-01", periods=10, freq="h"),
    "actual_price": range(10),
  })

  # Ratios that do not sum to 1.0 must fail loudly, not truncate silently.
  with pytest.raises(ValueError):
    split_time_series_data(
      data=data,
      train_ratio=0.7,
      validation_ratio=0.1,
      test_ratio=0.1,
    )
