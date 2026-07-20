from dataclasses import asdict, dataclass

import pandas as pd


@dataclass(frozen=True)
class LifecycleSplitPlan:
  """Store one reproducible lifecycle split definition."""

  train_start_utc: pd.Timestamp
  validation_start_utc: pd.Timestamp
  test_start_utc: pd.Timestamp
  test_end_utc: pd.Timestamp
  purge_hours: int

  def to_dict(self) -> dict:
    """Return serializable split metadata."""
    return {
      key: (
        value.isoformat()
        if isinstance(value, pd.Timestamp)
        else value
      )
      for key, value in asdict(self).items()
    }


def normalize_latest_timestamp(
  latest_timestamp_utc,
) -> pd.Timestamp:
  """Normalize the newest finalized observation to one UTC hour."""
  timestamp = pd.Timestamp(latest_timestamp_utc)

  if pd.isna(timestamp):
    raise ValueError(
      "Latest finalized timestamp must be valid."
    )

  if timestamp.tzinfo is not None:
    timestamp = (
      timestamp
      .tz_convert("UTC")
      .tz_localize(None)
    )

  return timestamp.floor("h")


def validate_lifecycle_configuration(
  validation_days: int,
  test_days: int,
  purge_hours: int,
  minimum_training_days: int,
) -> None:
  """Validate lifecycle window durations."""
  positive_values = {
    "validation_days": validation_days,
    "test_days": test_days,
    "minimum_training_days": minimum_training_days,
  }

  for name, value in positive_values.items():
    if not isinstance(value, int) or value <= 0:
      raise ValueError(
        f"{name} must be a positive integer."
      )

  if not isinstance(purge_hours, int) or purge_hours < 0:
    raise ValueError(
      "purge_hours must be a non-negative integer."
    )


def build_expanding_split_plan(
  latest_timestamp_utc,
  train_start_utc,
  validation_days: int,
  test_days: int,
  purge_hours: int,
  minimum_training_days: int,
) -> LifecycleSplitPlan:
  """Build expanding train and recent validation/test windows."""
  validate_lifecycle_configuration(
    validation_days=validation_days,
    test_days=test_days,
    purge_hours=purge_hours,
    minimum_training_days=minimum_training_days,
  )

  latest_timestamp = normalize_latest_timestamp(
    latest_timestamp_utc
  )
  train_start = normalize_latest_timestamp(
    train_start_utc
  )

  test_duration = pd.Timedelta(
    days=test_days
  )
  validation_duration = pd.Timedelta(
    days=validation_days
  )
  purge_duration = pd.Timedelta(
    hours=purge_hours
  )

  # Inclusive test boundaries contain exactly test_days * 24 hours.
  test_start = (
    latest_timestamp
    - test_duration
    + pd.Timedelta(hours=1)
  )

  validation_end_exclusive = (
    test_start - purge_duration
  )
  validation_start = (
    validation_end_exclusive
    - validation_duration
  )

  train_end_exclusive = (
    validation_start - purge_duration
  )

  minimum_training_end = (
    train_start
    + pd.Timedelta(
      days=minimum_training_days,
    )
  )

  if train_end_exclusive < minimum_training_end:
    raise ValueError(
      "Available data does not provide the minimum "
      "required training history."
    )

  return LifecycleSplitPlan(
    train_start_utc=train_start,
    validation_start_utc=validation_start,
    test_start_utc=test_start,
    test_end_utc=latest_timestamp,
    purge_hours=purge_hours,
  )


def build_lifecycle_split_plan_from_config(
  latest_timestamp_utc,
  modeling_config: dict,
  lifecycle_config: dict,
) -> LifecycleSplitPlan:
  """Build lifecycle boundaries from project configuration."""
  if lifecycle_config.get("strategy") != "expanding":
    raise ValueError(
      "Only the expanding lifecycle strategy is supported."
    )

  return build_expanding_split_plan(
    latest_timestamp_utc=latest_timestamp_utc,
    train_start_utc=modeling_config[
      "train_start_utc"
    ],
    validation_days=lifecycle_config[
      "validation_days"
    ],
    test_days=lifecycle_config[
      "test_days"
    ],
    purge_hours=lifecycle_config[
      "purge_hours"
    ],
    minimum_training_days=lifecycle_config[
      "minimum_training_days"
    ],
  )
