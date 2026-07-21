"""Load active artifacts and produce one provenance-aware horizon forecast."""

from pathlib import Path

import joblib
import pandas as pd

from electricity_predictor.features.feature_columns import (
  parse_model_feature_columns,
)
from electricity_predictor.serving.model_registry import (
  ACTIVE_MODEL_REGISTRY_PATH,
  resolve_active_metadata_paths,
)


# Research decision tools historically import this name from serving. Keep the
# public alias while all parsing behavior lives in the shared feature contract.
parse_feature_columns = parse_model_feature_columns


def load_model_metadata(
  metadata_path: Path,
  required_columns: set[str],
) -> pd.DataFrame:
  """Load and validate one selected-model metadata file."""
  if not metadata_path.exists():
    raise FileNotFoundError(
      f"Model metadata file not found: {metadata_path}"
    )

  metadata = pd.read_csv(metadata_path)
  missing_columns = required_columns - set(metadata.columns)

  if missing_columns:
    raise ValueError(
      f"Model metadata is missing columns: {sorted(missing_columns)}"
    )

  if metadata.empty:
    raise ValueError(f"Model metadata is empty: {metadata_path}")

  return metadata


def prepare_feature_row(
  features: dict,
  feature_columns: list[str],
) -> pd.DataFrame:
  """Validate and order one inference feature row."""
  missing_columns = [
    column
    for column in feature_columns
    if column not in features
  ]

  if missing_columns:
    raise ValueError(
      f"Inference features are missing columns: {missing_columns}"
    )

  ordered_features = {
    column: features[column]
    for column in feature_columns
  }

  feature_row = pd.DataFrame([ordered_features])

  if feature_row.isna().any().any():
    raise ValueError("Inference features cannot contain missing values.")

  return feature_row


def select_horizon_metadata(
  metadata: pd.DataFrame,
  horizon_hours: int,
) -> dict:
  """Select exactly one artifact metadata row for one horizon."""
  matching_rows = metadata[
    metadata["horizon_hours"].astype(int) == int(horizon_hours)
  ]

  if matching_rows.empty:
    raise ValueError(
      f"No selected model found for horizon: {horizon_hours}h"
    )

  if len(matching_rows) > 1:
    raise ValueError(
      f"Multiple selected models found for horizon: {horizon_hours}h"
    )

  return matching_rows.iloc[0].to_dict()


def load_artifact(metadata_row: dict):
  """Load the artifact referenced by one metadata row."""
  artifact_path = Path(str(metadata_row["artifact_path"]))

  if not artifact_path.exists():
    raise FileNotFoundError(
      f"Model artifact not found: {artifact_path}"
    )

  return joblib.load(artifact_path)


def predict_regression_value(
  artifact,
  metadata_row: dict,
  feature_row: pd.DataFrame,
) -> float:
  """Generate one price forecast from an estimator or rule baseline."""
  if isinstance(artifact, dict):
    if artifact.get("model_type") != "rule_baseline":
      raise ValueError("Unsupported regression artifact dictionary.")

    prediction_column = artifact.get("prediction_column")

    if prediction_column not in feature_row.columns:
      raise ValueError(
        f"Regression baseline requires feature: {prediction_column}"
      )

    return float(feature_row.iloc[0][prediction_column])

  if not hasattr(artifact, "predict"):
    raise ValueError(
      f"Regression artifact for {metadata_row['model_name']} "
      "does not support predict()."
    )

  prediction = artifact.predict(feature_row)

  return float(prediction[0])


def get_forecast_kind(artifact) -> str:
  """Return the provenance carried with one regression output.

  A persistence rule remains visible as a reference forecast, but downstream
  product logic can use this provenance to keep it out of savings claims.
  """
  if (
    isinstance(artifact, dict)
    and artifact.get("model_type") == "rule_baseline"
    and artifact.get("prediction_column")
    == "actual_price_lag_1h"
  ):
    return "persistence_reference"

  return "model_forecast"


def predict_classification_value(
  artifact,
  metadata_row: dict,
  feature_row: pd.DataFrame,
) -> tuple[float, float, bool]:
  """Generate spike probability and binary decision."""
  decision_threshold = metadata_row.get("decision_threshold")

  if isinstance(artifact, dict):
    if artifact.get("model_type") != "rule_baseline":
      raise ValueError("Unsupported classification artifact dictionary.")

    prediction_column = artifact.get("prediction_column")
    spike_threshold = float(metadata_row["spike_threshold"])

    if prediction_column not in feature_row.columns:
      raise ValueError(
        f"Classification baseline requires feature: {prediction_column}"
      )

    is_spike = bool(
      float(feature_row.iloc[0][prediction_column]) > spike_threshold
    )

    # Rule baselines produce binary output, so 0.5 is the display convention.
    if pd.isna(decision_threshold):
      decision_threshold = 0.5
    else:
      decision_threshold = float(decision_threshold)

    spike_probability = float(is_spike)

    return spike_probability, decision_threshold, is_spike

  if pd.isna(decision_threshold):
    raise ValueError(
      "Classification metadata is missing decision_threshold."
    )

  decision_threshold = float(decision_threshold)

  if not hasattr(artifact, "predict_proba"):
    raise ValueError(
      f"Classification artifact for {metadata_row['model_name']} "
      "does not support predict_proba()."
    )

  spike_probability = float(
    artifact.predict_proba(feature_row)[0, 1]
  )
  is_spike = spike_probability >= decision_threshold

  return spike_probability, decision_threshold, bool(is_spike)


def predict_horizon(
  horizon_hours: int,
  features: dict,
  regression_metadata_path: Path | None = None,
  classification_metadata_path: Path | None = None,
  active_registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
) -> dict:
  """Generate price and spike-risk predictions for one forecast horizon."""
  if (
    regression_metadata_path is None
    or classification_metadata_path is None
  ):
    (
      active_regression_path,
      active_classification_path,
      _,
    ) = resolve_active_metadata_paths(
      registry_path=active_registry_path
    )

    if regression_metadata_path is None:
      regression_metadata_path = (
        active_regression_path
      )

    if classification_metadata_path is None:
      classification_metadata_path = (
        active_classification_path
      )

  regression_metadata = load_model_metadata(
    metadata_path=regression_metadata_path,
    required_columns={
      "model_name",
      "horizon_hours",
      "artifact_path",
      "feature_columns",
    },
  )
  classification_metadata = load_model_metadata(
    metadata_path=classification_metadata_path,
    required_columns={
      "model_name",
      "horizon_hours",
      "artifact_path",
      "feature_columns",
      "spike_threshold",
      "decision_threshold",
    },
  )

  regression_row = select_horizon_metadata(
    metadata=regression_metadata,
    horizon_hours=horizon_hours,
  )
  classification_row = select_horizon_metadata(
    metadata=classification_metadata,
    horizon_hours=horizon_hours,
  )

  regression_features = parse_model_feature_columns(
    regression_row["feature_columns"]
  )
  classification_features = parse_model_feature_columns(
    classification_row["feature_columns"]
  )

  # Each artifact receives features in the exact order recorded at training.
  regression_feature_row = prepare_feature_row(
    features=features,
    feature_columns=regression_features,
  )
  classification_feature_row = prepare_feature_row(
    features=features,
    feature_columns=classification_features,
  )

  regression_artifact = load_artifact(regression_row)
  classification_artifact = load_artifact(classification_row)

  predicted_price = predict_regression_value(
    artifact=regression_artifact,
    metadata_row=regression_row,
    feature_row=regression_feature_row,
  )
  (
    spike_probability,
    decision_threshold,
    is_spike,
  ) = predict_classification_value(
    artifact=classification_artifact,
    metadata_row=classification_row,
    feature_row=classification_feature_row,
  )

  return {
    "horizon_hours": int(horizon_hours),
    "predicted_price": predicted_price,
    "spike_probability": spike_probability,
    "decision_threshold": decision_threshold,
    "is_spike": is_spike,
    "spike_threshold": float(
      classification_row["spike_threshold"]
    ),
    "regression_model": regression_row["model_name"],
    "classification_model": classification_row["model_name"],
    "forecast_kind": get_forecast_kind(
      regression_artifact
    ),
  }
