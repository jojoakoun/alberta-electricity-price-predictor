from pathlib import Path

import joblib
import pandas as pd
import sklearn

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.classification.final_test_evaluation import (
  BEST_MODEL_PATH,
  load_selected_classification_models,
  train_selected_classification_model,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_splits,
)
from electricity_predictor.modeling.regression.feature_columns import (
  REGRESSION_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data,
)


MODEL_OUTPUT_DIR = Path("models/classification")
MODEL_METADATA_PATH = (
  MODEL_OUTPUT_DIR / "selected_classification_model_metadata.csv"
)

MODEL_METADATA_COLUMNS = [
  "model_name",
  "horizon_hours",
  "target_column",
  "spike_threshold",
  "artifact_path",
  "training_rows",
  "feature_columns",
  "sklearn_version",
  "training_start_utc",
  "training_end_utc",
  "selection_metric",
  "selection_rule",
  "model_parameters",
]


def build_model_artifact_filename(
  model_name: str,
  horizon_hours: int,
) -> str:
  """Build a stable selected-classifier artifact filename."""
  return (
    f"selected_classification_model_"
    f"{horizon_hours}h_{model_name}.joblib"
  )


def save_model_artifact(model, output_path: Path) -> Path:
  """Save one classification model or rule artifact."""
  output_path.parent.mkdir(parents=True, exist_ok=True)
  joblib.dump(model, output_path)

  return output_path


def build_naive_spike_baseline_artifact(
  selected_model: dict,
  target_column: str,
  threshold: float,
) -> dict:
  """Build a serializable naive spike baseline rule."""
  return {
    "model_name": "naive_spike_baseline",
    "model_type": "rule_baseline",
    "horizon_hours": int(selected_model["horizon_hours"]),
    "target_column": target_column,
    "prediction_column": "actual_price_lag_1h",
    "spike_threshold": threshold,
    "model_parameters": selected_model.get(
      "model_parameters",
      "",
    ),
  }


def build_model_metadata_row(
  selected_model: dict,
  target_column: str,
  threshold: float,
  artifact_path: Path,
  training_rows: int,
  training_start_utc: str,
  training_end_utc: str,
) -> dict:
  """Build metadata for one selected classification artifact."""
  return {
    "model_name": selected_model["model_name"],
    "horizon_hours": int(selected_model["horizon_hours"]),
    "target_column": target_column,
    "spike_threshold": threshold,
    "artifact_path": str(artifact_path),
    "training_rows": training_rows,
    "feature_columns": "|".join(
      REGRESSION_FEATURE_COLUMNS
    ),
    "sklearn_version": sklearn.__version__,
    "training_start_utc": training_start_utc,
    "training_end_utc": training_end_utc,
    "selection_metric": selected_model.get(
      "selection_metric",
      "",
    ),
    "selection_rule": selected_model.get(
      "selection_rule",
      "",
    ),
    "model_parameters": selected_model.get(
      "model_parameters",
      "",
    ),
  }


def save_selected_classification_models(
  best_model_path: Path = BEST_MODEL_PATH,
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  output_dir: Path = MODEL_OUTPUT_DIR,
  metadata_path: Path = MODEL_METADATA_PATH,
) -> Path:
  """Train and save the selected classifier for each horizon."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  selected_models = load_selected_classification_models(
    best_model_path
  )
  training_data = load_training_dataset(
    training_dataset_path
  )

  train_data, validation_data, test_data = split_time_series_data(
    data=training_data,
    train_ratio=modeling_config["train_ratio"],
    validation_ratio=modeling_config["validation_ratio"],
    test_ratio=modeling_config["test_ratio"],
  )

  (
    prepared_train,
    prepared_validation,
    _,
    threshold,
  ) = prepare_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=horizons_hours,
  )

  final_training_data = pd.concat(
    [prepared_train, prepared_validation],
    ignore_index=True,
  )

  training_start_utc = str(
    final_training_data["datetime_universal_time"].min()
  )
  training_end_utc = str(
    final_training_data["datetime_universal_time"].max()
  )

  metadata_rows = []

  for selected_model in selected_models.to_dict(
    orient="records"
  ):
    horizon_hours = int(selected_model["horizon_hours"])
    target_column = build_spike_target_column_name(
      horizon_hours
    )

    print("")
    print(f"Saving selected classifier: {horizon_hours}h")
    print("=" * 38)
    print(f"Model: {selected_model['model_name']}")
    print(f"Target column: {target_column}")

    if selected_model["model_name"] == "naive_spike_baseline":
      artifact = build_naive_spike_baseline_artifact(
        selected_model=selected_model,
        target_column=target_column,
        threshold=threshold,
      )
    else:
      artifact = train_selected_classification_model(
        selected_model=selected_model,
        train_data=final_training_data,
        target_column=target_column,
      )

    artifact_path = output_dir / build_model_artifact_filename(
      model_name=selected_model["model_name"],
      horizon_hours=horizon_hours,
    )

    saved_path = save_model_artifact(
      model=artifact,
      output_path=artifact_path,
    )

    metadata_rows.append(
      build_model_metadata_row(
        selected_model=selected_model,
        target_column=target_column,
        threshold=threshold,
        artifact_path=saved_path,
        training_rows=len(final_training_data),
        training_start_utc=training_start_utc,
        training_end_utc=training_end_utc,
      )
    )

  output_dir.mkdir(parents=True, exist_ok=True)

  pd.DataFrame(
    metadata_rows,
    columns=MODEL_METADATA_COLUMNS,
  ).to_csv(
    metadata_path,
    index=False,
  )

  return metadata_path


def print_saved_classification_model_summary(
  metadata_path: Path,
) -> None:
  """Print saved selected classification artifacts."""
  metadata = pd.read_csv(metadata_path)

  print("")
  print("Saved selected classification models")
  print("====================================")

  for _, row in metadata.iterrows():
    print(
      f"{int(row['horizon_hours'])}h | "
      f"{row['model_name']} | "
      f"{row['artifact_path']}"
    )

  print("")
  print(f"Metadata written to: {metadata_path}")


if __name__ == "__main__":
  written_path = save_selected_classification_models()

  print_saved_classification_model_summary(
    metadata_path=written_path,
  )
