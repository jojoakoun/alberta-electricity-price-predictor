import pandas as pd

from electricity_predictor.features.feature_engineering import build_target_column_name
from electricity_predictor.modeling.classification.spike_definition import (
  calculate_iqr_spike_threshold,
  classify_spikes,
)
from electricity_predictor.contracts.columns import (
  ACTUAL_PRICE_COLUMN,
)




def build_spike_target_column_name(horizon_hours: int) -> str:
  """Build the classification target name for one forecast horizon."""
  return f"is_spike_target_{horizon_hours}h"


def validate_classification_target_inputs(
  data: pd.DataFrame,
  horizons_hours: list[int],
) -> None:
  """Validate columns required to create classification targets."""
  if ACTUAL_PRICE_COLUMN not in data.columns:
    raise ValueError(f"Missing required column: {ACTUAL_PRICE_COLUMN}")

  for horizon_hours in horizons_hours:
    target_column = build_target_column_name(horizon_hours)

    if target_column not in data.columns:
      raise ValueError(f"Missing target column: {target_column}")


def add_spike_targets(
  data: pd.DataFrame,
  threshold: float,
  horizons_hours: list[int],
) -> pd.DataFrame:
  """Add binary spike targets using one fixed train-derived threshold."""
  validate_classification_target_inputs(
    data=data,
    horizons_hours=horizons_hours,
  )

  data = data.copy()

  for horizon_hours in horizons_hours:
    price_target_column = build_target_column_name(horizon_hours)
    spike_target_column = build_spike_target_column_name(horizon_hours)

    # Reuse one frozen threshold so all horizons share the same spike definition.
    data[spike_target_column] = classify_spikes(
      prices=data[price_target_column],
      threshold=threshold,
    )

  return data


def prepare_classification_splits(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  test_data: pd.DataFrame,
  horizons_hours: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, float]:
  """Create classification targets after fitting the spike threshold on train."""
  (
    prepared_train,
    prepared_validation,
    threshold,
  ) = prepare_classification_training_splits(
    train_data=train_data,
    validation_data=validation_data,
    horizons_hours=horizons_hours,
  )

  prepared_test = add_spike_targets(
    data=test_data,
    threshold=threshold,
    horizons_hours=horizons_hours,
  )

  return (
    prepared_train,
    prepared_validation,
    prepared_test,
    threshold,
  )


def prepare_classification_training_splits(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  horizons_hours: list[int],
) -> tuple[pd.DataFrame, pd.DataFrame, float]:
  """Prepare train and validation targets without accessing protected test data."""
  validate_classification_target_inputs(
    data=train_data,
    horizons_hours=horizons_hours,
  )

  # Fit the spike definition on train only to avoid future distribution leakage.
  threshold = calculate_iqr_spike_threshold(
    train_data[ACTUAL_PRICE_COLUMN]
  )

  prepared_train = add_spike_targets(
    data=train_data,
    threshold=threshold,
    horizons_hours=horizons_hours,
  )

  prepared_validation = add_spike_targets(
    data=validation_data,
    threshold=threshold,
    horizons_hours=horizons_hours,
  )

  return (
    prepared_train,
    prepared_validation,
    threshold,
  )
