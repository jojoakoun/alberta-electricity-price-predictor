#!/usr/bin/env python3

from __future__ import annotations

import csv
import hashlib
import zipfile
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "context_exports"

ZIP_PATH = (
  EXPORT_DIR
  / "alberta-electricity-price-predictor.zip"
)

MANIFEST_PATH = (
  EXPORT_DIR
  / "project_files_manifest.txt"
)

CONTEXT_PATH = (
  EXPORT_DIR
  / "project_context_full.txt"
)

EXCLUDED_PATH = (
  EXPORT_DIR
  / "project_excluded_manifest.txt"
)

FORBIDDEN_FILES = {
  ".env",
}

FORBIDDEN_PREFIXES = (
  ".git/",
  ".venv/",
  "context_exports/",
  "local/",
  "logs/",
  "node_modules/",
)


def sha256_bytes(content: bytes) -> str:
  return hashlib.sha256(
    content
  ).hexdigest()


def load_manifest() -> dict[str, dict[str, str]]:
  with MANIFEST_PATH.open(
    "r",
    encoding="utf-8",
    newline="",
  ) as manifest_file:
    rows = list(
      csv.DictReader(
        manifest_file,
        delimiter="\t",
      )
    )

  manifest = {
    row["path"]: row
    for row in rows
  }

  if len(manifest) != len(rows):
    raise ValueError(
      "Duplicate paths exist in the manifest."
    )

  return manifest


def validate_archive_path(path: str) -> None:
  parsed = PurePosixPath(path)

  if (
    parsed.is_absolute()
    or ".." in parsed.parts
  ):
    raise ValueError(
      f"Unsafe archive path: {path}"
    )

  if (
    path in FORBIDDEN_FILES
    or path.startswith(
      FORBIDDEN_PREFIXES
    )
  ):
    raise ValueError(
      f"Forbidden archive path: {path}"
    )


def main() -> None:
  required_files = (
    ZIP_PATH,
    MANIFEST_PATH,
    CONTEXT_PATH,
    EXCLUDED_PATH,
  )

  for path in required_files:
    if (
      not path.is_file()
      or path.stat().st_size == 0
    ):
      raise FileNotFoundError(
        f"Missing or empty export file: {path}"
      )

  manifest = load_manifest()

  with zipfile.ZipFile(
    ZIP_PATH,
    "r",
  ) as archive:
    corrupt_member = archive.testzip()

    if corrupt_member:
      raise ValueError(
        f"Corrupt ZIP member: {corrupt_member}"
      )

    members = [
      member
      for member in archive.infolist()
      if not member.is_dir()
    ]

    paths = [
      member.filename
      for member in members
    ]

    if len(paths) != len(set(paths)):
      raise ValueError(
        "Duplicate paths exist in the ZIP."
      )

    for path in paths:
      validate_archive_path(path)

    manifest_paths = set(manifest)
    archive_paths = set(paths)

    missing = sorted(
      manifest_paths - archive_paths
    )

    unexpected = sorted(
      archive_paths - manifest_paths
    )

    if missing:
      raise ValueError(
        f"Files missing from ZIP: {missing}"
      )

    if unexpected:
      raise ValueError(
        f"Unexpected ZIP files: {unexpected}"
      )

    for member in members:
      row = manifest[
        member.filename
      ]

      content = archive.read(
        member
      )

      if len(content) != int(
        row["size_bytes"]
      ):
        raise ValueError(
          f"Size mismatch: {member.filename}"
        )

      if sha256_bytes(
        content
      ) != row["sha256"]:
        raise ValueError(
          f"Checksum mismatch: {member.filename}"
        )

  print(
    f"Verified files: {len(manifest)}"
  )
  print("Missing manifest files: 0")
  print("Unexpected ZIP files: 0")
  print("Checksum mismatches: 0")
  print("Forbidden exported paths: 0")
  print(
    "Project export verification passed."
  )


if __name__ == "__main__":
  main()
