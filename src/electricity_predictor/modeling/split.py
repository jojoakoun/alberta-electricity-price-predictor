from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from electricity_predictor.config import load_configuration


TRAINING_DATASET_PATH = Path("data/processed/training_dataset.csv")


def load_training_dataset(file_path: Path) -> pd.DataFrame:
  """Load the model-ready training dataset."""
  if not file_path.exists():
    raise FileNotFoundError(f"Training dataset not found: {file_path}")

  data = pd.read_csv(file_path)

  # Convert UTC time before sorting and printing split date ranges.
  data["datetime_universal_time"] = pd.to_datetime(data["datetime_universal_time"])

  # Time-series splits only make sense when rows are ordered from oldest to newest.
  data = data.sort_values("datetime_universal_time").reset_index(drop=True)

  return data


def validate_split_ratios(
  train_ratio: float,
  validation_ratio: float,
  test_ratio: float,
) -> None:
  """Validate train, validation, and test ratios."""
  ratios = [train_ratio, validation_ratio, test_ratio]

  # Each split must receive data so training, tuning, and final testing all exist.
  if any(ratio <= 0 for ratio in ratios):
    raise ValueError("Train, validation, and test ratios must be greater than 0.")

  total_ratio = sum(ratios)
  difference_from_one = abs(total_ratio - 1.0)

  # Use a small tolerance so valid decimal ratios are not rejected by floating-point math.
  if difference_from_one > 1e-9:
    raise ValueError("Train, validation, and test ratios must sum to 1.0.")


def split_time_series_data(
  data: pd.DataFrame,
  train_ratio: float,
  validation_ratio: float,
  test_ratio: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
  """Split ordered time-series data into train, validation, and test sets."""
  if data.empty:
    raise ValueError("Cannot split an empty dataset.")
  



  validate_split_ratios(
    train_ratio=train_ratio,
    validation_ratio=validation_ratio,
    test_ratio=test_ratio,
  )

  # Use shuffle=False so the model trains on older rows before seeing newer rows.
  train_data, temporary_data = train_test_split(
    data,
    train_size=train_ratio,
    shuffle=False,
  )

  temporary_ratio = validation_ratio + test_ratio

  # The second split only sees the remaining validation + test block.
  validation_share_of_temporary_data = validation_ratio / temporary_ratio

  # Keep validation before test so the final test set represents the newest data.
  validation_data, test_data = train_test_split(
    temporary_data,
    train_size=validation_share_of_temporary_data,
    shuffle=False,
  )

  return (
    train_data.reset_index(drop=True),
    validation_data.reset_index(drop=True),
    test_data.reset_index(drop=True),
  )


def print_split_summary(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  test_data: pd.DataFrame,
) -> None:
  """Print a readable summary of the time-based split."""
  print("Time-based modeling split")
  print("=========================")
  print(f"Train rows: {len(train_data):,}")
  print(f"Validation rows: {len(validation_data):,}")
  print(f"Test rows: {len(test_data):,}")

  print("\nTime ranges")
  print("-----------")
  print(
    f"Train: {train_data['datetime_universal_time'].min()} "
    f"to {train_data['datetime_universal_time'].max()}"
  )
  print(
    f"Validation: {validation_data['datetime_universal_time'].min()} "
    f"to {validation_data['datetime_universal_time'].max()}"
  )
  print(
    f"Test: {test_data['datetime_universal_time'].min()} "
    f"to {test_data['datetime_universal_time'].max()}"
  )


if __name__ == "__main__":
  configuration = load_configuration()

  modeling_config = configuration["modeling"]

  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, test_data = split_time_series_data(
    data=training_data,
    train_ratio=modeling_config["train_ratio"],
    validation_ratio=modeling_config["validation_ratio"],
    test_ratio=modeling_config["test_ratio"],
  )

  print_split_summary(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
  )