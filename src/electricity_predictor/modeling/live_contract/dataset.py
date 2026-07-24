"""Build parallel modeling datasets for the selected current-hour contract."""

from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.feature_engineering import (
  add_horizon_target_features,
  build_target_column_names,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
  add_live_feature_candidates,
)


HISTORICAL_DATASET_PATH = Path(
  "data/interim/current_historical_prices_clean.csv"
)

LIVE_MODELING_DATASET_PATH = Path(
  "data/processed/live_modeling_dataset.csv"
)

LIVE_TRAINING_DATASET_PATH = Path(
  "data/processed/live_training_dataset.csv"
)

DATETIME_COLUMN = "datetime_universal_time"
LOCAL_DATETIME_COLUMN = "datetime_local_time"


def load_live_feature_source(
  path: Path = HISTORICAL_DATASET_PATH,
) -> pd.DataFrame:
  """Load and normalize the continuous hourly source dataset."""
  if not path.exists():
    raise FileNotFoundError(
      f"Historical dataset not found: {path}"
    )

  data = pd.read_csv(path)

  required_columns = {
    DATETIME_COLUMN,
    LOCAL_DATETIME_COLUMN,
    "actual_price",
    "forecast_price",
  }

  missing_columns = (
    required_columns - set(data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Historical dataset is missing columns: "
      f"{sorted(missing_columns)}"
    )

  data[DATETIME_COLUMN] = pd.to_datetime(
    data[DATETIME_COLUMN],
    utc=True,
    errors="raise",
  )

  data[LOCAL_DATETIME_COLUMN] = pd.to_datetime(
    data[LOCAL_DATETIME_COLUMN],
    errors="raise",
  )

  data["actual_price"] = pd.to_numeric(
    data["actual_price"],
    errors="coerce",
  )

  data["forecast_price"] = pd.to_numeric(
    data["forecast_price"],
    errors="coerce",
  )

  return (
    data
    .sort_values(DATETIME_COLUMN)
    .reset_index(drop=True)
  )


def ordered_unique(
  columns: list[str],
) -> list[str]:
  """Return columns in first-seen order without duplicates."""
  return list(
    dict.fromkeys(columns)
  )


def build_live_modeling_dataset(
  source_data: pd.DataFrame,
) -> pd.DataFrame:
  """Build selected live features and all five future price targets."""
  feature_data = add_live_feature_candidates(
    source_data
  )

  modeling_data = add_horizon_target_features(
    data=feature_data,
    horizons_hours=list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    ),
  )

  target_columns = build_target_column_names(
    list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  )

  output_columns = ordered_unique([
    DATETIME_COLUMN,
    LOCAL_DATETIME_COLUMN,
    "actual_price",
    "forecast_price",
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *target_columns,
  ])

  return modeling_data[
    output_columns
  ].copy()


def build_live_training_dataset(
  modeling_data: pd.DataFrame,
) -> pd.DataFrame:
  """Keep rows complete for the selected features and every target horizon."""
  target_columns = build_target_column_names(
    list(
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  )

  required_training_columns = [
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *target_columns,
  ]

  return (
    modeling_data
    .dropna(
      subset=required_training_columns,
    )
    .reset_index(drop=True)
  )


def write_dataset(
  data: pd.DataFrame,
  output_path: Path,
) -> Path:
  """Write one generated dataset to its isolated output path."""
  output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  data.to_csv(
    output_path,
    index=False,
  )

  return output_path


def build_and_write_live_datasets() -> tuple[
  Path,
  Path,
  pd.DataFrame,
  pd.DataFrame,
]:
  """Build and persist both selected-contract datasets."""
  source_data = load_live_feature_source()

  modeling_data = build_live_modeling_dataset(
    source_data
  )

  training_data = build_live_training_dataset(
    modeling_data
  )

  modeling_path = write_dataset(
    modeling_data,
    LIVE_MODELING_DATASET_PATH,
  )

  training_path = write_dataset(
    training_data,
    LIVE_TRAINING_DATASET_PATH,
  )

  return (
    modeling_path,
    training_path,
    modeling_data,
    training_data,
  )


def main() -> None:
  """Generate the isolated selected-contract datasets."""
  (
    modeling_path,
    training_path,
    modeling_data,
    training_data,
  ) = build_and_write_live_datasets()

  print(
    "selected_live_contract="
    f"{SELECTED_LIVE_FEATURE_CONTRACT}"
  )

  print(
    "selected_live_feature_count="
    f"{len(SELECTED_LIVE_FEATURE_COLUMNS)}"
  )

  print(
    f"live_modeling_rows={len(modeling_data)}"
  )

  print(
    f"live_training_rows={len(training_data)}"
  )

  print(
    f"live_modeling_dataset={modeling_path}"
  )

  print(
    f"live_training_dataset={training_path}"
  )


if __name__ == "__main__":
  main()
