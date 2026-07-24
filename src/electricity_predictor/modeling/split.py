"""Create leakage-safe chronological training, validation, and test splits."""

from pathlib import Path

import pandas as pd


TRAINING_DATASET_PATH = Path("data/processed/training_dataset.csv")
DATETIME_COLUMN = "datetime_universal_time"


def load_training_dataset(file_path: Path = TRAINING_DATASET_PATH) -> pd.DataFrame:
  """Load and chronologically sort the model-ready training dataset."""
  if not file_path.exists():
    raise FileNotFoundError(f"Training dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  if DATETIME_COLUMN not in data.columns:
    raise ValueError(f"Missing required datetime column: {DATETIME_COLUMN}")

  data[DATETIME_COLUMN] = pd.to_datetime(
    data[DATETIME_COLUMN],
    errors="coerce",
  )

  if data[DATETIME_COLUMN].isna().any():
    raise ValueError("Training dataset contains invalid UTC timestamps.")

  # Every modeling workflow must receive the same chronological row order.
  return data.sort_values(DATETIME_COLUMN).reset_index(drop=True)


def validate_fixed_split_configuration(
  train_start_utc: str,
  validation_start_utc: str,
  test_start_utc: str,
  test_end_utc: str,
  purge_hours: int,
) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
  """Validate and normalize fixed chronological split boundaries."""
  if purge_hours < 0:
    raise ValueError("Purge hours must be greater than or equal to 0.")

  timestamps = pd.to_datetime(
    [
      train_start_utc,
      validation_start_utc,
      test_start_utc,
      test_end_utc,
    ],
    errors="coerce",
  )

  if timestamps.isna().any():
    raise ValueError("Fixed split boundaries must be valid UTC timestamps.")

  train_start, validation_start, test_start, test_end = timestamps

  if not train_start < validation_start < test_start <= test_end:
    raise ValueError(
      "Fixed split boundaries must follow "
      "train_start < validation_start < test_start <= test_end."
    )

  return train_start, validation_start, test_start, test_end


def split_time_series_data(
  data: pd.DataFrame,
  train_start_utc: str,
  validation_start_utc: str,
  test_start_utc: str,
  test_end_utc: str,
  purge_hours: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
  """Create fixed chronological splits with a purge before each next period."""
  if data.empty:
    raise ValueError("Cannot split an empty dataset.")

  if DATETIME_COLUMN not in data.columns:
    raise ValueError(f"Missing required datetime column: {DATETIME_COLUMN}")

  working_data = data.copy()
  working_data[DATETIME_COLUMN] = pd.to_datetime(
    working_data[DATETIME_COLUMN],
    errors="coerce",
  )

  if working_data[DATETIME_COLUMN].isna().any():
    raise ValueError("Cannot split data with invalid UTC timestamps.")

  working_data = working_data.sort_values(DATETIME_COLUMN).reset_index(drop=True)

  (
    train_start,
    validation_start,
    test_start,
    test_end,
  ) = validate_fixed_split_configuration(
    train_start_utc=train_start_utc,
    validation_start_utc=validation_start_utc,
    test_start_utc=test_start_utc,
    test_end_utc=test_end_utc,
    purge_hours=purge_hours,
  )

  purge_delta = pd.Timedelta(hours=purge_hours)

  # The purge removes labels whose future horizon could cross the next boundary.
  train_end_exclusive = validation_start - purge_delta
  validation_end_exclusive = test_start - purge_delta

  train_data = working_data[
    (working_data[DATETIME_COLUMN] >= train_start)
    & (working_data[DATETIME_COLUMN] < train_end_exclusive)
  ]

  validation_data = working_data[
    (working_data[DATETIME_COLUMN] >= validation_start)
    & (working_data[DATETIME_COLUMN] < validation_end_exclusive)
  ]

  test_data = working_data[
    (working_data[DATETIME_COLUMN] >= test_start)
    & (working_data[DATETIME_COLUMN] <= test_end)
  ]

  if train_data.empty or validation_data.empty or test_data.empty:
    raise ValueError(
      "Fixed split configuration must produce non-empty "
      "train, validation, and test sets."
    )

  return (
    train_data.reset_index(drop=True),
    validation_data.reset_index(drop=True),
    test_data.reset_index(drop=True),
  )


def split_time_series_data_from_config(
  data: pd.DataFrame,
  modeling_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
  """Create fixed chronological splits from the shared modeling configuration."""
  required_keys = {
    "train_start_utc",
    "validation_start_utc",
    "test_start_utc",
    "test_end_utc",
    "purge_hours",
  }
  missing_keys = required_keys - set(modeling_config)

  if missing_keys:
    raise ValueError(
      f"Missing fixed split configuration keys: {sorted(missing_keys)}"
    )

  # One helper prevents modeling workflows from interpreting boundaries differently.
  return split_time_series_data(
    data=data,
    train_start_utc=modeling_config["train_start_utc"],
    validation_start_utc=modeling_config["validation_start_utc"],
    test_start_utc=modeling_config["test_start_utc"],
    test_end_utc=modeling_config["test_end_utc"],
    purge_hours=modeling_config["purge_hours"],
  )


def get_time_series_cv_gap_hours(modeling_config: dict) -> int:
  """Read and validate the shared cross-validation gap."""
  if "time_series_cv_gap_hours" not in modeling_config:
    raise ValueError("Missing time_series_cv_gap_hours in modeling configuration.")

  gap_hours = modeling_config["time_series_cv_gap_hours"]

  if not isinstance(gap_hours, int) or gap_hours < 0:
    raise ValueError(
      "time_series_cv_gap_hours must be a non-negative integer."
    )

  return gap_hours
