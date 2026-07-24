"""Validate and manually activate model tasks that passed lifecycle gates."""

import argparse
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.modeling.lifecycle.candidate_run import (
  read_json_file,
  write_json_file,
)
from electricity_predictor.modeling.lifecycle.frozen_splits import (
  resolve_latest_candidate_manifest_path,
)
from electricity_predictor.serving.model_registry import (
  ACTIVE_MODEL_REGISTRY_PATH,
  TASK_NAMES,
  current_utc_timestamp,
  initialize_active_registry,
  read_active_registry,
  validate_active_registry,
  write_active_registry_atomic,
)


ACTIVE_MODEL_HISTORY_DIRECTORY = Path(
  "models/production/history"
)


def validate_metadata_bundle(
  task_name: str,
  metadata_path: Path,
) -> None:
  """Validate one complete deployable metadata bundle."""
  if not metadata_path.exists():
    raise FileNotFoundError(
      f"Candidate {task_name} metadata not found: "
      f"{metadata_path}"
    )

  metadata = pd.read_csv(
    metadata_path
  )

  required_columns = {
    "model_name",
    "horizon_hours",
    "artifact_path",
    "feature_columns",
  }

  if task_name == "classification":
    required_columns.update(
      {
        "spike_threshold",
        "decision_threshold",
      }
    )

  missing_columns = (
    required_columns
    - set(metadata.columns)
  )

  if missing_columns:
    raise ValueError(
      f"Candidate {task_name} metadata is missing: "
      f"{sorted(missing_columns)}"
    )

  if metadata.empty:
    raise ValueError(
      f"Candidate {task_name} metadata is empty."
    )

  horizons = set(
    metadata[
      "horizon_hours"
    ].astype(int)
  )

  if horizons != set(
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    raise ValueError(
      f"Candidate {task_name} horizons must be "
      f"{list(SUPPORTED_FORECAST_HORIZONS_HOURS)}, received "
      f"{sorted(horizons)}."
    )

  if metadata[
    "horizon_hours"
  ].astype(int).duplicated().any():
    raise ValueError(
      f"Candidate {task_name} contains duplicate horizons."
    )

  for artifact_path_text in metadata[
    "artifact_path"
  ]:
    artifact_path = Path(
      str(
        artifact_path_text
      )
    )

    if not artifact_path.exists():
      raise FileNotFoundError(
        f"Candidate artifact not found: "
        f"{artifact_path}"
      )


def validate_task_promotion_gate(
  candidate_manifest: dict,
  task_name: str,
) -> None:
  """Require one completed task and successful comparison gate."""
  if task_name not in TASK_NAMES:
    raise ValueError(
      f"Unsupported promotion task: {task_name}"
    )

  task = candidate_manifest[
    "tasks"
  ][task_name]

  if task.get(
    "status"
  ) != "completed":
    raise ValueError(
      f"Candidate task {task_name} is not completed."
    )

  comparison = candidate_manifest.get(
    "comparison"
  )

  if not comparison:
    raise ValueError(
      "Candidate has no champion comparison."
    )

  gate_name = (
    "regression_gate_pass"
    if task_name == "regression"
    else "classification_gate_pass"
  )

  if not comparison.get(
    gate_name,
    False,
  ):
    raise ValueError(
      f"Candidate {task_name} promotion gate did not pass."
    )

  validate_metadata_bundle(
    task_name=task_name,
    metadata_path=Path(
      task[
        "metadata_path"
      ]
    ),
  )


def archive_active_registry(
  registry: dict,
  history_directory: Path = (
    ACTIVE_MODEL_HISTORY_DIRECTORY
  ),
) -> Path:
  """Archive the current registry before changing it."""
  history_directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  timestamp = datetime.now(
    UTC
  ).strftime(
    "%Y%m%dT%H%M%S%fZ"
  )

  history_path = (
    history_directory
    / f"{timestamp}-active_models.json"
  )

  write_active_registry_atomic(
    registry=registry,
    registry_path=history_path,
  )

  return history_path


def promote_candidate_tasks(
  candidate_manifest_path: Path,
  task_names: list[str],
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
  history_directory: Path = (
    ACTIVE_MODEL_HISTORY_DIRECTORY
  ),
) -> tuple[Path, Path, dict]:
  """Promote selected candidate tasks through the active registry."""
  if not task_names:
    raise ValueError(
      "At least one promotion task is required."
    )

  unique_task_names = list(
    dict.fromkeys(
      task_names
    )
  )

  candidate_manifest = read_json_file(
    candidate_manifest_path
  )

  if candidate_manifest.get(
    "status"
  ) != "evaluated":
    raise ValueError(
      "Candidate must be evaluated before promotion."
    )

  for task_name in unique_task_names:
    validate_task_promotion_gate(
      candidate_manifest=(
        candidate_manifest
      ),
      task_name=task_name,
    )

  initialize_active_registry(
    registry_path=registry_path
  )

  current_registry = read_active_registry(
    registry_path=registry_path
  )

  history_path = archive_active_registry(
    registry=current_registry,
    history_directory=history_directory,
  )

  updated_registry = deepcopy(
    current_registry
  )

  promoted_at = (
    current_utc_timestamp()
  )

  for task_name in unique_task_names:
    task = candidate_manifest[
      "tasks"
    ][task_name]

    updated_registry[
      "tasks"
    ][task_name] = {
      "model_version": (
        candidate_manifest[
          "model_version"
        ]
      ),
      "metadata_path": str(
        task[
          "metadata_path"
        ]
      ),
      "source": "candidate",
      "candidate_manifest_path": str(
        candidate_manifest_path
      ),
      "promoted_at_utc": promoted_at,
    }

  updated_registry[
    "updated_at_utc"
  ] = promoted_at

  written_registry_path = (
    write_active_registry_atomic(
      registry=updated_registry,
      registry_path=registry_path,
    )
  )

  promotion = candidate_manifest.setdefault(
    "promotion",
    {}
  )

  promoted_tasks = set(
    promotion.get(
      "promoted_tasks",
      [],
    )
  )

  promoted_tasks.update(
    unique_task_names
  )

  promotion.update(
    {
      "mode": "manual",
      "promoted_at_utc": promoted_at,
      "promoted_tasks": sorted(
        promoted_tasks
      ),
      "active_registry_path": str(
        written_registry_path
      ),
      "previous_registry_snapshot": str(
        history_path
      ),
    }
  )

  write_json_file(
    content=candidate_manifest,
    file_path=candidate_manifest_path,
  )

  return (
    written_registry_path,
    history_path,
    updated_registry,
  )


def rollback_active_registry(
  snapshot_path: Path,
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
  history_directory: Path = (
    ACTIVE_MODEL_HISTORY_DIRECTORY
  ),
) -> tuple[Path, Path, dict]:
  """Restore one archived active registry."""
  snapshot = read_json_file(
    snapshot_path
  )

  validate_active_registry(
    snapshot,
    require_metadata_files=True,
  )

  current_registry = read_active_registry(
    registry_path=registry_path
  )

  current_snapshot_path = (
    archive_active_registry(
      registry=current_registry,
      history_directory=(
        history_directory
      ),
    )
  )

  restored_registry = deepcopy(
    snapshot
  )

  restored_registry[
    "updated_at_utc"
  ] = current_utc_timestamp()

  restored_registry[
    "restored_from_snapshot"
  ] = str(
    snapshot_path
  )

  written_path = (
    write_active_registry_atomic(
      registry=restored_registry,
      registry_path=registry_path,
    )
  )

  return (
    written_path,
    current_snapshot_path,
    restored_registry,
  )


def print_registry_summary(
  registry: dict,
) -> None:
  """Print active task versions and metadata paths."""
  print("Active model registry")
  print("=====================")

  for task_name in TASK_NAMES:
    task = registry[
      "tasks"
    ][task_name]

    print("")
    print(task_name)
    print("-" * len(task_name))

    print(
      "Model version: "
      f"{task['model_version']}"
    )

    print(
      "Metadata: "
      f"{task['metadata_path']}"
    )

    print(
      "Source: "
      f"{task['source']}"
    )


def main() -> None:
  """Initialize, promote, or roll back active models."""
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "--initialize",
    action="store_true",
  )

  parser.add_argument(
    "--task",
    action="append",
    choices=list(
      TASK_NAMES
    ),
  )

  parser.add_argument(
    "--rollback",
    type=Path,
  )

  arguments = parser.parse_args()

  selected_actions = sum(
    [
      bool(arguments.initialize),
      bool(arguments.task),
      arguments.rollback is not None,
    ]
  )

  if selected_actions != 1:
    parser.error(
      "Choose exactly one action: "
      "--initialize, --task, or --rollback."
    )

  if arguments.initialize:
    registry_path, registry = (
      initialize_active_registry()
    )

    print_registry_summary(
      registry
    )

    print("")
    print(
      f"Registry: {registry_path}"
    )

    return

  if arguments.rollback is not None:
    (
      registry_path,
      rollback_snapshot,
      registry,
    ) = rollback_active_registry(
      snapshot_path=(
        arguments.rollback
      )
    )

    print_registry_summary(
      registry
    )

    print("")
    print(
      f"Registry: {registry_path}"
    )

    print(
      "Pre-rollback snapshot: "
      f"{rollback_snapshot}"
    )

    return

  candidate_manifest_path = (
    resolve_latest_candidate_manifest_path()
  )

  (
    registry_path,
    history_path,
    registry,
  ) = promote_candidate_tasks(
    candidate_manifest_path=(
      candidate_manifest_path
    ),
    task_names=arguments.task,
  )

  print_registry_summary(
    registry
  )

  print("")
  print(
    f"Registry: {registry_path}"
  )

  print(
    f"Rollback snapshot: {history_path}"
  )


if __name__ == "__main__":
  main()
