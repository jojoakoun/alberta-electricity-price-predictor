"""Manage independent active regression and classification model lineages."""

from datetime import UTC, datetime
import json
import os
from pathlib import Path
from uuid import uuid4


ACTIVE_MODEL_REGISTRY_PATH = Path(
  "models/production/active_models.json"
)

LEGACY_REGRESSION_METADATA_PATH = Path(
  "models/regression/"
  "selected_regression_model_metadata.csv"
)

LEGACY_CLASSIFICATION_METADATA_PATH = Path(
  "models/classification/"
  "selected_classification_model_metadata.csv"
)

TASK_NAMES = (
  "regression",
  "classification",
)


def current_utc_timestamp() -> str:
  """Return one ISO-formatted UTC timestamp."""
  return datetime.now(
    UTC
  ).isoformat()


def build_legacy_registry(
  updated_at_utc: str | None = None,
) -> dict:
  """Build the initial registry without merging the two task lineages."""
  return {
    "schema_version": 1,
    "updated_at_utc": (
      updated_at_utc
      or current_utc_timestamp()
    ),
    "tasks": {
      "regression": {
        "model_version": (
          "legacy-unversioned"
        ),
        "metadata_path": str(
          LEGACY_REGRESSION_METADATA_PATH
        ),
        "source": "legacy",
      },
      "classification": {
        "model_version": (
          "legacy-unversioned"
        ),
        "metadata_path": str(
          LEGACY_CLASSIFICATION_METADATA_PATH
        ),
        "source": "legacy",
      },
    },
  }


def validate_active_registry(
  registry: dict,
  require_metadata_files: bool = True,
) -> None:
  """Validate the active model registry."""
  if not isinstance(registry, dict):
    raise ValueError(
      "Active model registry must be a JSON object."
    )

  required_top_level = {
    "schema_version",
    "updated_at_utc",
    "tasks",
  }

  missing_top_level = (
    required_top_level
    - set(registry)
  )

  if missing_top_level:
    raise ValueError(
      "Active model registry is missing fields: "
      f"{sorted(missing_top_level)}"
    )

  if registry["schema_version"] != 1:
    raise ValueError(
      "Unsupported active model registry schema."
    )

  tasks = registry["tasks"]

  if not isinstance(tasks, dict):
    raise ValueError(
      "Active model registry tasks must be an object."
    )

  for task_name in TASK_NAMES:
    if task_name not in tasks:
      raise ValueError(
        "Active model registry is missing task: "
        f"{task_name}"
      )

    task = tasks[task_name]

    required_task_fields = {
      "model_version",
      "metadata_path",
      "source",
    }

    missing_task_fields = (
      required_task_fields
      - set(task)
    )

    if missing_task_fields:
      raise ValueError(
        f"Registry task {task_name} is missing fields: "
        f"{sorted(missing_task_fields)}"
      )

    if not str(
      task["model_version"]
    ).strip():
      raise ValueError(
        f"Registry task {task_name} has no model version."
      )

    metadata_path = Path(
      str(
        task["metadata_path"]
      )
    )

    if (
      require_metadata_files
      and not metadata_path.exists()
    ):
      raise FileNotFoundError(
        f"Active {task_name} metadata not found: "
        f"{metadata_path}"
      )


def read_active_registry(
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
  require_metadata_files: bool = True,
) -> dict:
  """Read and validate the active model registry."""
  if not registry_path.exists():
    raise FileNotFoundError(
      "Active model registry not found: "
      f"{registry_path}"
    )

  registry = json.loads(
    registry_path.read_text(
      encoding="utf-8"
    )
  )

  validate_active_registry(
    registry=registry,
    require_metadata_files=(
      require_metadata_files
    ),
  )

  return registry


def write_active_registry_atomic(
  registry: dict,
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
  require_metadata_files: bool = True,
) -> Path:
  """Write the registry through an atomic file replacement."""
  validate_active_registry(
    registry=registry,
    require_metadata_files=(
      require_metadata_files
    ),
  )

  registry_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  temporary_path = (
    registry_path.parent
    / (
      f".{registry_path.name}."
      f"{uuid4().hex}.tmp"
    )
  )

  serialized = json.dumps(
    registry,
    indent=2,
    sort_keys=True,
  ) + "\n"

  try:
    temporary_path.write_text(
      serialized,
      encoding="utf-8",
    )

    # Readers must see either the previous complete registry or the new one,
    # never a partially written activation file.
    os.replace(
      temporary_path,
      registry_path,
    )
  finally:
    if temporary_path.exists():
      temporary_path.unlink()

  return registry_path


def initialize_active_registry(
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
) -> tuple[Path, dict]:
  """Create the legacy registry without overwriting one already present."""
  if registry_path.exists():
    registry = read_active_registry(
      registry_path=registry_path
    )

    return (
      registry_path,
      registry,
    )

  registry = build_legacy_registry()

  written_path = (
    write_active_registry_atomic(
      registry=registry,
      registry_path=registry_path,
    )
  )

  return (
    written_path,
    registry,
  )


def _resolve_task_metadata_path(
  registry: dict,
  task_name: str,
) -> Path:
  """Return the normalized metadata path exposed by one registry task."""
  return Path(
    str(registry["tasks"][task_name]["metadata_path"])
  )


def resolve_active_metadata_paths(
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
) -> tuple[Path, Path, dict]:
  """Resolve each active task's metadata without conflating its lineage."""
  registry = read_active_registry(
    registry_path=registry_path
  )

  regression_path = _resolve_task_metadata_path(
    registry=registry,
    task_name="regression",
  )
  classification_path = _resolve_task_metadata_path(
    registry=registry,
    task_name="classification",
  )

  return (
    regression_path,
    classification_path,
    registry,
  )
