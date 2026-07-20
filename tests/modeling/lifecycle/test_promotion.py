import json
from pathlib import Path

import joblib
import pandas as pd
import pytest

from electricity_predictor.modeling.lifecycle.promotion import (
  promote_candidate_tasks,
)
from electricity_predictor.serving.model_registry import (
  build_legacy_registry,
  read_active_registry,
  write_active_registry_atomic,
)


HORIZONS = [
  1,
  3,
  6,
  12,
  24,
]


def write_metadata_bundle(
  directory: Path,
  task_name: str,
) -> Path:
  directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  rows = []

  for horizon in HORIZONS:
    artifact_path = (
      directory
      / f"{task_name}-{horizon}.joblib"
    )

    joblib.dump(
      {
        "model_type": "rule_baseline",
        "prediction_column":
          "actual_price_lag_1h",
      },
      artifact_path,
    )

    row = {
      "model_name": (
        f"{task_name}_model"
      ),
      "horizon_hours": horizon,
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

    rows.append(row)

  metadata_path = (
    directory / "metadata.csv"
  )

  pd.DataFrame(
    rows
  ).to_csv(
    metadata_path,
    index=False,
  )

  return metadata_path


def prepare_promotion_fixture(
  tmp_path: Path,
) -> tuple[Path, Path, Path]:
  legacy_regression = (
    write_metadata_bundle(
      tmp_path / "legacy-regression",
      "regression",
    )
  )

  legacy_classification = (
    write_metadata_bundle(
      tmp_path / "legacy-classification",
      "classification",
    )
  )

  candidate_regression = (
    write_metadata_bundle(
      tmp_path / "candidate-regression",
      "regression",
    )
  )

  candidate_classification = (
    write_metadata_bundle(
      tmp_path / "candidate-classification",
      "classification",
    )
  )

  registry = build_legacy_registry()

  registry[
    "tasks"
  ][
    "regression"
  ][
    "metadata_path"
  ] = str(
    legacy_regression
  )

  registry[
    "tasks"
  ][
    "classification"
  ][
    "metadata_path"
  ] = str(
    legacy_classification
  )

  registry_path = (
    tmp_path / "active.json"
  )

  write_active_registry_atomic(
    registry=registry,
    registry_path=registry_path,
  )

  candidate_manifest = {
    "schema_version": 1,
    "status": "evaluated",
    "model_version": (
      "candidate-test-version"
    ),
    "tasks": {
      "regression": {
        "status": "completed",
        "metadata_path": str(
          candidate_regression
        ),
      },
      "classification": {
        "status": "completed",
        "metadata_path": str(
          candidate_classification
        ),
      },
    },
    "comparison": {
      "regression_gate_pass": True,
      "classification_gate_pass": False,
    },
  }

  candidate_manifest_path = (
    tmp_path / "candidate.json"
  )

  candidate_manifest_path.write_text(
    json.dumps(
      candidate_manifest
    ),
    encoding="utf-8",
  )

  return (
    candidate_manifest_path,
    registry_path,
    legacy_classification,
  )


def test_promote_regression_preserves_classification(
  tmp_path: Path,
):
  (
    candidate_manifest_path,
    registry_path,
    legacy_classification,
  ) = prepare_promotion_fixture(
    tmp_path
  )

  (
    _,
    history_path,
    registry,
  ) = promote_candidate_tasks(
    candidate_manifest_path=(
      candidate_manifest_path
    ),
    task_names=[
      "regression",
    ],
    registry_path=registry_path,
    history_directory=(
      tmp_path / "history"
    ),
  )

  assert history_path.exists()

  assert (
    registry[
      "tasks"
    ][
      "regression"
    ][
      "model_version"
    ]
    == "candidate-test-version"
  )

  assert (
    registry[
      "tasks"
    ][
      "classification"
    ][
      "metadata_path"
    ]
    == str(
      legacy_classification
    )
  )

  loaded = read_active_registry(
    registry_path=registry_path
  )

  assert (
    loaded[
      "tasks"
    ][
      "regression"
    ][
      "source"
    ]
    == "candidate"
  )


def test_classification_failed_gate_cannot_promote(
  tmp_path: Path,
):
  (
    candidate_manifest_path,
    registry_path,
    _,
  ) = prepare_promotion_fixture(
    tmp_path
  )

  with pytest.raises(
    ValueError,
    match="classification promotion gate",
  ):
    promote_candidate_tasks(
      candidate_manifest_path=(
        candidate_manifest_path
      ),
      task_names=[
        "classification",
      ],
      registry_path=registry_path,
      history_directory=(
        tmp_path / "history"
      ),
    )
