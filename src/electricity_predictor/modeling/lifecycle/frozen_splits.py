"""Resolve and reproduce the frozen data splits for lifecycle candidates."""

from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.lifecycle.candidate import (
  build_candidate_model_version,
  read_json_file,
)
from electricity_predictor.modeling.lifecycle.manifest import (
  build_lifecycle_splits,
  calculate_dataset_sha256,
)
from electricity_predictor.modeling.lifecycle.paths import (
  CANDIDATE_ROOT,
  LATEST_SPLIT_MANIFEST_PATH,
)
from electricity_predictor.modeling.lifecycle.split_plan import (
  LifecycleSplitPlan,
)
from electricity_predictor.modeling.split import (
  DATETIME_COLUMN,
  load_training_dataset,
)


def resolve_latest_candidate_manifest_path(
  latest_split_manifest_path: Path = (
    LATEST_SPLIT_MANIFEST_PATH
  ),
  candidate_root: Path = CANDIDATE_ROOT,
) -> Path:
  """Resolve the prepared candidate for the latest split."""
  split_manifest = read_json_file(
    latest_split_manifest_path
  )

  model_version = build_candidate_model_version(
    split_manifest["split_version"]
  )

  return (
    candidate_root
    / model_version
    / "candidate_manifest.json"
  )


def build_plan_from_split_manifest(
  split_manifest: dict,
) -> LifecycleSplitPlan:
  """Restore a frozen split plan from its manifest."""
  plan = split_manifest["plan"]

  return LifecycleSplitPlan(
    train_start_utc=pd.Timestamp(
      plan["train_start_utc"]
    ),
    validation_start_utc=pd.Timestamp(
      plan["validation_start_utc"]
    ),
    test_start_utc=pd.Timestamp(
      plan["test_start_utc"]
    ),
    test_end_utc=pd.Timestamp(
      plan["test_end_utc"]
    ),
    purge_hours=int(
      plan["purge_hours"]
    ),
  )


def validate_materialized_split(
  split_name: str,
  split_data: pd.DataFrame,
  expected_summary: dict,
) -> None:
  """Verify that current data reproduces the frozen split."""
  actual_row_count = len(split_data)

  actual_start = split_data[
    DATETIME_COLUMN
  ].min()

  actual_end = split_data[
    DATETIME_COLUMN
  ].max()

  expected_row_count = int(
    expected_summary["row_count"]
  )

  expected_start = pd.Timestamp(
    expected_summary["start_utc"]
  )

  expected_end = pd.Timestamp(
    expected_summary["end_utc"]
  )

  if actual_row_count != expected_row_count:
    raise ValueError(
      f"{split_name} row count changed: "
      f"expected {expected_row_count}, "
      f"received {actual_row_count}."
    )

  if actual_start != expected_start:
    raise ValueError(
      f"{split_name} start changed: "
      f"expected {expected_start}, "
      f"received {actual_start}."
    )

  if actual_end != expected_end:
    raise ValueError(
      f"{split_name} end changed: "
      f"expected {expected_end}, "
      f"received {actual_end}."
    )


def load_frozen_candidate_splits(
  candidate_manifest: dict,
) -> tuple[
  pd.DataFrame,
  pd.DataFrame,
  pd.DataFrame,
  dict,
]:
  """Load and reproduce the dataset frozen for one candidate."""
  frozen_manifest_path = Path(
    candidate_manifest[
      "frozen_split_manifest_path"
    ]
  )

  split_manifest = read_json_file(
    frozen_manifest_path
  )

  dataset_path = Path(
    split_manifest["dataset"]["path"]
  )

  expected_hash = split_manifest[
    "dataset"
  ]["sha256"]

  actual_hash = calculate_dataset_sha256(
    dataset_path
  )

  if actual_hash != expected_hash:
    raise ValueError(
      "The training dataset hash no longer matches "
      "the candidate split manifest. Prepare a new "
      "split and candidate before training."
    )

  data = load_training_dataset(
    dataset_path
  )

  plan = build_plan_from_split_manifest(
    split_manifest
  )

  (
    train_data,
    validation_data,
    test_data,
  ) = build_lifecycle_splits(
    data=data,
    plan=plan,
  )

  for split_name, split_data in [
    ("train", train_data),
    ("validation", validation_data),
    ("test", test_data),
  ]:
    validate_materialized_split(
      split_name=split_name,
      split_data=split_data,
      expected_summary=(
        split_manifest[
          "splits"
        ][split_name]
      ),
    )

  return (
    train_data,
    validation_data,
    test_data,
    split_manifest,
  )
