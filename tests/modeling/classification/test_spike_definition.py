import pandas as pd
import pytest

from electricity_predictor.modeling.classification.spike_definition import (
  calculate_iqr_spike_threshold,
  calculate_quantile_spike_threshold,
  classify_spikes,
  summarize_spikes,
)


def test_calculate_iqr_spike_threshold_uses_upper_iqr_fence():
  prices = pd.Series([1.0, 2.0, 3.0, 4.0, 100.0])

  threshold = calculate_iqr_spike_threshold(prices)

  # Q1=2, Q3=4, and IQR=2, so the upper fence is 4 + 1.5*2 = 7.
  assert threshold == pytest.approx(7.0)


def test_calculate_iqr_spike_threshold_rejects_non_positive_multiplier():
  prices = pd.Series([10.0, 20.0, 30.0])

  with pytest.raises(ValueError, match="multiplier must be greater than 0"):
    calculate_iqr_spike_threshold(
      prices=prices,
      multiplier=0,
    )


def test_calculate_quantile_spike_threshold_returns_requested_quantile():
  prices = pd.Series(range(101), dtype=float)

  threshold = calculate_quantile_spike_threshold(
    prices=prices,
    quantile=0.95,
  )

  assert threshold == pytest.approx(95.0)


def test_calculate_quantile_spike_threshold_rejects_invalid_quantile():
  prices = pd.Series([10.0, 20.0, 30.0])

  with pytest.raises(ValueError, match="greater than 0 and less than 1"):
    calculate_quantile_spike_threshold(
      prices=prices,
      quantile=1.0,
    )


def test_spike_threshold_functions_reject_empty_or_missing_prices():
  with pytest.raises(ValueError, match="empty price series"):
    calculate_iqr_spike_threshold(pd.Series([], dtype=float))

  with pytest.raises(ValueError, match="non-missing prices"):
    calculate_iqr_spike_threshold(pd.Series([10.0, None, 30.0]))


def test_classify_spikes_marks_only_prices_strictly_above_threshold():
  prices = pd.Series([49.0, 50.0, 51.0, 100.0])

  labels = classify_spikes(
    prices=prices,
    threshold=50.0,
  )

  assert labels.tolist() == [0, 0, 1, 1]


def test_summarize_spikes_reports_class_balance():
  prices = pd.Series([10.0, 20.0, 60.0, 80.0])

  summary = summarize_spikes(
    prices=prices,
    threshold=50.0,
  )

  assert summary == {
    "row_count": 4,
    "spike_count": 2,
    "non_spike_count": 2,
    "spike_rate": 0.5,
  }


from electricity_predictor.modeling.classification.analyze_spike_definition import (
  build_spike_analysis_rows,
  calculate_train_thresholds,
)


def make_horizon_data(prices: list[float]) -> pd.DataFrame:
  """Create one synthetic horizon target for spike-analysis tests."""
  return pd.DataFrame({
    "actual_price": prices,
    "actual_price_target_1h": prices,
  })


def test_calculate_train_thresholds_returns_all_candidate_methods():
  train_prices = pd.Series([1.0, 2.0, 3.0, 4.0, 100.0])

  thresholds = calculate_train_thresholds(train_prices)

  assert set(thresholds) == {"iqr", "q95", "q99"}
  assert thresholds["iqr"] == pytest.approx(7.0)


def test_build_spike_analysis_rows_reuses_train_threshold_for_all_splits():
  train_data = make_horizon_data([1.0, 2.0, 3.0, 4.0, 100.0])
  validation_data = make_horizon_data([1000.0, 1100.0])

  rows = build_spike_analysis_rows(
    train_data=train_data,
    validation_data=validation_data,
    horizons_hours=[1],
  )

  iqr_rows = [row for row in rows if row["method"] == "iqr"]

  # Extreme future prices must not change the train-derived IQR threshold.
  assert len(iqr_rows) == 2
  assert all(row["threshold"] == pytest.approx(7.0) for row in iqr_rows)


def test_build_spike_analysis_rows_creates_one_row_per_method_and_split():
  train_data = make_horizon_data([1.0, 2.0, 3.0, 4.0, 100.0])
  validation_data = make_horizon_data([2.0, 3.0])

  rows = build_spike_analysis_rows(
    train_data=train_data,
    validation_data=validation_data,
    horizons_hours=[1],
  )

  # Three methods multiplied by two research splits produce six rows.
  assert len(rows) == 6
  assert {row["split"] for row in rows} == {"train", "validation"}


def test_build_spike_analysis_rows_rejects_missing_target_column():
  data = pd.DataFrame({"actual_price": [10.0, 20.0]})

  with pytest.raises(ValueError, match="Missing target column"):
    build_spike_analysis_rows(
      train_data=data,
      validation_data=data,
      horizons_hours=[1],
    )
