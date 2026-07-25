import json
from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.modeling.lifecycle.frozen_splits import (
  build_plan_from_split_manifest,
  load_frozen_candidate_splits,
  resolve_latest_candidate_manifest_path,
  validate_materialized_split,
)
from electricity_predictor.modeling.lifecycle.manifest import (
  calculate_dataset_sha256,
)
from electricity_predictor.modeling.split import (
  DATETIME_COLUMN,
)


def build_split_manifest(
  dataset_path: Path,
  dataset_hash: str,
) -> dict:
  return {
    "schema_version": 1,
    "split_version": "split-test",
    "strategy": "expanding",
    "dataset": {
      "path": str(dataset_path),
      "sha256": dataset_hash,
      "version": (
        f"sha256-{dataset_hash[:12]}"
      ),
      "row_count": 15,
      "start_utc": "2026-01-01T00:00:00",
      "end_utc": "2026-01-01T14:00:00",
    },
    "plan": {
      "train_start_utc": "2026-01-01T00:00:00",
      "validation_start_utc": "2026-01-01T05:00:00",
      "test_start_utc": "2026-01-01T10:00:00",
      "test_end_utc": "2026-01-01T14:00:00",
      "purge_hours": 1,
    },
    "splits": {
      "train": {
        "row_count": 4,
        "start_utc": "2026-01-01T00:00:00",
        "end_utc": "2026-01-01T03:00:00",
      },
      "validation": {
        "row_count": 4,
        "start_utc": "2026-01-01T05:00:00",
        "end_utc": "2026-01-01T08:00:00",
      },
      "test": {
        "row_count": 5,
        "start_utc": "2026-01-01T10:00:00",
        "end_utc": "2026-01-01T14:00:00",
      },
    },
  }


def prepare_frozen_split_fixture(
  tmp_path: Path,
) -> tuple[dict, dict, Path]:
  dataset_path = tmp_path / "training.csv"
  timestamps = pd.date_range(
    start="2026-01-01T00:00:00",
    periods=15,
    freq="h",
  )

  data = pd.DataFrame(
    {
      DATETIME_COLUMN: timestamps,
      "actual_price": range(15),
    }
  ).sample(
    frac=1,
    random_state=42,
  )

  data.to_csv(
    dataset_path,
    index=False,
  )

  dataset_hash = calculate_dataset_sha256(
    dataset_path
  )
  split_manifest = build_split_manifest(
    dataset_path=dataset_path,
    dataset_hash=dataset_hash,
  )
  split_manifest_path = (
    tmp_path / "split_manifest.json"
  )
  split_manifest_path.write_text(
    json.dumps(split_manifest),
    encoding="utf-8",
  )

  candidate_manifest = {
    "split_version": "different-candidate-version",
    "frozen_split_manifest_path": str(
      split_manifest_path
    ),
  }

  return (
    candidate_manifest,
    split_manifest,
    dataset_path,
  )


def test_resolve_latest_candidate_manifest_path_is_deterministic(
  tmp_path: Path,
) -> None:
  latest_split_manifest_path = (
    tmp_path / "latest_split.json"
  )
  latest_split_manifest_path.write_text(
    json.dumps(
      {
        "split_version": "split-test",
      }
    ),
    encoding="utf-8",
  )
  candidate_root = tmp_path / "candidates"
  expected_path = (
    candidate_root
    / "candidate-split-test"
    / "candidate_manifest.json"
  )

  first_path = resolve_latest_candidate_manifest_path(
    latest_split_manifest_path=(
      latest_split_manifest_path
    ),
    candidate_root=candidate_root,
  )
  second_path = resolve_latest_candidate_manifest_path(
    latest_split_manifest_path=(
      latest_split_manifest_path
    ),
    candidate_root=candidate_root,
  )

  assert first_path == expected_path
  assert second_path == expected_path
  assert not expected_path.exists()


def test_resolve_latest_candidate_manifest_path_preserves_missing_file_error(
  tmp_path: Path,
) -> None:
  missing_path = tmp_path / "missing.json"

  with pytest.raises(
    FileNotFoundError,
  ) as error:
    resolve_latest_candidate_manifest_path(
      latest_split_manifest_path=missing_path,
      candidate_root=tmp_path / "candidates",
    )

  assert str(error.value) == (
    f"JSON file not found: {missing_path}"
  )


def test_build_plan_from_split_manifest_preserves_all_fields() -> None:
  split_manifest = {
    "plan": {
      "train_start_utc": "2026-01-01T00:00:00+00:00",
      "validation_start_utc": "2026-02-01T00:00:00+00:00",
      "test_start_utc": "2026-02-08T00:00:00+00:00",
      "test_end_utc": "2026-02-14T23:00:00+00:00",
      "purge_hours": "24",
    }
  }

  plan = build_plan_from_split_manifest(
    split_manifest
  )

  assert plan.train_start_utc == pd.Timestamp(
    "2026-01-01T00:00:00+00:00"
  )
  assert plan.validation_start_utc == pd.Timestamp(
    "2026-02-01T00:00:00+00:00"
  )
  assert plan.test_start_utc == pd.Timestamp(
    "2026-02-08T00:00:00+00:00"
  )
  assert plan.test_end_utc == pd.Timestamp(
    "2026-02-14T23:00:00+00:00"
  )
  assert plan.purge_hours == 24


def build_materialized_split(
  timestamps: list[str],
) -> pd.DataFrame:
  return pd.DataFrame(
    {
      DATETIME_COLUMN: pd.to_datetime(
        timestamps
      )
    }
  )


def test_validate_materialized_split_accepts_matching_summary() -> None:
  split_data = build_materialized_split(
    [
      "2026-01-01T00:00:00",
      "2026-01-01T01:00:00",
      "2026-01-01T02:00:00",
    ]
  )

  validate_materialized_split(
    split_name="train",
    split_data=split_data,
    expected_summary={
      "row_count": 3,
      "start_utc": "2026-01-01T00:00:00",
      "end_utc": "2026-01-01T02:00:00",
    },
  )


@pytest.mark.parametrize(
  (
    "split_data",
    "expected_summary",
    "expected_message",
  ),
  [
    (
      build_materialized_split(
        [
          "2026-01-01T00:00:00",
          "2026-01-01T01:00:00",
        ]
      ),
      {
        "row_count": 3,
        "start_utc": "2026-01-01T00:00:00",
        "end_utc": "2026-01-01T02:00:00",
      },
      (
        "train row count changed: expected 3, "
        "received 2."
      ),
    ),
    (
      build_materialized_split(
        [
          "2026-01-01T01:00:00",
          "2026-01-01T02:00:00",
          "2026-01-01T03:00:00",
        ]
      ),
      {
        "row_count": 3,
        "start_utc": "2026-01-01T00:00:00",
        "end_utc": "2026-01-01T03:00:00",
      },
      (
        "train start changed: expected "
        "2026-01-01 00:00:00, received "
        "2026-01-01 01:00:00."
      ),
    ),
    (
      build_materialized_split(
        [
          "2026-01-01T00:00:00",
          "2026-01-01T01:00:00",
          "2026-01-01T02:00:00",
        ]
      ),
      {
        "row_count": 3,
        "start_utc": "2026-01-01T00:00:00",
        "end_utc": "2026-01-01T03:00:00",
      },
      (
        "train end changed: expected "
        "2026-01-01 03:00:00, received "
        "2026-01-01 02:00:00."
      ),
    ),
  ],
  ids=[
    "row-count",
    "start",
    "end",
  ],
)
def test_validate_materialized_split_preserves_exact_errors(
  split_data: pd.DataFrame,
  expected_summary: dict,
  expected_message: str,
) -> None:
  with pytest.raises(ValueError) as error:
    validate_materialized_split(
      split_name="train",
      split_data=split_data,
      expected_summary=expected_summary,
    )

  assert str(error.value) == expected_message


def test_validate_materialized_split_remains_summary_only() -> None:
  split_with_interior_gap = build_materialized_split(
    [
      "2026-01-01T00:00:00",
      "2026-01-01T01:00:00",
      "2026-01-01T03:00:00",
    ]
  )

  validate_materialized_split(
    split_name="train",
    split_data=split_with_interior_gap,
    expected_summary={
      "row_count": 3,
      "start_utc": "2026-01-01T00:00:00",
      "end_utc": "2026-01-01T03:00:00",
    },
  )


def test_load_frozen_candidate_splits_preserves_order_and_metadata(
  tmp_path: Path,
) -> None:
  (
    candidate_manifest,
    split_manifest,
    _,
  ) = prepare_frozen_split_fixture(
    tmp_path
  )

  (
    train_data,
    validation_data,
    test_data,
    loaded_manifest,
  ) = load_frozen_candidate_splits(
    candidate_manifest
  )

  assert train_data[DATETIME_COLUMN].tolist() == list(
    pd.date_range(
      start="2026-01-01T00:00:00",
      periods=4,
      freq="h",
    )
  )
  assert validation_data[DATETIME_COLUMN].tolist() == list(
    pd.date_range(
      start="2026-01-01T05:00:00",
      periods=4,
      freq="h",
    )
  )
  assert test_data[DATETIME_COLUMN].tolist() == list(
    pd.date_range(
      start="2026-01-01T10:00:00",
      periods=5,
      freq="h",
    )
  )
  assert loaded_manifest == split_manifest


def test_load_frozen_candidate_splits_preserves_hash_error(
  tmp_path: Path,
) -> None:
  (
    candidate_manifest,
    _,
    dataset_path,
  ) = prepare_frozen_split_fixture(
    tmp_path
  )
  dataset_path.write_text(
    dataset_path.read_text(
      encoding="utf-8"
    )
    + "\n",
    encoding="utf-8",
  )

  with pytest.raises(ValueError) as error:
    load_frozen_candidate_splits(
      candidate_manifest
    )

  assert str(error.value) == (
    "The training dataset hash no longer matches "
    "the candidate split manifest. Prepare a new "
    "split and candidate before training."
  )


def test_load_frozen_candidate_splits_preserves_missing_manifest_error(
  tmp_path: Path,
) -> None:
  missing_path = tmp_path / "missing-split.json"

  with pytest.raises(
    FileNotFoundError,
  ) as error:
    load_frozen_candidate_splits(
      {
        "frozen_split_manifest_path": str(
          missing_path
        )
      }
    )

  assert str(error.value) == (
    f"JSON file not found: {missing_path}"
  )
