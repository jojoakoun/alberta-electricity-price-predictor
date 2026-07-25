from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.lifecycle.manifest import (
  build_lifecycle_manifest,
  build_lifecycle_splits,
  build_split_version,
  calculate_dataset_sha256,
  write_lifecycle_manifest,
)
from electricity_predictor.modeling.lifecycle.split_plan import (
  build_expanding_split_plan,
)


def build_hourly_dataset() -> pd.DataFrame:
  timestamps = pd.date_range(
    start="2025-01-01 00:00:00",
    end="2026-03-01 00:00:00",
    freq="h",
  )

  return pd.DataFrame(
    {
      "datetime_universal_time":
        timestamps,
      "actual_price": range(
        len(timestamps)
      ),
    }
  )


def build_test_plan():
  return build_expanding_split_plan(
    latest_timestamp_utc=(
      "2026-03-01 00:00:00"
    ),
    train_start_utc=(
      "2025-01-01 00:00:00"
    ),
    validation_days=30,
    test_days=15,
    purge_hours=24,
    minimum_training_days=30,
  )


def test_calculate_dataset_sha256_is_stable(
  tmp_path: Path,
):
  dataset_path = (
    tmp_path / "dataset.csv"
  )
  dataset_path.write_text(
    "timestamp,value\n"
    "2026-01-01,10\n",
    encoding="utf-8",
  )

  first_hash = calculate_dataset_sha256(
    dataset_path
  )
  second_hash = calculate_dataset_sha256(
    dataset_path
  )

  assert first_hash == second_hash
  assert len(first_hash) == 64


def test_build_lifecycle_splits_applies_purges():
  data = build_hourly_dataset()
  plan = build_test_plan()

  (
    train_data,
    validation_data,
    test_data,
  ) = build_lifecycle_splits(
    data=data,
    plan=plan,
  )

  assert (
    train_data[
      "datetime_universal_time"
    ].max()
    < plan.validation_start_utc
  )

  assert (
    validation_data[
      "datetime_universal_time"
    ].max()
    < plan.test_start_utc
  )

  assert (
    test_data[
      "datetime_universal_time"
    ].max()
    == plan.test_end_utc
  )


def test_build_split_version_is_deterministic():
  plan = build_test_plan()

  first_version = build_split_version(
    plan=plan,
    dataset_sha256="a" * 64,
  )

  second_version = build_split_version(
    plan=plan,
    dataset_sha256="a" * 64,
  )

  assert first_version == second_version
  assert first_version.endswith(
    "aaaaaaaaaaaa"
  )


def test_build_and_write_manifest(
  tmp_path: Path,
):
  data = build_hourly_dataset()
  plan = build_test_plan()

  (
    train_data,
    validation_data,
    test_data,
  ) = build_lifecycle_splits(
    data=data,
    plan=plan,
  )

  manifest = build_lifecycle_manifest(
    data=data,
    dataset_path=Path(
      "training_dataset.csv"
    ),
    dataset_sha256="b" * 64,
    plan=plan,
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    generated_at_utc=(
      "2026-03-01T01:00:00+00:00"
    ),
  )

  (
    versioned_path,
    latest_path,
  ) = write_lifecycle_manifest(
    manifest=manifest,
    manifest_directory=(
      tmp_path / "manifests"
    ),
    latest_manifest_path=(
      tmp_path / "latest.json"
    ),
  )

  assert versioned_path.exists()
  assert latest_path.exists()
  assert (
    manifest["splits"]["test"][
      "row_count"
    ]
    == 15 * 24
  )
  assert (
    manifest["dataset"]["version"]
    == "sha256-bbbbbbbbbbbb"
  )
