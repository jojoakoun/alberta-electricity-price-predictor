import json
from pathlib import Path
import tarfile

import joblib
import pandas as pd

from electricity_predictor.modeling.lifecycle.release_bundle import (
  build_production_release,
  calculate_file_sha256,
)
from electricity_predictor.serving.model_registry import (
  build_legacy_registry,
  write_active_registry_atomic,
)


def write_task_bundle(
  directory: Path,
  task_name: str,
) -> Path:
  directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  artifact_path = (
    directory
    / f"{task_name}.joblib"
  )

  joblib.dump(
    {
      "task": task_name,
    },
    artifact_path,
  )

  row = {
    "model_name": (
      f"{task_name}_model"
    ),
    "horizon_hours": 1,
    "artifact_path": str(
      artifact_path
    ),
    "feature_columns": (
      "forecast_price|"
      "actual_price_lag_1h"
    ),
  }

  if task_name == "classification":
    row.update(
      {
        "spike_threshold": 157.885,
        "decision_threshold": 0.5,
      }
    )

  metadata_path = (
    directory / "metadata.csv"
  )

  pd.DataFrame(
    [row]
  ).to_csv(
    metadata_path,
    index=False,
  )

  return metadata_path


def prepare_registry(
  tmp_path: Path,
) -> Path:
  regression_metadata = (
    write_task_bundle(
      tmp_path / "source-regression",
      "regression",
    )
  )

  classification_metadata = (
    write_task_bundle(
      tmp_path / "source-classification",
      "classification",
    )
  )

  registry = build_legacy_registry(
    updated_at_utc=(
      "2026-07-20T20:00:00+00:00"
    )
  )

  registry[
    "tasks"
  ][
    "regression"
  ].update(
    {
      "model_version":
        "regression-v1",
      "metadata_path": str(
        regression_metadata
      ),
      "source": "candidate",
    }
  )

  registry[
    "tasks"
  ][
    "classification"
  ].update(
    {
      "model_version":
        "classification-v1",
      "metadata_path": str(
        classification_metadata
      ),
      "source": "legacy",
    }
  )

  registry_path = (
    tmp_path / "active_models.json"
  )

  write_active_registry_atomic(
    registry=registry,
    registry_path=registry_path,
  )

  return registry_path


def test_calculate_file_sha256_is_stable(
  tmp_path: Path,
):
  file_path = (
    tmp_path / "file.txt"
  )

  file_path.write_text(
    "wattwise\n",
    encoding="utf-8",
  )

  first = calculate_file_sha256(
    file_path
  )

  second = calculate_file_sha256(
    file_path
  )

  assert first == second
  assert len(first) == 64


def test_build_production_release_is_self_contained(
  tmp_path: Path,
):
  registry_path = prepare_registry(
    tmp_path
  )

  descriptor = (
    build_production_release(
      registry_path=registry_path,
      build_root=(
        tmp_path / "build"
      ),
      install_root=Path(
        "models/production/releases"
      ),
    )
  )

  archive_path = Path(
    descriptor[
      "archive_path"
    ]
  )

  assert archive_path.exists()

  extraction_root = (
    tmp_path / "extracted"
  )

  extraction_root.mkdir()

  with tarfile.open(
    archive_path,
    mode="r:gz",
  ) as archive:
    archive.extractall(
      extraction_root
    )

  extracted_registry_path = (
    extraction_root
    / "models"
    / "production"
    / "active_models.json"
  )

  extracted_registry = json.loads(
    extracted_registry_path.read_text(
      encoding="utf-8"
    )
  )

  release_id = descriptor[
    "release_id"
  ]

  for task_name in [
    "regression",
    "classification",
  ]:
    installed_metadata_path = Path(
      extracted_registry[
        "tasks"
      ][task_name][
        "metadata_path"
      ]
    )

    extracted_metadata_path = (
      extraction_root
      / installed_metadata_path
    )

    assert extracted_metadata_path.exists()

    metadata = pd.read_csv(
      extracted_metadata_path
    )

    installed_artifact_path = Path(
      metadata.iloc[0][
        "artifact_path"
      ]
    )

    assert (
      extraction_root
      / installed_artifact_path
    ).exists()

    assert release_id in str(
      installed_artifact_path
    )


def test_build_production_release_is_deterministic(
  tmp_path: Path,
):
  registry_path = prepare_registry(
    tmp_path
  )

  first = build_production_release(
    registry_path=registry_path,
    build_root=(
      tmp_path / "build"
    ),
  )

  second = build_production_release(
    registry_path=registry_path,
    build_root=(
      tmp_path / "build"
    ),
  )

  assert (
    first["release_id"]
    == second["release_id"]
  )

  assert (
    first["archive_sha256"]
    == second["archive_sha256"]
  )
