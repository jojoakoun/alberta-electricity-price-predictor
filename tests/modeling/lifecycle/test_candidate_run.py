import json
from pathlib import Path

import pytest

from electricity_predictor.modeling.lifecycle.candidate_run import (
  build_candidate_manifest,
  build_candidate_model_version,
  prepare_candidate_run,
)


def build_test_split_manifest() -> dict:
  return {
    "schema_version": 1,
    "split_version": (
      "expanding-20260719T130000-"
      "dd356b9313f2"
    ),
    "strategy": "expanding",
    "dataset": {
      "path": (
        "data/processed/"
        "training_dataset.csv"
      ),
      "sha256": "d" * 64,
      "version": (
        "sha256-dd356b9313f2"
      ),
      "row_count": 57223,
      "start_utc": (
        "2020-01-08T07:00:00"
      ),
      "end_utc": (
        "2026-07-19T13:00:00"
      ),
    },
    "plan": {
      "train_start_utc": (
        "2020-01-08T07:00:00"
      ),
      "validation_start_utc": (
        "2025-01-19T14:00:00"
      ),
      "test_start_utc": (
        "2026-01-20T14:00:00"
      ),
      "test_end_utc": (
        "2026-07-19T13:00:00"
      ),
      "purge_hours": 24,
    },
    "splits": {
      "train": {
        "row_count": 44095,
        "start_utc": (
          "2020-01-08T07:00:00"
        ),
        "end_utc": (
          "2025-01-18T13:00:00"
        ),
      },
      "validation": {
        "row_count": 8760,
        "start_utc": (
          "2025-01-19T14:00:00"
        ),
        "end_utc": (
          "2026-01-19T13:00:00"
        ),
      },
      "test": {
        "row_count": 4320,
        "start_utc": (
          "2026-01-20T14:00:00"
        ),
        "end_utc": (
          "2026-07-19T13:00:00"
        ),
      },
    },
  }


def write_split_manifest(
  file_path: Path,
) -> None:
  file_path.write_text(
    json.dumps(
      build_test_split_manifest()
    ),
    encoding="utf-8",
  )


def test_build_candidate_model_version():
  version = (
    build_candidate_model_version(
      "expanding-20260719T130000-"
      "dd356b9313f2"
    )
  )

  assert version == (
    "candidate-"
    "expanding-20260719T130000-"
    "dd356b9313f2"
  )


def test_build_candidate_manifest_is_pending():
  manifest = build_candidate_manifest(
    split_manifest=(
      build_test_split_manifest()
    ),
    source_split_manifest_path=Path(
      "latest.json"
    ),
    candidate_root=Path(
      "models/candidates"
    ),
    promotion_mode="manual",
    created_at_utc=(
      "2026-07-20T17:00:00+00:00"
    ),
  )

  assert manifest["status"] == "prepared"

  assert (
    manifest["tasks"]["regression"][
      "status"
    ]
    == "pending"
  )

  assert (
    manifest["tasks"]["classification"][
      "status"
    ]
    == "pending"
  )

  assert (
    manifest["current_champion"][
      "status"
    ]
    == "legacy_unversioned"
  )


def test_prepare_candidate_run_creates_isolated_directories(
  tmp_path: Path,
):
  split_manifest_path = (
    tmp_path / "latest.json"
  )

  write_split_manifest(
    split_manifest_path
  )

  (
    candidate_manifest_path,
    frozen_split_manifest_path,
    manifest,
  ) = prepare_candidate_run(
    split_manifest_path=(
      split_manifest_path
    ),
    candidate_root=(
      tmp_path / "candidates"
    ),
    promotion_mode="manual",
    created_at_utc=(
      "2026-07-20T17:00:00+00:00"
    ),
  )

  candidate_directory = Path(
    manifest["candidate_directory"]
  )

  assert candidate_manifest_path.exists()
  assert frozen_split_manifest_path.exists()

  assert (
    candidate_directory
    / "regression"
  ).is_dir()

  assert (
    candidate_directory
    / "classification"
  ).is_dir()

  assert (
    candidate_directory
    / "reports"
    / "regression"
  ).is_dir()

  assert (
    candidate_directory
    / "reports"
    / "classification"
  ).is_dir()


def test_prepare_candidate_run_is_idempotent(
  tmp_path: Path,
):
  split_manifest_path = (
    tmp_path / "latest.json"
  )

  write_split_manifest(
    split_manifest_path
  )

  first_result = prepare_candidate_run(
    split_manifest_path=(
      split_manifest_path
    ),
    candidate_root=(
      tmp_path / "candidates"
    ),
    promotion_mode="manual",
    created_at_utc=(
      "2026-07-20T17:00:00+00:00"
    ),
  )

  second_result = prepare_candidate_run(
    split_manifest_path=(
      split_manifest_path
    ),
    candidate_root=(
      tmp_path / "candidates"
    ),
    promotion_mode="manual",
    created_at_utc=(
      "2026-07-21T17:00:00+00:00"
    ),
  )

  assert (
    first_result[2]["created_at_utc"]
    == second_result[2]["created_at_utc"]
  )


def test_build_candidate_manifest_rejects_incomplete_split():
  with pytest.raises(
    ValueError,
    match="missing required fields",
  ):
    build_candidate_manifest(
      split_manifest={
        "split_version": "incomplete",
      },
      source_split_manifest_path=Path(
        "latest.json"
      ),
      candidate_root=Path(
        "models/candidates"
      ),
      promotion_mode="manual",
    )
