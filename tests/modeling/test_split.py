from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.split import (
  load_training_dataset,
  split_time_series_data,
  split_time_series_data_from_config,
  validate_fixed_split_configuration,
)


def make_sample_time_series_data() -> pd.DataFrame:
  """Create hourly data covering all fixed test periods."""
  timestamps = pd.date_range(
    start="2023-12-28 00:00:00",
    end="2025-01-03 23:00:00",
    freq="h",
  )

  return pd.DataFrame({
    "datetime_universal_time": timestamps,
    "actual_price": range(len(timestamps)),
  })


def test_validate_fixed_split_configuration_accepts_ordered_boundaries():
  boundaries = validate_fixed_split_configuration(
    train_start_utc="2023-12-28 00:00:00",
    validation_start_utc="2024-01-01 00:00:00",
    test_start_utc="2025-01-01 00:00:00",
    test_end_utc="2025-01-03 23:00:00",
    purge_hours=24,
  )

  assert boundaries == (
    pd.Timestamp("2023-12-28 00:00:00"),
    pd.Timestamp("2024-01-01 00:00:00"),
    pd.Timestamp("2025-01-01 00:00:00"),
    pd.Timestamp("2025-01-03 23:00:00"),
  )


def test_validate_fixed_split_configuration_rejects_invalid_order():
  with pytest.raises(ValueError, match="must follow"):
    validate_fixed_split_configuration(
      train_start_utc="2024-01-01 00:00:00",
      validation_start_utc="2023-01-01 00:00:00",
      test_start_utc="2025-01-01 00:00:00",
      test_end_utc="2025-12-31 23:00:00",
      purge_hours=24,
    )


def test_validate_fixed_split_configuration_rejects_negative_purge():
  with pytest.raises(ValueError, match="Purge hours"):
    validate_fixed_split_configuration(
      train_start_utc="2023-01-01 00:00:00",
      validation_start_utc="2024-01-01 00:00:00",
      test_start_utc="2025-01-01 00:00:00",
      test_end_utc="2025-12-31 23:00:00",
      purge_hours=-1,
    )


def test_split_time_series_data_rejects_empty_dataset():
  with pytest.raises(ValueError, match="Cannot split an empty dataset"):
    split_time_series_data(
      data=pd.DataFrame(),
      train_start_utc="2023-12-28 00:00:00",
      validation_start_utc="2024-01-01 00:00:00",
      test_start_utc="2025-01-01 00:00:00",
      test_end_utc="2025-01-03 23:00:00",
      purge_hours=24,
    )


def test_split_time_series_data_uses_fixed_dates_and_purges_boundaries():
  data = make_sample_time_series_data()

  train, validation, test = split_time_series_data(
    data=data,
    train_start_utc="2023-12-28 00:00:00",
    validation_start_utc="2024-01-01 00:00:00",
    test_start_utc="2025-01-01 00:00:00",
    test_end_utc="2025-01-03 23:00:00",
    purge_hours=24,
  )

  assert train["datetime_universal_time"].min() == pd.Timestamp(
    "2023-12-28 00:00:00"
  )
  assert train["datetime_universal_time"].max() == pd.Timestamp(
    "2023-12-30 23:00:00"
  )

  assert validation["datetime_universal_time"].min() == pd.Timestamp(
    "2024-01-01 00:00:00"
  )
  assert validation["datetime_universal_time"].max() == pd.Timestamp(
    "2024-12-30 23:00:00"
  )

  assert test["datetime_universal_time"].min() == pd.Timestamp(
    "2025-01-01 00:00:00"
  )
  assert test["datetime_universal_time"].max() == pd.Timestamp(
    "2025-01-03 23:00:00"
  )


def test_split_time_series_data_removes_exactly_24_hours_before_each_boundary():
  data = make_sample_time_series_data()

  train, validation, test = split_time_series_data(
    data=data,
    train_start_utc="2023-12-28 00:00:00",
    validation_start_utc="2024-01-01 00:00:00",
    test_start_utc="2025-01-01 00:00:00",
    test_end_utc="2025-01-03 23:00:00",
    purge_hours=24,
  )

  all_split_times = set(
    pd.concat([
      train["datetime_universal_time"],
      validation["datetime_universal_time"],
      test["datetime_universal_time"],
    ])
  )

  first_purge = set(pd.date_range(
    "2023-12-31 00:00:00",
    "2023-12-31 23:00:00",
    freq="h",
  ))
  second_purge = set(pd.date_range(
    "2024-12-31 00:00:00",
    "2024-12-31 23:00:00",
    freq="h",
  ))

  assert not all_split_times & first_purge
  assert not all_split_times & second_purge
  assert len(first_purge) == 24
  assert len(second_purge) == 24


def test_split_time_series_data_returns_disjoint_ordered_splits():
  data = make_sample_time_series_data()

  train, validation, test = split_time_series_data(
    data=data,
    train_start_utc="2023-12-28 00:00:00",
    validation_start_utc="2024-01-01 00:00:00",
    test_start_utc="2025-01-01 00:00:00",
    test_end_utc="2025-01-03 23:00:00",
    purge_hours=24,
  )

  train_times = set(train["datetime_universal_time"])
  validation_times = set(validation["datetime_universal_time"])
  test_times = set(test["datetime_universal_time"])

  assert not train_times & validation_times
  assert not validation_times & test_times
  assert not train_times & test_times

  assert (
    train["datetime_universal_time"].max()
    < validation["datetime_universal_time"].min()
  )
  assert (
    validation["datetime_universal_time"].max()
    < test["datetime_universal_time"].min()
  )


def test_split_time_series_data_rejects_empty_resulting_split():
  data = make_sample_time_series_data()

  with pytest.raises(ValueError, match="non-empty"):
    split_time_series_data(
      data=data,
      train_start_utc="2020-01-01 00:00:00",
      validation_start_utc="2021-01-01 00:00:00",
      test_start_utc="2022-01-01 00:00:00",
      test_end_utc="2022-12-31 23:00:00",
      purge_hours=24,
    )


def test_load_training_dataset_rejects_missing_file():
  with pytest.raises(FileNotFoundError):
    load_training_dataset(Path("missing_training_dataset.csv"))


def test_load_training_dataset_loads_and_sorts_by_utc_time(tmp_path):
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

  assert str(loaded["datetime_universal_time"].dtype).startswith("datetime64")
  assert loaded["datetime_universal_time"].is_monotonic_increasing
  assert loaded["actual_price"].tolist() == [1.0, 2.0, 3.0]


def test_load_training_dataset_rejects_invalid_timestamps(tmp_path):
  data = pd.DataFrame({
    "datetime_universal_time": [
      "2026-01-01 08:00:00",
      "invalid",
    ],
    "actual_price": [1.0, 2.0],
  })

  file_path = tmp_path / "training_dataset.csv"
  data.to_csv(file_path, index=False)

  with pytest.raises(ValueError, match="invalid UTC timestamps"):
    load_training_dataset(file_path)


def test_split_time_series_data_from_config_uses_shared_boundaries():
  data = make_sample_time_series_data()

  train, validation, test = split_time_series_data_from_config(
    data=data,
    modeling_config={
      "train_start_utc": "2023-12-28 00:00:00",
      "validation_start_utc": "2024-01-01 00:00:00",
      "test_start_utc": "2025-01-01 00:00:00",
      "test_end_utc": "2025-01-03 23:00:00",
      "purge_hours": 24,
    },
  )

  assert train["datetime_universal_time"].max() == pd.Timestamp(
    "2023-12-30 23:00:00"
  )
  assert validation["datetime_universal_time"].max() == pd.Timestamp(
    "2024-12-30 23:00:00"
  )
  assert test["datetime_universal_time"].max() == pd.Timestamp(
    "2025-01-03 23:00:00"
  )


def test_split_time_series_data_from_config_rejects_missing_keys():
  data = make_sample_time_series_data()

  with pytest.raises(ValueError, match="Missing fixed split configuration keys"):
    split_time_series_data_from_config(
      data=data,
      modeling_config={
        "train_start_utc": "2023-12-28 00:00:00",
      },
    )


def test_split_time_series_data_normalizes_timezone_aware_utc_values():
  """Timezone-aware UTC input must follow the existing naive UTC contract."""
  timestamps = pd.date_range(
    start="2023-12-28 00:00:00",
    end="2025-01-03 23:00:00",
    freq="h",
    tz="UTC",
  )

  data = pd.DataFrame({
    "datetime_universal_time": timestamps,
    "actual_price": range(len(timestamps)),
  })

  train, validation, test = split_time_series_data(
    data=data,
    train_start_utc="2023-12-28 00:00:00",
    validation_start_utc="2024-01-01 00:00:00",
    test_start_utc="2025-01-01 00:00:00",
    test_end_utc="2025-01-03 23:00:00",
    purge_hours=24,
  )

  assert train["datetime_universal_time"].dt.tz is None
  assert validation["datetime_universal_time"].dt.tz is None
  assert test["datetime_universal_time"].dt.tz is None

  assert train["datetime_universal_time"].min() == pd.Timestamp(
    "2023-12-28 00:00:00"
  )
  assert train["datetime_universal_time"].max() == pd.Timestamp(
    "2023-12-30 23:00:00"
  )
