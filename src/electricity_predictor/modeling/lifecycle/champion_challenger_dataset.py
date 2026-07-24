"""Build one frozen dataset for champion-challenger evaluation."""

from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.feature_engineering import (
  add_horizon_target_features,
  add_lag_features,
  add_rolling_features,
  build_target_column_names,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  add_live_feature_candidates,
)
from electricity_predictor.modeling.live_contract.live_model_datasets import (
  DATETIME_COLUMN,
  HISTORICAL_DATASET_PATH,
  LOCAL_DATETIME_COLUMN,
  load_live_feature_source,
  ordered_unique,
  write_dataset,
)


CHAMPION_CHALLENGER_MODELING_DATASET_PATH = Path(
  "data/processed/"
  "champion_challenger_modeling_dataset.csv"
)

CHAMPION_CHALLENGER_TRAINING_DATASET_PATH = Path(
  "data/processed/"
  "champion_challenger_training_dataset.csv"
)

# The comparison dataset supports both the active model contract and the
# production-safe challenger contract. Each model still selects its own order.
CHAMPION_CHALLENGER_FEATURE_COLUMNS = ordered_unique([
  *SELECTED_LIVE_FEATURE_COLUMNS,
  *MODEL_FEATURE_COLUMNS,
])


def build_champion_challenger_modeling_dataset(
  source_data: pd.DataFrame,
) -> pd.DataFrame:
  """Build legacy and live features on the same continuous hourly rows."""
  finalized_data = (
    source_data
    .dropna(
      subset=[
        "actual_price",
      ],
    )
    .reset_index(drop=True)
    .copy()
  )

  # Live features establish the production-safe challenger contract.
  feature_data = add_live_feature_candidates(
    finalized_data
  )

  # Legacy-only columns remain available strictly for evaluating an older
  # active champion during the architectural transition.
  feature_data = add_lag_features(
    feature_data
  )

  feature_data = add_rolling_features(
    feature_data
  )

  target_columns = build_target_column_names(
    list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  )

  modeling_data = add_horizon_target_features(
    data=feature_data,
    horizons_hours=list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    ),
  )

  output_columns = ordered_unique([
    DATETIME_COLUMN,
    LOCAL_DATETIME_COLUMN,
    "actual_price",
    "forecast_price",
    *CHAMPION_CHALLENGER_FEATURE_COLUMNS,
    *target_columns,
  ])

  return modeling_data[
    output_columns
  ].copy()


def build_champion_challenger_training_dataset(
  modeling_data: pd.DataFrame,
) -> pd.DataFrame:
  """Keep rows complete for both model contracts and every target."""
  target_columns = build_target_column_names(
    list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  )

  required_columns = [
    *CHAMPION_CHALLENGER_FEATURE_COLUMNS,
    *target_columns,
  ]

  return (
    modeling_data
    .dropna(
      subset=required_columns,
    )
    .reset_index(drop=True)
  )


def build_and_save_champion_challenger_datasets() -> tuple[
  Path,
  Path,
  pd.DataFrame,
  pd.DataFrame,
]:
  """Build and save the datasets later frozen by the lifecycle manifest."""
  source_data = load_live_feature_source()

  modeling_data = (
    build_champion_challenger_modeling_dataset(
      source_data
    )
  )

  training_data = (
    build_champion_challenger_training_dataset(
      modeling_data
    )
  )

  modeling_path = write_dataset(
    modeling_data,
    CHAMPION_CHALLENGER_MODELING_DATASET_PATH,
  )

  training_path = write_dataset(
    training_data,
    CHAMPION_CHALLENGER_TRAINING_DATASET_PATH,
  )

  return (
    modeling_path,
    training_path,
    modeling_data,
    training_data,
  )
