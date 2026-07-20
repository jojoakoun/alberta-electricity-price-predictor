import csv
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tarfile
from urllib.request import urlopen
from uuid import uuid4


MODEL_RELEASE_URL_ENV = "MODEL_RELEASE_URL"
MODEL_RELEASE_SHA256_ENV = "MODEL_RELEASE_SHA256"

EXPECTED_HORIZONS = {
  1,
  3,
  6,
  12,
  24,
}


def calculate_file_sha256(
  file_path: Path,
) -> str:
  """Calculate the SHA-256 checksum of one file."""
  digest = sha256()

  with file_path.open("rb") as file_stream:
    for chunk in iter(
      lambda: file_stream.read(
        1024 * 1024
      ),
      b"",
    ):
      digest.update(chunk)

  return digest.hexdigest()


def normalize_expected_sha256(
  expected_sha256: str,
) -> str:
  """Validate and normalize an expected checksum."""
  normalized = str(
    expected_sha256
  ).strip().lower()

  if not re.fullmatch(
    r"[0-9a-f]{64}",
    normalized,
  ):
    raise ValueError(
      "MODEL_RELEASE_SHA256 must contain "
      "exactly 64 hexadecimal characters."
    )

  return normalized


def download_release_archive(
  release_url: str,
  destination_path: Path,
) -> Path:
  """Download one release archive."""
  if not str(
    release_url
  ).strip():
    raise ValueError(
      "MODEL_RELEASE_URL must not be empty."
    )

  destination_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  with urlopen(
    release_url,
    timeout=300,
  ) as response:
    with destination_path.open(
      "wb"
    ) as destination:
      shutil.copyfileobj(
        response,
        destination,
        length=1024 * 1024,
      )

  if (
    not destination_path.exists()
    or destination_path.stat().st_size == 0
  ):
    raise ValueError(
      "Downloaded model release is empty."
    )

  return destination_path


def validate_archive_members(
  archive: tarfile.TarFile,
) -> list[tarfile.TarInfo]:
  """Reject unsafe or unexpected archive entries."""
  members = archive.getmembers()

  if not members:
    raise ValueError(
      "Model release archive is empty."
    )

  member_names = set()

  for member in members:
    archive_path = PurePosixPath(
      member.name
    )

    if (
      archive_path.is_absolute()
      or ".." in archive_path.parts
    ):
      raise ValueError(
        "Model release contains an unsafe path: "
        f"{member.name}"
      )

    if (
      member.issym()
      or member.islnk()
    ):
      raise ValueError(
        "Model release cannot contain links: "
        f"{member.name}"
      )

    if (
      not archive_path.parts
      or archive_path.parts[0]
      != "models"
    ):
      raise ValueError(
        "Model release contains an unexpected path: "
        f"{member.name}"
      )

    member_names.add(
      member.name.rstrip("/")
    )

  required_registry = (
    "models/production/active_models.json"
  )

  if required_registry not in member_names:
    raise ValueError(
      "Model release does not contain "
      "active_models.json."
    )

  return members


def extract_release_archive(
  archive_path: Path,
  extraction_root: Path,
) -> Path:
  """Extract one validated archive."""
  extraction_root.mkdir(
    parents=True,
    exist_ok=True,
  )

  with tarfile.open(
    archive_path,
    mode="r:gz",
  ) as archive:
    members = validate_archive_members(
      archive
    )

    archive.extractall(
      path=extraction_root,
      members=members,
      filter="data",
    )

  return extraction_root


def resolve_release_path(
  extraction_root: Path,
  relative_path: str,
) -> Path:
  """Resolve a release path without allowing traversal."""
  path = Path(
    str(
      relative_path
    )
  )

  if path.is_absolute():
    raise ValueError(
      "Release paths must be repository-relative."
    )

  root = extraction_root.resolve()
  resolved = (
    extraction_root / path
  ).resolve()

  if (
    resolved != root
    and root not in resolved.parents
  ):
    raise ValueError(
      "Release path escapes the extraction root: "
      f"{relative_path}"
    )

  return resolved


def load_release_manifest(
  extraction_root: Path,
) -> tuple[Path, dict]:
  """Load the single release manifest."""
  manifest_paths = list(
    extraction_root.glob(
      "models/production/releases/"
      "*/release_manifest.json"
    )
  )

  if len(manifest_paths) != 1:
    raise ValueError(
      "Model release must contain exactly one "
      "release_manifest.json."
    )

  manifest_path = manifest_paths[0]

  manifest = json.loads(
    manifest_path.read_text(
      encoding="utf-8"
    )
  )

  required_fields = {
    "schema_version",
    "release_id",
    "release_hash",
    "file_count",
    "files",
  }

  missing_fields = (
    required_fields
    - set(manifest)
  )

  if missing_fields:
    raise ValueError(
      "Release manifest is missing fields: "
      f"{sorted(missing_fields)}"
    )

  if manifest[
    "schema_version"
  ] != 1:
    raise ValueError(
      "Unsupported release manifest schema."
    )

  if len(
    manifest["files"]
  ) != int(
    manifest["file_count"]
  ):
    raise ValueError(
      "Release manifest file count does not match."
    )

  return (
    manifest_path,
    manifest,
  )


def verify_release_manifest_files(
  extraction_root: Path,
  manifest: dict,
) -> None:
  """Verify every checksum recorded in the manifest."""
  for file_record in manifest[
    "files"
  ]:
    required_fields = {
      "path",
      "bytes",
      "sha256",
    }

    missing_fields = (
      required_fields
      - set(file_record)
    )

    if missing_fields:
      raise ValueError(
        "Release file record is missing fields: "
        f"{sorted(missing_fields)}"
      )

    file_path = resolve_release_path(
      extraction_root=extraction_root,
      relative_path=file_record[
        "path"
      ],
    )

    if not file_path.is_file():
      raise FileNotFoundError(
        f"Release file not found: {file_path}"
      )

    if file_path.stat().st_size != int(
      file_record["bytes"]
    ):
      raise ValueError(
        "Release file size mismatch: "
        f"{file_record['path']}"
      )

    expected_checksum = (
      normalize_expected_sha256(
        file_record["sha256"]
      )
    )

    actual_checksum = (
      calculate_file_sha256(
        file_path
      )
    )

    if (
      actual_checksum
      != expected_checksum
    ):
      raise ValueError(
        "Release file checksum mismatch: "
        f"{file_record['path']}"
      )


def validate_release_registry(
  extraction_root: Path,
  manifest: dict,
) -> dict:
  """Validate registry metadata and artifact references."""
  registry_path = (
    extraction_root
    / "models"
    / "production"
    / "active_models.json"
  )

  registry = json.loads(
    registry_path.read_text(
      encoding="utf-8"
    )
  )

  if (
    registry.get(
      "release_id"
    )
    != manifest[
      "release_id"
    ]
  ):
    raise ValueError(
      "Registry and manifest release IDs differ."
    )

  tasks = registry.get(
    "tasks"
  )

  if not isinstance(
    tasks,
    dict,
  ):
    raise ValueError(
      "Release registry contains no task definitions."
    )

  for task_name in [
    "regression",
    "classification",
  ]:
    if task_name not in tasks:
      raise ValueError(
        "Release registry is missing task: "
        f"{task_name}"
      )

    metadata_path = resolve_release_path(
      extraction_root=extraction_root,
      relative_path=tasks[
        task_name
      ][
        "metadata_path"
      ],
    )

    if not metadata_path.is_file():
      raise FileNotFoundError(
        f"Release metadata not found: {metadata_path}"
      )

    with metadata_path.open(
      newline="",
      encoding="utf-8",
    ) as metadata_stream:
      rows = list(
        csv.DictReader(
          metadata_stream
        )
      )

    if not rows:
      raise ValueError(
        f"Release {task_name} metadata is empty."
      )

    horizons = {
      int(
        row[
          "horizon_hours"
        ]
      )
      for row in rows
    }

    if horizons != EXPECTED_HORIZONS:
      raise ValueError(
        f"Release {task_name} horizons must be "
        f"{sorted(EXPECTED_HORIZONS)}."
      )

    for row in rows:
      artifact_path = resolve_release_path(
        extraction_root=extraction_root,
        relative_path=row[
          "artifact_path"
        ],
      )

      if not artifact_path.is_file():
        raise FileNotFoundError(
          "Release artifact not found: "
          f"{artifact_path}"
        )

  return registry


def verify_extracted_release(
  extraction_root: Path,
) -> dict:
  """Verify the complete extracted release."""
  _, manifest = load_release_manifest(
    extraction_root
  )

  verify_release_manifest_files(
    extraction_root=extraction_root,
    manifest=manifest,
  )

  registry = validate_release_registry(
    extraction_root=extraction_root,
    manifest=manifest,
  )

  return {
    "release_id": manifest[
      "release_id"
    ],
    "release_hash": manifest[
      "release_hash"
    ],
    "verified_files": int(
      manifest[
        "file_count"
      ]
    ),
    "registry": registry,
  }


def read_installed_release_id(
  project_root: Path,
) -> str | None:
  """Read the release already installed locally."""
  registry_path = (
    project_root
    / "models"
    / "production"
    / "active_models.json"
  )

  if not registry_path.exists():
    return None

  try:
    registry = json.loads(
      registry_path.read_text(
        encoding="utf-8"
      )
    )
  except (
    json.JSONDecodeError,
    OSError,
  ):
    return None

  release_id = registry.get(
    "release_id"
  )

  if release_id is None:
    return None

  return str(
    release_id
  )


def install_release_archive(
  archive_path: Path,
  expected_sha256: str,
  project_root: Path = Path("."),
) -> dict:
  """Verify and atomically install one release archive."""
  expected_checksum = (
    normalize_expected_sha256(
      expected_sha256
    )
  )

  actual_checksum = (
    calculate_file_sha256(
      archive_path
    )
  )

  if (
    actual_checksum
    != expected_checksum
  ):
    raise ValueError(
      "Model release archive checksum mismatch."
    )

  project_root = (
    project_root.resolve()
  )

  models_root = (
    project_root / "models"
  )

  models_root.mkdir(
    parents=True,
    exist_ok=True,
  )

  operation_id = uuid4().hex

  staging_root = (
    models_root
    / f".release-install-{operation_id}"
  )

  backup_path = (
    models_root
    / f".production-backup-{operation_id}"
  )

  destination_path = (
    models_root / "production"
  )

  try:
    extract_release_archive(
      archive_path=archive_path,
      extraction_root=staging_root,
    )

    verification = (
      verify_extracted_release(
        staging_root
      )
    )

    release_id = verification[
      "release_id"
    ]

    if (
      read_installed_release_id(
        project_root
      )
      == release_id
    ):
      return {
        **verification,
        "status": "already_installed",
        "registry_path": str(
          destination_path
          / "active_models.json"
        ),
      }

    source_path = (
      staging_root
      / "models"
      / "production"
    )

    if not source_path.is_dir():
      raise FileNotFoundError(
        "Extracted release has no "
        "models/production directory."
      )

    if destination_path.exists():
      os.replace(
        destination_path,
        backup_path,
      )

    try:
      os.replace(
        source_path,
        destination_path,
      )
    except Exception:
      if (
        backup_path.exists()
        and not destination_path.exists()
      ):
        os.replace(
          backup_path,
          destination_path,
        )

      raise

    if backup_path.exists():
      shutil.rmtree(
        backup_path
      )

    return {
      **verification,
      "status": "installed",
      "registry_path": str(
        destination_path
        / "active_models.json"
      ),
    }
  finally:
    if staging_root.exists():
      shutil.rmtree(
        staging_root
      )

    if backup_path.exists():
      shutil.rmtree(
        backup_path
      )


def install_release_from_url(
  release_url: str,
  expected_sha256: str,
  project_root: Path = Path("."),
) -> dict:
  """Download, verify and install one model release."""
  project_root = (
    project_root.resolve()
  )

  download_directory = (
    project_root / "models"
  )

  download_directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  archive_path = (
    download_directory
    / (
      ".model-release-download-"
      f"{uuid4().hex}.tar.gz"
    )
  )

  try:
    download_release_archive(
      release_url=release_url,
      destination_path=archive_path,
    )

    return install_release_archive(
      archive_path=archive_path,
      expected_sha256=(
        expected_sha256
      ),
      project_root=project_root,
    )
  finally:
    if archive_path.exists():
      archive_path.unlink()


def install_release_from_environment(
  project_root: Path = Path("."),
) -> dict:
  """Install the release configured through environment variables."""
  release_url = os.environ.get(
    MODEL_RELEASE_URL_ENV
  )

  expected_sha256 = os.environ.get(
    MODEL_RELEASE_SHA256_ENV
  )

  missing_variables = [
    variable_name
    for variable_name, value in [
      (
        MODEL_RELEASE_URL_ENV,
        release_url,
      ),
      (
        MODEL_RELEASE_SHA256_ENV,
        expected_sha256,
      ),
    ]
    if not value
  ]

  if missing_variables:
    raise RuntimeError(
      "Missing model release environment variables: "
      f"{missing_variables}"
    )

  return install_release_from_url(
    release_url=release_url,
    expected_sha256=expected_sha256,
    project_root=project_root,
  )


def main() -> None:
  """Install the configured production release."""
  result = (
    install_release_from_environment()
  )

  print("Production model release")
  print("========================")

  print(
    f"Status: {result['status']}"
  )

  print(
    f"Release ID: {result['release_id']}"
  )

  print(
    "Verified files: "
    f"{result['verified_files']}"
  )

  print(
    "Registry: "
    f"{result['registry_path']}"
  )


if __name__ == "__main__":
  main()
