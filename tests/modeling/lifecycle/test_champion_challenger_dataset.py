import numpy as np
import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.feature_engineering import (
  build_target_column_names,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.lifecycle.champion_challenger_dataset import (
  CHAMPION_CHALLENGER_FEATURE_COLUMNS,
  build_champion_challenger_modeling_dataset,
  build_champion_challenger_training_dataset,
)
from electricity_predictor.modeling.live_contract.live_model_datasets import (
  DATETIME_COLUMN,
  LOCAL_DATETIME_COLUMN,
  ordered_unique,
)


def build_hourly_source(
  row_count: int = 260,
) -> pd.DataFrame:
  """Build enough continuous data for seven-day rolling features."""
  utc_timestamps = pd.date_range(
    start="2026-01-01 00:00:00",
    periods=row_count,
    freq="h",
    tz="UTC",
  )

  return pd.DataFrame({
    DATETIME_COLUMN:
      utc_timestamps,
    LOCAL_DATETIME_COLUMN:
      utc_timestamps.tz_convert(
        "America/Edmonton"
      ),
    "actual_price":
      np.arange(
        row_count,
        dtype=float,
      )
      + 50.0,
    "forecast_price":
      np.arange(
        row_count,
        dtype=float,
      )
      + 45.0,
  })


def test_feature_contract_is_the_ordered_union() -> None:
  expected_columns = ordered_unique([
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *MODEL_FEATURE_COLUMNS,
  ])

  assert (
    CHAMPION_CHALLENGER_FEATURE_COLUMNS
    == expected_columns
  )

  assert len(
    CHAMPION_CHALLENGER_FEATURE_COLUMNS
  ) == 18

  assert set(
    MODEL_FEATURE_COLUMNS
  ) <= set(
    CHAMPION_CHALLENGER_FEATURE_COLUMNS
  )

  assert set(
    SELECTED_LIVE_FEATURE_COLUMNS
  ) <= set(
    CHAMPION_CHALLENGER_FEATURE_COLUMNS
  )


def test_modeling_dataset_contains_both_contracts() -> None:
  source_data = build_hourly_source()

  modeling_data = (
    build_champion_challenger_modeling_dataset(
      source_data
    )
  )

  target_columns = build_target_column_names(
    list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  )

  expected_columns = ordered_unique([
    DATETIME_COLUMN,
    LOCAL_DATETIME_COLUMN,
    "actual_price",
    "forecast_price",
    *CHAMPION_CHALLENGER_FEATURE_COLUMNS,
    *target_columns,
  ])

  assert list(
    modeling_data.columns
  ) == expected_columns

  assert len(modeling_data) == len(
    source_data
  )


def test_legacy_and_safe_actual_features_remain_distinct() -> None:
  source_data = build_hourly_source()

  modeling_data = (
    build_champion_challenger_modeling_dataset(
      source_data
    )
  )

  row_index = 200

  assert (
    modeling_data.loc[
      row_index,
      "actual_price_lag_1h",
    ]
    == source_data.loc[
      row_index - 1,
      "actual_price",
    ]
  )

  assert (
    modeling_data.loc[
      row_index,
      "actual_price_lag_24h",
    ]
    == source_data.loc[
      row_index - 24,
      "actual_price",
    ]
  )

  expected_safe_mean = (
    source_data[
      "actual_price"
    ]
    .shift(24)
    .rolling(
      window=24,
      min_periods=24,
    )
    .mean()
    .loc[row_index]
  )

  assert (
    modeling_data.loc[
      row_index,
      "actual_price_safe_24h_mean",
    ]
    == expected_safe_mean
  )


def test_training_dataset_contains_only_complete_rows() -> None:
  modeling_data = (
    build_champion_challenger_modeling_dataset(
      build_hourly_source()
    )
  )

  training_data = (
    build_champion_challenger_training_dataset(
      modeling_data
    )
  )

  target_columns = build_target_column_names(
    list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  )

  required_columns = [
    *CHAMPION_CHALLENGER_FEATURE_COLUMNS,
    *target_columns,
  ]

  assert not training_data.empty

  assert len(training_data) < len(
    modeling_data
  )

  assert not training_data[
    required_columns
  ].isna().any().any()


def test_internal_missing_actual_price_breaks_hourly_continuity() -> None:
  source_data = build_hourly_source()

  source_data.loc[
    100,
    "actual_price",
  ] = np.nan

  with pytest.raises(ValueError):
    build_champion_challenger_modeling_dataset(
      source_data
    )
