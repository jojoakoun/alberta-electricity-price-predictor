from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import ENGINEERED_FEATURE_COLUMNS


def load_modeling_dataset(file_path: Path) -> pd.DataFrame:
  """Load the modeling dataset used as input for training data preparation."""

  if not file_path.exists():
    raise FileNotFoundError(f"Modeling dataset not found: {file_path}")

  return pd.read_csv(file_path)

def build_training_dataset(data: pd.DataFrame) -> pd.DataFrame:
  """Build a model-ready training dataset from the modeling dataset."""
  data = data.copy()

  # Rows with missing engineered features cannot be used by the first model.
  data = data.dropna(subset=ENGINEERED_FEATURE_COLUMNS)

  return data.reset_index(drop=True)


def write_training_dataset(data: pd.DataFrame, output_path: Path) -> Path:
  """Write the training dataset to a CSV file."""

  # Create the processed data folder if it does not exist yet.
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # Save the clean training dataset for baseline model development.
  data.to_csv(output_path, index=False)

  return output_path



if __name__ == "__main__":
  modeling_dataset_path = Path("data/processed/modeling_dataset.csv")
  training_dataset_path = Path("data/processed/training_dataset.csv")
  modeling_data = load_modeling_dataset(modeling_dataset_path)
  training_data = build_training_dataset(modeling_data)
  written_path = write_training_dataset(training_data, training_dataset_path)

  print(f"Training dataset written to: {written_path}")
  print(f"Rows: {training_data.shape[0]:,}")
  print(f"Columns: {training_data.shape[1]}")
