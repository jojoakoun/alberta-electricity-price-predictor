"""Feature metadata parsing and compatibility exports.

All reusable column values are defined in
``electricity_predictor.contracts.columns``.
"""

from electricity_predictor.contracts.columns import (
  ENGINEERED_FEATURE_COLUMNS,
  HORIZON_TARGET_COLUMNS,
  MODEL_FEATURE_COLUMNS,
  SUPPORTED_FORECAST_HORIZONS_HOURS,
  TRAINING_REQUIRED_COLUMNS,
)


def parse_model_feature_columns(
  value: object,
) -> list[str]:
  """Return the ordered feature names recorded in model metadata.

  Feature order is part of the artifact contract. Invalid metadata must fail
  instead of silently changing the estimator input shape.
  """
  if not isinstance(value, str) or not value.strip():
    raise ValueError(
      "Model metadata contains no feature columns."
    )

  feature_columns = [
    column.strip()
    for column in value.split("|")
    if column.strip()
  ]

  if not feature_columns:
    raise ValueError(
      "Model metadata contains no valid feature columns."
    )

  return feature_columns
