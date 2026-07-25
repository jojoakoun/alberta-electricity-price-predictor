from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)
from electricity_predictor.modeling.lifecycle import (
  live_candidate_training as training,
)
from electricity_predictor.modeling.lifecycle.candidate_run import (
  write_json_file,
)
from electricity_predictor.modeling.live_contract.live_model_datasets import (
  DATETIME_COLUMN,
)


def build_training_frame(
  start: str,
  row_count: int,
  marker: float,
) -> pd.DataFrame:
  """Build complete live rows for lifecycle training tests."""
  timestamps = pd.date_range(
    start=start,
    periods=row_count,
    freq="h",
    tz="UTC",
  )

  data = pd.DataFrame({
    column: [
      marker + row_index
      for row_index in range(
        row_count
      )
    ]
    for column in (
      SELECTED_LIVE_FEATURE_COLUMNS
    )
  })

  data[
    DATETIME_COLUMN
  ] = timestamps

  data[
    "source_marker"
  ] = marker

  for horizon in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    data[
      f"actual_price_target_{horizon}h"
    ] = [
      marker
      + horizon
      + row_index
      for row_index in range(
        row_count
      )
    ]

  return data


def build_candidate_manifest(
  tmp_path: Path,
) -> tuple[
  Path,
  dict,
]:
  """Create one prepared candidate manifest."""
  candidate_directory = (
    tmp_path
    / "candidate-v1"
  )

  manifest = {
    "schema_version": 1,
    "model_version":
      "candidate-v1",
    "status":
      "prepared",
    "candidate_directory":
      str(
        candidate_directory
      ),
    "frozen_split_manifest_path":
      str(
        candidate_directory
        / "split_manifest.json"
      ),
    "tasks": {
      "regression": {
        "status":
          "pending",
        "artifact_directory":
          str(
            candidate_directory
            / "regression"
          ),
        "metadata_path":
          str(
            candidate_directory
            / "regression"
            / "selected_regression_model_metadata.csv"
          ),
      },
      "classification": {
        "status":
          "pending",
        "artifact_directory":
          str(
            candidate_directory
            / "classification"
          ),
        "metadata_path":
          str(
            candidate_directory
            / "classification"
            / "selected_classification_model_metadata.csv"
          ),
      },
    },
    "current_champion": {
      "status":
        "no_active_models",
    },
  }

  manifest_path = (
    candidate_directory
    / "candidate_manifest.json"
  )

  write_json_file(
    content=manifest,
    file_path=manifest_path,
  )

  return (
    manifest_path,
    manifest,
  )


def build_result_tables() -> tuple[
  pd.DataFrame,
  pd.DataFrame,
]:
  """Build five-horizon selected result tables."""
  regression_rows = []
  classification_rows = []

  for horizon in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    regression_rows.append({
      "contract":
        SELECTED_LIVE_FEATURE_CONTRACT,
      "horizon_hours":
        horizon,
    })

    classification_rows.append({
      "contract":
        SELECTED_LIVE_FEATURE_CONTRACT,
      "horizon_hours":
        horizon,
      "spike_threshold":
        170.77,
    })

  return (
    pd.DataFrame(
      regression_rows
    ),
    pd.DataFrame(
      classification_rows
    ),
  )


def create_metadata_rows(
  task_name: str,
  artifact_directory: Path,
) -> list[dict]:
  """Create five fake artifact files and matching metadata."""
  metadata_rows = []

  artifact_directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  for horizon in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    artifact_path = (
      artifact_directory
      / f"{task_name}_{horizon}h.joblib"
    )

    artifact_path.write_bytes(
      b"fake-model"
    )

    row = {
      "task":
        task_name,
      "contract":
        SELECTED_LIVE_FEATURE_CONTRACT,
      "horizon_hours":
        horizon,
      "artifact_path":
        str(
          artifact_path
        ),
      "artifact_sha256":
        "test-sha256",
      "feature_columns":
        "|".join(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
    }

    if task_name == "classification":
      row[
        "spike_threshold"
      ] = 170.77

    metadata_rows.append(
      row
    )

  return metadata_rows


def test_live_lifecycle_training_uses_only_train_and_validation(
  tmp_path,
  monkeypatch,
):
  manifest_path, manifest = (
    build_candidate_manifest(
      tmp_path
    )
  )

  train_data = build_training_frame(
    start="2026-01-01T00:00:00Z",
    row_count=3,
    marker=10.0,
  )

  validation_data = build_training_frame(
    start="2026-01-02T00:00:00Z",
    row_count=2,
    marker=20.0,
  )

  protected_test_data = build_training_frame(
    start="2026-01-03T00:00:00Z",
    row_count=4,
    marker=999.0,
  )

  regression_results, classification_results = (
    build_result_tables()
  )

  captured_training_markers = []
  captured_directories = {}

  def fake_load_selected_results(
    path,
    task_name,
    required_columns,
  ):
    if task_name == "Regression":
      return regression_results

    return classification_results

  def fake_train_regression_candidates(
    training_data,
    results,
    artifact_directory,
  ):
    captured_training_markers.append(
      set(
        training_data[
          "source_marker"
        ]
      )
    )

    captured_directories[
      "regression"
    ] = artifact_directory

    return create_metadata_rows(
      task_name="regression",
      artifact_directory=artifact_directory,
    )

  def fake_train_classification_candidates(
    training_data,
    results,
    artifact_directory,
  ):
    captured_training_markers.append(
      set(
        training_data[
          "source_marker"
        ]
      )
    )

    captured_directories[
      "classification"
    ] = artifact_directory

    return create_metadata_rows(
      task_name="classification",
      artifact_directory=artifact_directory,
    )

  def fake_write_manifest(
    regression_metadata,
    classification_metadata,
    manifest_path,
  ):
    content = {
      "protected_test_used":
        False,
      "active_registry_modified":
        False,
    }

    manifest_path.write_text(
      json.dumps(
        content
      ),
      encoding="utf-8",
    )

    return content

  monkeypatch.setattr(
    training,
    "load_selected_results",
    fake_load_selected_results,
  )

  monkeypatch.setattr(
    training,
    "load_frozen_candidate_splits",
    lambda candidate_manifest: (
      train_data,
      validation_data,
      protected_test_data,
      {},
    ),
  )

  monkeypatch.setattr(
    training,
    "train_regression_candidates",
    fake_train_regression_candidates,
  )

  monkeypatch.setattr(
    training,
    "train_classification_candidates",
    fake_train_classification_candidates,
  )

  monkeypatch.setattr(
    training,
    "write_manifest",
    fake_write_manifest,
  )

  (
    regression_metadata_path,
    classification_metadata_path,
    bundle_manifest_path,
    updated_manifest,
  ) = training.train_live_lifecycle_candidate(
    candidate_manifest_path=(
      manifest_path
    ),
    regression_results_path=(
      tmp_path
      / "regression_results.csv"
    ),
    classification_results_path=(
      tmp_path
      / "classification_results.csv"
    ),
  )

  assert captured_training_markers == [
    {
      10.0,
      20.0,
    },
    {
      10.0,
      20.0,
    },
  ]

  assert 999.0 not in (
    captured_training_markers[
      0
    ]
  )

  assert captured_directories[
    "regression"
  ] == Path(
    manifest[
      "tasks"
    ][
      "regression"
    ][
      "artifact_directory"
    ]
  )

  assert captured_directories[
    "classification"
  ] == Path(
    manifest[
      "tasks"
    ][
      "classification"
    ][
      "artifact_directory"
    ]
  )

  assert regression_metadata_path.is_file()
  assert classification_metadata_path.is_file()
  assert bundle_manifest_path.is_file()

  assert updated_manifest[
    "status"
  ] == "trained"

  assert updated_manifest[
    "tasks"
  ][
    "regression"
  ][
    "status"
  ] == "completed"

  assert updated_manifest[
    "tasks"
  ][
    "classification"
  ][
    "status"
  ] == "completed"

  assert updated_manifest[
    "live_training"
  ][
    "training_rows"
  ] == 5

  assert updated_manifest[
    "live_training"
  ][
    "protected_test_used"
  ] is False

  assert updated_manifest[
    "live_training"
  ][
    "active_registry_modified"
  ] is False

  written_manifest = json.loads(
    manifest_path.read_text(
      encoding="utf-8"
    )
  )

  assert written_manifest[
    "status"
  ] == "trained"


def test_failed_training_does_not_mark_candidate_completed(
  tmp_path,
  monkeypatch,
):
  manifest_path, original_manifest = (
    build_candidate_manifest(
      tmp_path
    )
  )

  train_data = build_training_frame(
    start="2026-01-01T00:00:00Z",
    row_count=3,
    marker=10.0,
  )

  validation_data = build_training_frame(
    start="2026-01-02T00:00:00Z",
    row_count=2,
    marker=20.0,
  )

  regression_results, classification_results = (
    build_result_tables()
  )

  monkeypatch.setattr(
    training,
    "load_selected_results",
    lambda path, task_name, required_columns: (
      regression_results
      if task_name == "Regression"
      else classification_results
    ),
  )

  monkeypatch.setattr(
    training,
    "load_frozen_candidate_splits",
    lambda candidate_manifest: (
      train_data,
      validation_data,
      build_training_frame(
        start="2026-01-03T00:00:00Z",
        row_count=2,
        marker=999.0,
      ),
      {},
    ),
  )

  monkeypatch.setattr(
    training,
    "train_regression_candidates",
    lambda training_data, results, artifact_directory: (
      create_metadata_rows(
        task_name="regression",
        artifact_directory=artifact_directory,
      )
    ),
  )

  def fail_classification_training(
    training_data,
    results,
    artifact_directory,
  ):
    raise RuntimeError(
      "classification training failed"
    )

  monkeypatch.setattr(
    training,
    "train_classification_candidates",
    fail_classification_training,
  )

  with pytest.raises(
    RuntimeError,
    match="classification training failed",
  ):
    training.train_live_lifecycle_candidate(
      candidate_manifest_path=(
        manifest_path
      ),
    )

  written_manifest = json.loads(
    manifest_path.read_text(
      encoding="utf-8"
    )
  )

  assert written_manifest == (
    original_manifest
  )

  assert written_manifest[
    "status"
  ] == "prepared"

  assert written_manifest[
    "tasks"
  ][
    "regression"
  ][
    "status"
  ] == "pending"

  assert written_manifest[
    "tasks"
  ][
    "classification"
  ][
    "status"
  ] == "pending"


def test_completed_training_is_not_repeated(
  tmp_path,
  monkeypatch,
):
  manifest_path, manifest = (
    build_candidate_manifest(
      tmp_path
    )
  )

  regression_metadata_path = Path(
    manifest[
      "tasks"
    ][
      "regression"
    ][
      "metadata_path"
    ]
  )

  classification_metadata_path = Path(
    manifest[
      "tasks"
    ][
      "classification"
    ][
      "metadata_path"
    ]
  )

  bundle_manifest_path = (
    Path(
      manifest[
        "candidate_directory"
      ]
    )
    / "live_bundle_manifest.json"
  )

  for path in (
    regression_metadata_path,
    classification_metadata_path,
    bundle_manifest_path,
  ):
    path.parent.mkdir(
      parents=True,
      exist_ok=True,
    )

    path.write_text(
      "complete\n",
      encoding="utf-8",
    )

  manifest[
    "status"
  ] = "trained"

  manifest[
    "tasks"
  ][
    "regression"
  ][
    "status"
  ] = "completed"

  manifest[
    "tasks"
  ][
    "classification"
  ][
    "status"
  ] = "completed"

  manifest[
    "live_training"
  ] = {
    "bundle_manifest_path":
      str(
        bundle_manifest_path
      ),
  }

  write_json_file(
    content=manifest,
    file_path=manifest_path,
  )

  def unexpected_call(*args, **kwargs):
    raise AssertionError(
      "completed training must not run again"
    )

  monkeypatch.setattr(
    training,
    "load_frozen_candidate_splits",
    unexpected_call,
  )

  monkeypatch.setattr(
    training,
    "train_regression_candidates",
    unexpected_call,
  )

  monkeypatch.setattr(
    training,
    "train_classification_candidates",
    unexpected_call,
  )

  outputs = (
    training.train_live_lifecycle_candidate(
      candidate_manifest_path=(
        manifest_path
      )
    )
  )

  assert outputs[
    0
  ] == regression_metadata_path

  assert outputs[
    1
  ] == classification_metadata_path

  assert outputs[
    2
  ] == bundle_manifest_path

  assert outputs[
    3
  ][
    "status"
  ] == "trained"
