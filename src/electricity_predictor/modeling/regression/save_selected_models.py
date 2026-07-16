from pathlib import Path

import joblib
import pandas as pd
import sklearn

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import build_target_column_name
from electricity_predictor.modeling.regression.feature_columns import REGRESSION_FEATURE_COLUMNS
from electricity_predictor.modeling.regression.final_test_evaluation import (
  BEST_MODEL_PATH,
  load_selected_regression_models,
  train_selected_regression_model,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


MODEL_OUTPUT_DIR = Path("models/regression")
MODEL_METADATA_PATH = MODEL_OUTPUT_DIR / "selected_regression_model_metadata.csv"

MODEL_METADATA_COLUMNS = [
  "model_name",
  "horizon_hours",
  "target_column",
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


def build_model_artifact_filename(model_name: str, horizon_hours: int) -> str:
  """Build a stable filename for one selected regression model artifact."""
  return f"selected_regression_model_{horizon_hours}h_{model_name}.joblib"


def save_model_artifact(model, output_path: Path) -> Path:
  """Save one trained model artifact with joblib."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # Joblib is the standard lightweight format for scikit-learn model artifacts.
  joblib.dump(model, output_path)

  return output_path


def build_naive_baseline_artifact(
  selected_model: dict,
  target_column: str,
) -> dict:
  """Build a serializable artifact for the selected naive baseline rule."""
  parameters = selected_model.get("model_parameters", "")
  prediction_column = "actual_price_lag_1h"

  for part in str(parameters).split(";"):
    if part.strip().startswith("prediction_column="):
      prediction_column = part.split("=", 1)[1].strip()

  return {
    "model_name": "naive_baseline",
    "model_type": "rule_baseline",
    "horizon_hours": int(selected_model["horizon_hours"]),
    "target_column": target_column,
    "prediction_column": prediction_column,
    "model_parameters": parameters,
  }


def build_model_metadata_row(
  selected_model: dict,
  target_column: str,
  artifact_path: Path,
  training_rows: int,
  training_start_utc: str = "",
  training_end_utc: str = "",
) -> dict:
  """Build one metadata row for a saved selected model."""
  return {
    "model_name": selected_model["model_name"],
    "horizon_hours": int(selected_model["horizon_hours"]),
    "target_column": target_column,
    "artifact_path": str(artifact_path),
    "training_rows": training_rows,
    # The exact ordered feature list makes future inference reproducible
    # even if REGRESSION_FEATURE_COLUMNS changes in a later phase.
    "feature_columns": "|".join(REGRESSION_FEATURE_COLUMNS),
    # Sklearn pickles are not portable across versions, so record it.
    "sklearn_version": sklearn.__version__,
    "training_start_utc": training_start_utc,
    "training_end_utc": training_end_utc,
    "selection_metric": selected_model.get("selection_metric", ""),
    "selection_rule": selected_model.get("selection_rule", ""),
    "model_parameters": selected_model.get("model_parameters", ""),
  }


def save_selected_regression_models(
  best_model_path: Path = BEST_MODEL_PATH,
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  output_dir: Path = MODEL_OUTPUT_DIR,
  metadata_path: Path = MODEL_METADATA_PATH,
) -> Path:
  """Train and save the selected regression model for each forecast horizon."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]

  selected_models = load_selected_regression_models(best_model_path)
  training_data = load_training_dataset(training_dataset_path)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  # After validation selection, the final model is trained on train + validation.
  # The test split remains excluded because it is only for final evaluation.
  final_training_data = pd.concat([train_data, validation_data], ignore_index=True)

  # Record the training window so every artifact is traceable to its data.
  training_start_utc = str(final_training_data["datetime_universal_time"].min())
  training_end_utc = str(final_training_data["datetime_universal_time"].max())

  metadata_rows = []

  for selected_model in selected_models.to_dict(orient="records"):
    horizon_hours = int(selected_model["horizon_hours"])
    target_column = build_target_column_name(horizon_hours)

    print("")
    print(f"Saving selected model: {horizon_hours}h")
    print("=" * 30)
    print(f"Model: {selected_model['model_name']}")
    print(f"Target column: {target_column}")

    if selected_model["model_name"] == "naive_baseline":
      # A naive baseline is a rule, not a trained sklearn model.
      # We save the rule description so the selected horizon still has an artifact.
      model_artifact = build_naive_baseline_artifact(
        selected_model=selected_model,
        target_column=target_column,
      )
    else:
      model_artifact = train_selected_regression_model(
        selected_model=selected_model,
        train_data=final_training_data,
        target_column=target_column,
      )

    artifact_path = output_dir / build_model_artifact_filename(
      model_name=selected_model["model_name"],
      horizon_hours=horizon_hours,
    )

    saved_path = save_model_artifact(model=model_artifact, output_path=artifact_path)

    metadata_rows.append(
      build_model_metadata_row(
        selected_model=selected_model,
        target_column=target_column,
        artifact_path=saved_path,
        training_rows=len(final_training_data),
        training_start_utc=training_start_utc,
        training_end_utc=training_end_utc,
      )
    )

  output_dir.mkdir(parents=True, exist_ok=True)

  metadata = pd.DataFrame(metadata_rows, columns=MODEL_METADATA_COLUMNS)
  metadata.to_csv(metadata_path, index=False)

  return metadata_path


def print_saved_model_summary(metadata_path: Path) -> None:
  """Print the saved model artifact summary."""
  metadata = pd.read_csv(metadata_path)

  print("")
  print("Saved selected regression models")
  print("================================")

  for _, row in metadata.iterrows():
    print(
      f"{int(row['horizon_hours'])}h | "
      f"{row['model_name']} | "
      f"{row['artifact_path']}"
    )

  print("")
  print(f"Metadata written to: {metadata_path}")


if __name__ == "__main__":
  written_metadata_path = save_selected_regression_models()
  print_saved_model_summary(written_metadata_path)
