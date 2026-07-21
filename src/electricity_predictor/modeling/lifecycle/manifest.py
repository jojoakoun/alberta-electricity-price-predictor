from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.lifecycle.paths import (
  LATEST_SPLIT_MANIFEST_PATH as LATEST_MANIFEST_PATH,
  MANIFEST_DIRECTORY,
)
from electricity_predictor.modeling.lifecycle.split_plan import (
  LifecycleSplitPlan,
  build_lifecycle_split_plan_from_config,
)
from electricity_predictor.modeling.split import (
  DATETIME_COLUMN,
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data,
)


def calculate_dataset_sha256(
  dataset_path: Path,
) -> str:
  """Calculate a stable identifier from dataset contents."""
  if not dataset_path.exists():
    raise FileNotFoundError(
      f"Dataset not found: {dataset_path}"
    )

  digest = sha256()

  with dataset_path.open("rb") as dataset_file:
    for chunk in iter(
      lambda: dataset_file.read(1024 * 1024),
      b"",
    ):
      digest.update(chunk)

  return digest.hexdigest()


def build_lifecycle_splits(
  data: pd.DataFrame,
  plan: LifecycleSplitPlan,
) -> tuple[
  pd.DataFrame,
  pd.DataFrame,
  pd.DataFrame,
]:
  """Apply a lifecycle plan using the shared split logic."""
  return split_time_series_data(
    data=data,
    train_start_utc=str(
      plan.train_start_utc
    ),
    validation_start_utc=str(
      plan.validation_start_utc
    ),
    test_start_utc=str(
      plan.test_start_utc
    ),
    test_end_utc=str(
      plan.test_end_utc
    ),
    purge_hours=plan.purge_hours,
  )


def summarize_split(
  split_data: pd.DataFrame,
) -> dict:
  """Summarize one materialized chronological split."""
  if split_data.empty:
    raise ValueError(
      "Lifecycle splits must not be empty."
    )

  return {
    "row_count": int(len(split_data)),
    "start_utc": (
      split_data[DATETIME_COLUMN]
      .min()
      .isoformat()
    ),
    "end_utc": (
      split_data[DATETIME_COLUMN]
      .max()
      .isoformat()
    ),
  }


def build_split_version(
  plan: LifecycleSplitPlan,
  dataset_sha256: str,
) -> str:
  """Build a deterministic split version identifier."""
  test_end = plan.test_end_utc.strftime(
    "%Y%m%dT%H%M%S"
  )

  return (
    f"expanding-{test_end}-"
    f"{dataset_sha256[:12]}"
  )


def build_lifecycle_manifest(
  data: pd.DataFrame,
  dataset_path: Path,
  dataset_sha256: str,
  plan: LifecycleSplitPlan,
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  test_data: pd.DataFrame,
  generated_at_utc: str | None = None,
) -> dict:
  """Build traceable metadata for one lifecycle split."""
  generated_at = (
    generated_at_utc
    or datetime.now(UTC).isoformat()
  )

  return {
    "schema_version": 1,
    "split_version": build_split_version(
      plan=plan,
      dataset_sha256=dataset_sha256,
    ),
    "strategy": "expanding",
    "generated_at_utc": generated_at,
    "dataset": {
      "path": str(dataset_path),
      "sha256": dataset_sha256,
      "version": (
        f"sha256-{dataset_sha256[:12]}"
      ),
      "row_count": int(len(data)),
      "start_utc": (
        data[DATETIME_COLUMN]
        .min()
        .isoformat()
      ),
      "end_utc": (
        data[DATETIME_COLUMN]
        .max()
        .isoformat()
      ),
    },
    "plan": plan.to_dict(),
    "splits": {
      "train": summarize_split(
        train_data
      ),
      "validation": summarize_split(
        validation_data
      ),
      "test": summarize_split(
        test_data
      ),
    },
  }


def write_lifecycle_manifest(
  manifest: dict,
  manifest_directory: Path = MANIFEST_DIRECTORY,
  latest_manifest_path: Path = LATEST_MANIFEST_PATH,
) -> tuple[Path, Path]:
  """Write versioned and latest lifecycle manifests."""
  manifest_directory.mkdir(
    parents=True,
    exist_ok=True,
  )
  latest_manifest_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  versioned_path = (
    manifest_directory
    / f"{manifest['split_version']}.json"
  )

  serialized_manifest = json.dumps(
    manifest,
    indent=2,
    sort_keys=True,
  )

  versioned_path.write_text(
    serialized_manifest + "\n",
    encoding="utf-8",
  )

  latest_manifest_path.write_text(
    serialized_manifest + "\n",
    encoding="utf-8",
  )

  return (
    versioned_path,
    latest_manifest_path,
  )


def materialize_lifecycle_manifest(
  dataset_path: Path = TRAINING_DATASET_PATH,
) -> tuple[Path, Path, dict]:
  """Create a lifecycle split manifest from current data."""
  configuration = load_configuration()

  data = load_training_dataset(
    dataset_path
  )

  latest_timestamp = data[
    DATETIME_COLUMN
  ].max()

  plan = (
    build_lifecycle_split_plan_from_config(
      latest_timestamp_utc=latest_timestamp,
      modeling_config=configuration[
        "modeling"
      ],
      lifecycle_config=configuration[
        "model_lifecycle"
      ],
    )
  )

  (
    train_data,
    validation_data,
    test_data,
  ) = build_lifecycle_splits(
    data=data,
    plan=plan,
  )

  dataset_sha256 = (
    calculate_dataset_sha256(
      dataset_path
    )
  )

  manifest = build_lifecycle_manifest(
    data=data,
    dataset_path=dataset_path,
    dataset_sha256=dataset_sha256,
    plan=plan,
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
  )

  (
    versioned_path,
    latest_path,
  ) = write_lifecycle_manifest(
    manifest=manifest
  )

  return (
    versioned_path,
    latest_path,
    manifest,
  )


def print_manifest_summary(
  manifest: dict,
) -> None:
  """Print a compact lifecycle split summary."""
  print("Model lifecycle split")
  print("=====================")
  print(
    f"Split version: "
    f"{manifest['split_version']}"
  )
  print(
    f"Dataset version: "
    f"{manifest['dataset']['version']}"
  )

  for split_name in [
    "train",
    "validation",
    "test",
  ]:
    split = manifest["splits"][
      split_name
    ]

    print(
      f"{split_name}: "
      f"{split['row_count']:,} rows | "
      f"{split['start_utc']} → "
      f"{split['end_utc']}"
    )


def main() -> None:
  """Materialize the current lifecycle split manifest."""
  (
    versioned_path,
    latest_path,
    manifest,
  ) = materialize_lifecycle_manifest()

  print_manifest_summary(manifest)

  print("")
  print(
    f"Versioned manifest: "
    f"{versioned_path}"
  )
  print(
    f"Latest manifest: "
    f"{latest_path}"
  )


if __name__ == "__main__":
  main()
