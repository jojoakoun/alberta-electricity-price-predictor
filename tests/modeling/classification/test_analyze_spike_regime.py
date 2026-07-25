import pandas as pd
import pytest

from electricity_predictor.modeling.classification.analyze_spike_regime import (
  build_spike_regime_rows,
  build_yearly_regime_rows,
)


def make_regime_data(
  timestamps: list[str],
  prices: list[float],
) -> pd.DataFrame:
  """Create synthetic time-series data for regime-analysis tests."""
  return pd.DataFrame({
    "datetime_universal_time": pd.to_datetime(timestamps),
    "actual_price": prices,
  })


def test_build_yearly_regime_rows_groups_prices_by_year():
  data = make_regime_data(
    timestamps=[
      "2023-12-31 22:00:00",
      "2023-12-31 23:00:00",
      "2024-01-01 00:00:00",
      "2024-01-01 01:00:00",
    ],
    prices=[10.0, 100.0, 20.0, 30.0],
  )

  rows = build_yearly_regime_rows(
    data=data,
    split_name="train",
    threshold=50.0,
  )

  assert len(rows) == 2

  first_row = rows[0]

  assert first_row["split"] == "train"
  assert first_row["year"] == 2023
  assert first_row["first_timestamp"] == pd.Timestamp(
    "2023-12-31 22:00:00"
  )
  assert first_row["last_timestamp"] == pd.Timestamp(
    "2023-12-31 23:00:00"
  )
  assert first_row["threshold_method"] == "iqr"
  assert first_row["threshold"] == 50.0
  assert first_row["row_count"] == 2
  assert first_row["spike_count"] == 1
  assert first_row["non_spike_count"] == 1
  assert first_row["spike_rate"] == 0.5
  assert first_row["mean_price"] == 55.0
  assert first_row["median_price"] == 55.0
  assert first_row["price_std"] == pytest.approx(63.6396103068)
  assert first_row["p95_price"] == pytest.approx(95.5)
  assert first_row["max_price"] == 100.0

  second_row = rows[1]

  assert second_row["year"] == 2024
  assert second_row["row_count"] == 2
  assert second_row["spike_count"] == 0
  assert second_row["spike_rate"] == 0.0
  assert second_row["mean_price"] == 25.0
  assert second_row["p95_price"] == pytest.approx(29.5)


def test_build_spike_regime_rows_reuses_train_threshold_for_all_splits():
  train_data = make_regime_data(
    timestamps=[
      "2020-01-01 00:00:00",
      "2020-01-01 01:00:00",
      "2020-01-01 02:00:00",
      "2020-01-01 03:00:00",
      "2020-01-01 04:00:00",
    ],
    prices=[1.0, 2.0, 3.0, 4.0, 100.0],
  )

  validation_data = make_regime_data(
    timestamps=[
      "2021-01-01 00:00:00",
      "2021-01-01 01:00:00",
    ],
    prices=[1000.0, 1100.0],
  )

  rows = build_spike_regime_rows(
    train_data=train_data,
    validation_data=validation_data,
  )

  # Q1=2, Q3=4, and IQR=2, so the frozen train threshold is 7.
  assert len(rows) == 2
  assert all(row["threshold"] == pytest.approx(7.0) for row in rows)
  assert {row["split"] for row in rows} == {
    "train",
    "validation",
  }


def test_build_yearly_regime_rows_rejects_missing_timestamp_column():
  data = pd.DataFrame({
    "actual_price": [10.0, 20.0],
  })

  with pytest.raises(
    ValueError,
    match="Missing required regime-analysis columns",
  ):
    build_yearly_regime_rows(
      data=data,
      split_name="train",
      threshold=50.0,
    )


def test_build_yearly_regime_rows_rejects_missing_timestamps():
  data = pd.DataFrame({
    "datetime_universal_time": [
      pd.Timestamp("2024-01-01 00:00:00"),
      pd.NaT,
    ],
    "actual_price": [10.0, 20.0],
  })

  with pytest.raises(
    ValueError,
    match="non-missing UTC timestamps",
  ):
    build_yearly_regime_rows(
      data=data,
      split_name="train",
      threshold=50.0,
    )


def test_build_yearly_regime_rows_rejects_non_numeric_prices():
  data = pd.DataFrame({
    "datetime_universal_time": pd.to_datetime([
      "2024-01-01 00:00:00",
      "2024-01-01 01:00:00",
    ]),
    "actual_price": ["10.0", "20.0"],
  })

  with pytest.raises(
    ValueError,
    match="numeric actual prices",
  ):
    build_yearly_regime_rows(
      data=data,
      split_name="train",
      threshold=50.0,
    )
