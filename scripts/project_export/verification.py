"""Verify project-export manifests and ZIP payloads."""

from __future__ import annotations

import csv
import hashlib
import zipfile
from pathlib import Path

from .policy import validate_archive_path


def sha256_bytes(content: bytes) -> str:
  return hashlib.sha256(content).hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, dict[str, str]]:
  """Load a tab-separated manifest and reject duplicate paths."""
  with manifest_path.open("r", encoding="utf-8", newline="") as manifest_file:
    rows = list(csv.DictReader(manifest_file, delimiter="\t"))

  manifest = {row["path"]: row for row in rows}

  if len(manifest) != len(rows):
    raise ValueError("Duplicate paths exist in the manifest.")

  return manifest


def verify_project_export(
  zip_path: Path,
  manifest_path: Path,
  context_path: Path,
  excluded_path: Path,
) -> int:
  """Verify required outputs, safe paths, sizes, and manifest hashes."""
  for path in (zip_path, manifest_path, context_path, excluded_path):
    if not path.is_file() or path.stat().st_size == 0:
      raise FileNotFoundError(f"Missing or empty export file: {path}")

  manifest = load_manifest(manifest_path)

  with zipfile.ZipFile(zip_path, "r") as archive:
    corrupt_member = archive.testzip()

    if corrupt_member:
      raise ValueError(f"Corrupt ZIP member: {corrupt_member}")

    archive_members = archive.infolist()

    # Directory entries are not part of the file manifest, but their names
    # must still obey the same traversal and local-only path policy.
    for member in archive_members:
      validate_archive_path(member.filename)

    members = [member for member in archive_members if not member.is_dir()]
    paths = [member.filename for member in members]

    if len(paths) != len(set(paths)):
      raise ValueError("Duplicate paths exist in the ZIP.")

    manifest_paths = set(manifest)
    archive_paths = set(paths)
    missing = sorted(manifest_paths - archive_paths)
    unexpected = sorted(archive_paths - manifest_paths)

    if missing:
      raise ValueError(f"Files missing from ZIP: {missing}")

    if unexpected:
      raise ValueError(f"Unexpected ZIP files: {unexpected}")

    for member in members:
      row = manifest[member.filename]
      content = archive.read(member)

      if len(content) != int(row["size_bytes"]):
        raise ValueError(f"Size mismatch: {member.filename}")

      if sha256_bytes(content) != row["sha256"]:
        raise ValueError(f"Checksum mismatch: {member.filename}")

  return len(manifest)
