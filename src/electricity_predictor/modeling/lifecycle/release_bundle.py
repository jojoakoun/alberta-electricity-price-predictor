from copy import deepcopy
from datetime import UTC, datetime
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tarfile
from uuid import uuid4

import pandas as pd

from electricity_predictor.serving.model_registry import (
  ACTIVE_MODEL_REGISTRY_PATH,
  read_active_registry,
)


RELEASE_BUILD_ROOT = Path(
  "dist/model-releases"
)

RELEASE_INSTALL_ROOT = Path(
  "models/production/releases"
)

TASK_NAMES = (
  "regression",
  "classification",
)


def calculate_file_sha256(
  file_path: Path,
) -> str:
  """Calculate the SHA-256 checksum of one file."""
  if not file_path.exists():
    raise FileNotFoundError(
      f"Release source file not found: {file_path}"
    )

  digest = sha256()

  with file_path.open("rb") as source_file:
    for chunk in iter(
      lambda: source_file.read(
        1024 * 1024
      ),
      b"",
    ):
      digest.update(chunk)

  return digest.hexdigest()


def load_release_metadata(
  task_name: str,
  metadata_path: Path,
) -> pd.DataFrame:
  """Load and validate active task metadata."""
  if not metadata_path.exists():
    raise FileNotFoundError(
      f"Active {task_name} metadata not found: "
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
      f"Active {task_name} metadata is missing: "
      f"{sorted(missing_columns)}"
    )

  if metadata.empty:
    raise ValueError(
      f"Active {task_name} metadata is empty."
    )

  if metadata[
    "horizon_hours"
  ].astype(int).duplicated().any():
    raise ValueError(
      f"Active {task_name} metadata contains "
      "duplicate horizons."
    )

  for artifact_text in metadata[
    "artifact_path"
  ]:
    artifact_path = Path(
      str(
        artifact_text
      )
    )

    if not artifact_path.exists():
      raise FileNotFoundError(
        f"Active artifact not found: "
        f"{artifact_path}"
      )

  return metadata.sort_values(
    "horizon_hours"
  ).reset_index(drop=True)


def build_release_identity(
  registry: dict,
  metadata_by_task: dict[
    str,
    pd.DataFrame,
  ],
) -> tuple[str, str]:
  """Build a deterministic release identifier."""
  digest = sha256()

  identity = {
    task_name: {
      "model_version": registry[
        "tasks"
      ][task_name][
        "model_version"
      ],
      "metadata_path": registry[
        "tasks"
      ][task_name][
        "metadata_path"
      ],
    }
    for task_name in TASK_NAMES
  }

  digest.update(
    json.dumps(
      identity,
      sort_keys=True,
    ).encode(
      "utf-8"
    )
  )

  for task_name in TASK_NAMES:
    metadata = metadata_by_task[
      task_name
    ]

    digest.update(
      metadata.to_csv(
        index=False
      ).encode(
        "utf-8"
      )
    )

    for artifact_text in metadata[
      "artifact_path"
    ]:
      artifact_path = Path(
        str(
          artifact_text
        )
      )

      digest.update(
        calculate_file_sha256(
          artifact_path
        ).encode(
          "utf-8"
        )
      )

  release_hash = digest.hexdigest()

  release_id = (
    f"release-{release_hash[:16]}"
  )

  return (
    release_id,
    release_hash,
  )


def copy_task_into_release(
  task_name: str,
  metadata: pd.DataFrame,
  payload_root: Path,
  release_id: str,
  install_root: Path,
) -> tuple[Path, pd.DataFrame]:
  """Copy one active task and rewrite its artifact paths."""
  payload_task_directory = (
    payload_root
    / install_root
    / release_id
    / task_name
  )

  payload_task_directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  installed_task_directory = (
    install_root
    / release_id
    / task_name
  )

  rewritten_metadata = (
    metadata.copy()
  )

  rewritten_artifact_paths = []

  for artifact_text in metadata[
    "artifact_path"
  ]:
    source_artifact = Path(
      str(
        artifact_text
      )
    )

    destination_artifact = (
      payload_task_directory
      / source_artifact.name
    )

    if destination_artifact.exists():
      raise ValueError(
        "Duplicate release artifact filename: "
        f"{source_artifact.name}"
      )

    shutil.copy2(
      source_artifact,
      destination_artifact,
    )

    rewritten_artifact_paths.append(
      str(
        installed_task_directory
        / source_artifact.name
      )
    )

  rewritten_metadata[
    "artifact_path"
  ] = rewritten_artifact_paths

  metadata_filename = (
    f"selected_{task_name}_"
    "model_metadata.csv"
  )

  payload_metadata_path = (
    payload_task_directory
    / metadata_filename
  )

  rewritten_metadata.to_csv(
    payload_metadata_path,
    index=False,
  )

  installed_metadata_path = (
    installed_task_directory
    / metadata_filename
  )

  return (
    installed_metadata_path,
    rewritten_metadata,
  )


def collect_payload_files(
  payload_root: Path,
) -> list[Path]:
  """List every regular file in deterministic order."""
  return sorted(
    file_path
    for file_path in payload_root.rglob(
      "*"
    )
    if file_path.is_file()
  )


def build_release_manifest(
  release_id: str,
  release_hash: str,
  registry: dict,
  payload_root: Path,
  generated_at_utc: str,
) -> dict:
  """Describe every file contained in a release."""
  files = []

  for file_path in collect_payload_files(
    payload_root
  ):
    relative_path = file_path.relative_to(
      payload_root
    )

    files.append(
      {
        "path": str(
          relative_path
        ),
        "bytes": file_path.stat().st_size,
        "sha256": calculate_file_sha256(
          file_path
        ),
      }
    )

  return {
    "schema_version": 1,
    "release_id": release_id,
    "release_hash": release_hash,
    "generated_at_utc": (
      generated_at_utc
    ),
    "tasks": {
      task_name: {
        "model_version": registry[
          "tasks"
        ][task_name][
          "model_version"
        ],
        "source": registry[
          "tasks"
        ][task_name][
          "source"
        ],
      }
      for task_name in TASK_NAMES
    },
    "file_count": len(files),
    "total_file_bytes": sum(
      file_record[
        "bytes"
      ]
      for file_record in files
    ),
    "files": files,
  }


def create_release_archive(
  payload_root: Path,
  archive_path: Path,
) -> Path:
  """Create a gzip archive containing repo-relative paths."""
  archive_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  temporary_archive = (
    archive_path.parent
    / (
      f".{archive_path.name}."
      f"{uuid4().hex}.tmp"
    )
  )

  try:
    with tarfile.open(
      temporary_archive,
      mode="w:gz",
    ) as archive:
      for payload_item in sorted(
        payload_root.iterdir()
      ):
        archive.add(
          payload_item,
          arcname=payload_item.name,
        )

    temporary_archive.replace(
      archive_path
    )
  finally:
    if temporary_archive.exists():
      temporary_archive.unlink()

  return archive_path


def build_production_release(
  registry_path: Path = (
    ACTIVE_MODEL_REGISTRY_PATH
  ),
  build_root: Path = (
    RELEASE_BUILD_ROOT
  ),
  install_root: Path = (
    RELEASE_INSTALL_ROOT
  ),
) -> dict:
  """Build an immutable release from active models only."""
  registry = read_active_registry(
    registry_path=registry_path
  )

  metadata_by_task = {
    task_name: load_release_metadata(
      task_name=task_name,
      metadata_path=Path(
        registry[
          "tasks"
        ][task_name][
          "metadata_path"
        ]
      ),
    )
    for task_name in TASK_NAMES
  }

  (
    release_id,
    release_hash,
  ) = build_release_identity(
    registry=registry,
    metadata_by_task=(
      metadata_by_task
    ),
  )

  release_directory = (
    build_root / release_id
  )

  payload_root = (
    release_directory
    / "payload"
  )

  archive_path = (
    build_root
    / f"{release_id}.tar.gz"
  )

  descriptor_path = (
    build_root
    / f"{release_id}.json"
  )

  if (
    release_directory.exists()
    and archive_path.exists()
    and descriptor_path.exists()
  ):
    descriptor = json.loads(
      descriptor_path.read_text(
        encoding="utf-8"
      )
    )

    return descriptor

  staging_directory = (
    build_root
    / (
      f".{release_id}."
      f"{uuid4().hex}.tmp"
    )
  )

  staging_payload_root = (
    staging_directory
    / "payload"
  )

  generated_at_utc = datetime.now(
    UTC
  ).isoformat()

  try:
    release_registry = deepcopy(
      registry
    )

    release_registry[
      "release_id"
    ] = release_id

    release_registry[
      "updated_at_utc"
    ] = generated_at_utc

    for task_name in TASK_NAMES:
      (
        installed_metadata_path,
        _,
      ) = copy_task_into_release(
        task_name=task_name,
        metadata=metadata_by_task[
          task_name
        ],
        payload_root=(
          staging_payload_root
        ),
        release_id=release_id,
        install_root=install_root,
      )

      release_registry[
        "tasks"
      ][task_name][
        "metadata_path"
      ] = str(
        installed_metadata_path
      )

      release_registry[
        "tasks"
      ][task_name][
        "release_id"
      ] = release_id

    payload_registry_path = (
      staging_payload_root
      / "models"
      / "production"
      / "active_models.json"
    )

    payload_registry_path.parent.mkdir(
      parents=True,
      exist_ok=True,
    )

    payload_registry_path.write_text(
      json.dumps(
        release_registry,
        indent=2,
        sort_keys=True,
      )
      + "\n",
      encoding="utf-8",
    )

    release_manifest_path = (
      staging_payload_root
      / install_root
      / release_id
      / "release_manifest.json"
    )

    release_manifest = (
      build_release_manifest(
        release_id=release_id,
        release_hash=release_hash,
        registry=registry,
        payload_root=(
          staging_payload_root
        ),
        generated_at_utc=(
          generated_at_utc
        ),
      )
    )

    release_manifest_path.write_text(
      json.dumps(
        release_manifest,
        indent=2,
        sort_keys=True,
      )
      + "\n",
      encoding="utf-8",
    )

    build_root.mkdir(
      parents=True,
      exist_ok=True,
    )

    if release_directory.exists():
      shutil.rmtree(
        release_directory
      )

    staging_directory.replace(
      release_directory
    )

    create_release_archive(
      payload_root=payload_root,
      archive_path=archive_path,
    )

    archive_sha256 = (
      calculate_file_sha256(
        archive_path
      )
    )

    descriptor = {
      "schema_version": 1,
      "release_id": release_id,
      "release_hash": release_hash,
      "generated_at_utc": (
        generated_at_utc
      ),
      "release_directory": str(
        release_directory
      ),
      "payload_directory": str(
        payload_root
      ),
      "archive_path": str(
        archive_path
      ),
      "archive_bytes": (
        archive_path.stat().st_size
      ),
      "archive_sha256": (
        archive_sha256
      ),
      "release_manifest_path": str(
        payload_root
        / install_root
        / release_id
        / "release_manifest.json"
      ),
    }

    descriptor_path.write_text(
      json.dumps(
        descriptor,
        indent=2,
        sort_keys=True,
      )
      + "\n",
      encoding="utf-8",
    )

    return descriptor
  finally:
    if staging_directory.exists():
      shutil.rmtree(
        staging_directory
      )


def main() -> None:
  """Build the production model release."""
  descriptor = (
    build_production_release()
  )

  print("Production model release")
  print("========================")

  for field_name in [
    "release_id",
    "archive_path",
    "archive_bytes",
    "archive_sha256",
    "release_manifest_path",
  ]:
    print(
      f"{field_name}: "
      f"{descriptor[field_name]}"
    )


if __name__ == "__main__":
  main()
