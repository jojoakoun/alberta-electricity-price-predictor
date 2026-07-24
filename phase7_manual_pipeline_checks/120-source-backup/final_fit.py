"""Refit frozen live model recipes on all currently available training rows."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.utils.class_weight import compute_sample_weight

from electricity_predictor.modeling.classification.spike_definition import (
  classify_spikes,
)

from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)


TRAINING_DATASET_PATH = Path(
  "data/processed/live_training_dataset.csv"
)

CANDIDATE_ROOT = Path("models/live_candidate")
FINAL_ROOT = Path("models/live_final")
TEMP_ROOT = Path("models/.live_final_tmp")

ACTIVE_REGISTRY_PATH = Path(
  "models/production/active_models.json"
)

EXPECTED_HORIZONS = {1, 3, 6, 12, 24}


def calculate_sha256(file_path: Path) -> str:
  """Calculate one artifact checksum."""

  digest = hashlib.sha256()

  with file_path.open("rb") as file:
    for chunk in iter(
      lambda: file.read(1024 * 1024),
      b"",
    ):
      digest.update(chunk)

  return digest.hexdigest()


def load_training_data() -> pd.DataFrame:
  """Load the complete selected-contract training dataset."""

  if not TRAINING_DATASET_PATH.exists():
    raise FileNotFoundError(
      f"Live training dataset not found: {TRAINING_DATASET_PATH}"
    )

  data = pd.read_csv(
    TRAINING_DATASET_PATH
  )

  data["datetime_universal_time"] = pd.to_datetime(
    data["datetime_universal_time"],
    utc=True,
    errors="raise",
  )

  required_columns = [
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *[
      f"actual_price_target_{horizon}h"
      for horizon in sorted(
        EXPECTED_HORIZONS
      )
    ],
  ]

  missing_columns = sorted(
    set(required_columns) - set(data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Live training dataset is missing columns: "
      f"{missing_columns}"
    )

  if data[required_columns].isna().any(axis=None):
    raise ValueError(
      "Live training dataset contains missing required values."
    )

  if len(data) <= 43602:
    raise ValueError(
      "Final fit must contain more rows than the validated candidate."
    )

  return data.sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)


def load_candidate_metadata(
  task: str,
) -> pd.DataFrame:
  """Load and validate one candidate metadata table."""

  metadata_path = (
    CANDIDATE_ROOT
    / f"{task}_metadata.csv"
  )

  if not metadata_path.exists():
    raise FileNotFoundError(
      f"Candidate metadata not found: {metadata_path}"
    )

  metadata = pd.read_csv(metadata_path)

  if len(metadata) != 5:
    raise ValueError(
      f"{task} metadata must contain five rows."
    )

  horizons = {
    int(value)
    for value in metadata["horizon_hours"]
  }

  if horizons != EXPECTED_HORIZONS:
    raise ValueError(
      f"{task} metadata has invalid horizons: {horizons}"
    )

  return metadata.sort_values(
    "horizon_hours"
  ).reset_index(drop=True)


def fit_regression_models(
  data: pd.DataFrame,
  metadata: pd.DataFrame,
) -> pd.DataFrame:
  """Refit the five frozen regression estimators."""
  features = data[
    SELECTED_LIVE_FEATURE_COLUMNS
  ]

  rows: list[dict] = []

  training_start = (
    data[
      "datetime_universal_time"
    ].min().isoformat()
  )

  training_end = (
    data[
      "datetime_universal_time"
    ].max().isoformat()
  )

  for source_row in metadata.to_dict(
    orient="records"
  ):
    horizon = int(
      source_row["horizon_hours"]
    )

    source_artifact_path = Path(
      source_row["artifact_path"]
    )

    if not source_artifact_path.exists():
      raise FileNotFoundError(
        "Candidate regression artifact "
        f"is missing: {source_artifact_path}"
      )

    estimator = clone(
      joblib.load(
        source_artifact_path
      )
    )

    target_column = (
      f"actual_price_target_{horizon}h"
    )

    estimator.fit(
      features,
      data[target_column],
    )

    filename = (
      f"regression_{horizon}h.joblib"
    )

    temporary_artifact_path = (
      TEMP_ROOT / filename
    )

    final_artifact_path = (
      FINAL_ROOT / filename
    )

    joblib.dump(
      estimator,
      temporary_artifact_path,
    )

    row = dict(
      source_row
    )

    row.update({
      "artifact_path":
        str(final_artifact_path),
      "artifact_sha256":
        calculate_sha256(
          temporary_artifact_path
        ),
      "feature_columns":
        "|".join(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "feature_count":
        len(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "training_rows":
        len(data),
      "training_start_utc":
        training_start,
      "training_end_utc":
        training_end,
      "sklearn_version":
        sklearn.__version__,
      "final_fit":
        True,
      "protected_test_evaluated":
        False,
    })

    rows.append(
      row
    )

  return pd.DataFrame(
    rows
  )


def fit_classification_models(
  data: pd.DataFrame,
  metadata: pd.DataFrame,
) -> pd.DataFrame:
  """Refit the five frozen and balanced spike classifiers."""
  features = data[
    SELECTED_LIVE_FEATURE_COLUMNS
  ]

  rows: list[dict] = []

  training_start = (
    data[
      "datetime_universal_time"
    ].min().isoformat()
  )

  training_end = (
    data[
      "datetime_universal_time"
    ].max().isoformat()
  )

  for source_row in metadata.to_dict(
    orient="records"
  ):
    horizon = int(
      source_row["horizon_hours"]
    )

    source_artifact_path = Path(
      source_row["artifact_path"]
    )

    if not source_artifact_path.exists():
      raise FileNotFoundError(
        "Candidate classification artifact "
        f"is missing: {source_artifact_path}"
      )

    estimator = clone(
      joblib.load(
        source_artifact_path
      )
    )

    price_target_column = (
      f"actual_price_target_{horizon}h"
    )

    spike_threshold = float(
      source_row["spike_threshold"]
    )

    target = classify_spikes(
      prices=data[
        price_target_column
      ],
      threshold=spike_threshold,
    )

    if target.nunique() != 2:
      raise ValueError(
        f"Classification horizon {horizon}h "
        "does not contain both classes."
      )

    sample_weight = (
      compute_sample_weight(
        class_weight="balanced",
        y=target,
      )
    )

    estimator.fit(
      features,
      target,
      sample_weight=sample_weight,
    )

    filename = (
      f"classification_{horizon}h.joblib"
    )

    temporary_artifact_path = (
      TEMP_ROOT / filename
    )

    final_artifact_path = (
      FINAL_ROOT / filename
    )

    joblib.dump(
      estimator,
      temporary_artifact_path,
    )

    row = dict(
      source_row
    )

    row.update({
      "artifact_path":
        str(final_artifact_path),
      "artifact_sha256":
        calculate_sha256(
          temporary_artifact_path
        ),
      "class_weight_strategy":
        "balanced",
      "feature_columns":
        "|".join(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "feature_count":
        len(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "training_rows":
        len(data),
      "training_start_utc":
        training_start,
      "training_end_utc":
        training_end,
      "sklearn_version":
        sklearn.__version__,
      "final_fit":
        True,
      "protected_test_evaluated":
        False,
    })

    rows.append(
      row
    )

  return pd.DataFrame(
    rows
  )


def write_manifest(
  data: pd.DataFrame,
  regression_metadata: pd.DataFrame,
  classification_metadata: pd.DataFrame,
) -> None:
  """Write checksums and final-fit provenance."""

  artifacts = []

  combined_metadata = pd.concat(
    [
      regression_metadata.assign(
        task="regression"
      ),
      classification_metadata.assign(
        task="classification"
      ),
    ],
    ignore_index=True,
  )

  for row in combined_metadata.to_dict(
    orient="records"
  ):
    final_path = Path(
      row["artifact_path"]
    )

    temporary_path = (
      TEMP_ROOT / final_path.name
    )

    artifacts.append({
      "task": row["task"],
      "horizon_hours": int(
        row["horizon_hours"]
      ),
      "artifact_path": str(final_path),
      "sha256": calculate_sha256(
        temporary_path
      ),
    })

  manifest = {
    "created_at_utc": (
      datetime.now(timezone.utc)
      .isoformat()
    ),
    "selected_live_contract": (
      SELECTED_LIVE_FEATURE_CONTRACT
    ),
    "selected_live_feature_count": len(
      SELECTED_LIVE_FEATURE_COLUMNS
    ),
    "feature_columns": (
      SELECTED_LIVE_FEATURE_COLUMNS
    ),
    "training_rows": len(data),
    "training_start_utc": (
      data[
        "datetime_universal_time"
      ].min().isoformat()
    ),
    "training_end_utc": (
      data[
        "datetime_universal_time"
      ].max().isoformat()
    ),
    "artifact_count": len(artifacts),
    "artifacts": artifacts,
    "hyperparameters_frozen": True,
    "decision_thresholds_frozen": True,
    "spike_thresholds_frozen": True,
    "protected_test_evaluated": False,
  }

  (
    TEMP_ROOT / "manifest.json"
  ).write_text(
    json.dumps(
      manifest,
      indent=2,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
  )


def activate_final_models() -> None:
  """Archive and atomically activate both live model tasks."""
  if not ACTIVE_REGISTRY_PATH.exists():
    raise FileNotFoundError(
      "Active production registry is missing: "
      f"{ACTIVE_REGISTRY_PATH}"
    )

  registry = json.loads(
    ACTIVE_REGISTRY_PATH.read_text(
      encoding="utf-8"
    )
  )

  tasks = registry.get(
    "tasks"
  )

  if not isinstance(
    tasks,
    dict,
  ):
    raise ValueError(
      "Active registry is missing its tasks object."
    )

  for task_name in (
    "regression",
    "classification",
  ):
    if task_name not in tasks:
      raise ValueError(
        "Active registry is missing task: "
        f"{task_name}"
      )

  activated_at = (
    datetime.now(
      timezone.utc
    ).isoformat()
  )

  version = (
    "live-final-"
    + datetime.now(
      timezone.utc
    ).strftime(
      "%Y%m%dT%H%M%SZ"
    )
  )

  history_directory = (
    ACTIVE_REGISTRY_PATH.parent
    / "history"
  )

  history_directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  history_path = (
    history_directory
    / (
      datetime.now(
        timezone.utc
      ).strftime(
        "%Y%m%dT%H%M%SZ"
      )
      + "-active_models.json"
    )
  )

  history_path.write_text(
    json.dumps(
      registry,
      indent=2,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
  )

  tasks[
    "regression"
  ]["metadata_path"] = str(
    FINAL_ROOT
    / "regression_metadata.csv"
  )

  tasks[
    "classification"
  ]["metadata_path"] = str(
    FINAL_ROOT
    / "classification_metadata.csv"
  )

  for task_name in (
    "regression",
    "classification",
  ):
    tasks[
      task_name
    ]["source"] = "live_final"

    tasks[
      task_name
    ]["model_version"] = version

    tasks[
      task_name
    ]["promoted_at_utc"] = (
      activated_at
    )

    tasks[
      task_name
    ].pop(
      "active_version",
      None,
    )

  registry[
    "updated_at_utc"
  ] = activated_at

  temporary_registry_path = (
    ACTIVE_REGISTRY_PATH.with_suffix(
      ".json.tmp"
    )
  )

  temporary_registry_path.write_text(
    json.dumps(
      registry,
      indent=2,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
  )

  os.replace(
    temporary_registry_path,
    ACTIVE_REGISTRY_PATH,
  )


def run_final_fit() -> dict:
  """Build, verify, install, and activate the final local bundle."""

  data = load_training_data()

  regression_candidate_metadata = (
    load_candidate_metadata(
      "regression"
    )
  )

  classification_candidate_metadata = (
    load_candidate_metadata(
      "classification"
    )
  )

  if TEMP_ROOT.exists():
    shutil.rmtree(TEMP_ROOT)

  TEMP_ROOT.mkdir(
    parents=True,
    exist_ok=False,
  )

  regression_metadata = (
    fit_regression_models(
      data=data,
      metadata=(
        regression_candidate_metadata
      ),
    )
  )

  classification_metadata = (
    fit_classification_models(
      data=data,
      metadata=(
        classification_candidate_metadata
      ),
    )
  )

  regression_metadata.to_csv(
    TEMP_ROOT
    / "regression_metadata.csv",
    index=False,
  )

  classification_metadata.to_csv(
    TEMP_ROOT
    / "classification_metadata.csv",
    index=False,
  )

  write_manifest(
    data=data,
    regression_metadata=(
      regression_metadata
    ),
    classification_metadata=(
      classification_metadata
    ),
  )

  for artifact_path in [
    *regression_metadata[
      "artifact_path"
    ].tolist(),
    *classification_metadata[
      "artifact_path"
    ].tolist(),
  ]:
    temporary_path = (
      TEMP_ROOT
      / Path(artifact_path).name
    )

    loaded_artifact = joblib.load(
      temporary_path
    )

    if not hasattr(
      loaded_artifact,
      "predict",
    ):
      raise ValueError(
        "Final artifact is not loadable as "
        f"a predictor: {temporary_path}"
      )

  if FINAL_ROOT.exists():
    shutil.rmtree(FINAL_ROOT)

  TEMP_ROOT.rename(FINAL_ROOT)

  activate_final_models()

  return {
    "selected_live_contract": (
      SELECTED_LIVE_FEATURE_CONTRACT
    ),
    "training_rows": len(data),
    "training_start_utc": (
      data[
        "datetime_universal_time"
      ].min().isoformat()
    ),
    "training_end_utc": (
      data[
        "datetime_universal_time"
      ].max().isoformat()
    ),
    "regression_models": len(
      regression_metadata
    ),
    "classification_models": len(
      classification_metadata
    ),
    "artifacts": (
      len(regression_metadata)
      + len(classification_metadata)
    ),
    "active_registry": str(
      ACTIVE_REGISTRY_PATH
    ),
    "protected_test_evaluated": False,
  }


def main() -> None:
  """Run the final local model fit."""

  result = run_final_fit()

  print("LIVE FINAL MODEL FIT")
  print("====================")

  for key, value in result.items():
    print(f"{key}={value}")


if __name__ == "__main__":
  main()
