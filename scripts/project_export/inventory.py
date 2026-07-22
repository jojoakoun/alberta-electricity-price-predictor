"""Collect a deterministic inventory of exportable project files."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from .policy import (
  KNOWN_TEXT_NAMES,
  KNOWN_TEXT_SUFFIXES,
  exclusion_reason,
)


@dataclass(frozen=True)
class ProjectFile:
  absolute_path: Path
  relative_path: Path
  size_bytes: int
  sha256: str
  kind: str


def calculate_sha256(path: Path) -> str:
  """Return the SHA-256 digest of a file without loading it all at once."""
  digest = hashlib.sha256()

  with path.open("rb") as stream:
    while chunk := stream.read(1024 * 1024):
      digest.update(chunk)

  return digest.hexdigest()


def is_text_file(path: Path) -> bool:
  """Classify known or UTF-8-compatible files as text."""
  if path.name in KNOWN_TEXT_NAMES:
    return True

  suffixes = "".join(path.suffixes).lower()

  if suffixes in KNOWN_TEXT_SUFFIXES or path.suffix.lower() in KNOWN_TEXT_SUFFIXES:
    return True

  try:
    sample = path.read_bytes()[:65536]
  except OSError:
    return False

  if b"\x00" in sample:
    return False

  try:
    sample.decode("utf-8")
  except UnicodeDecodeError:
    return False

  return True


def collect_project_files(
  root: Path,
) -> tuple[list[ProjectFile], list[tuple[str, str]]]:
  """Collect allowed regular files beneath root in deterministic path order."""
  root = root.resolve()
  project_files: list[ProjectFile] = []
  excluded: list[tuple[str, str]] = []

  for current_root, directories, filenames in os.walk(root):
    current_path = Path(current_root)
    relative_directory = current_path.relative_to(root)
    kept_directories: list[str] = []

    for directory in directories:
      relative_path = relative_directory / directory
      absolute_path = current_path / directory
      reason = exclusion_reason(relative_path)

      if absolute_path.is_symlink():
        reason = "symbolic link"

      if reason:
        excluded.append((f"{relative_path.as_posix()}/", reason))
      else:
        kept_directories.append(directory)

    directories[:] = kept_directories

    for filename in filenames:
      absolute_path = current_path / filename
      relative_path = absolute_path.relative_to(root)
      reason = exclusion_reason(relative_path)

      if absolute_path.is_symlink():
        reason = "symbolic link"

      if reason:
        excluded.append((relative_path.as_posix(), reason))
        continue

      if not absolute_path.is_file():
        continue

      size_bytes = absolute_path.stat().st_size
      project_files.append(
        ProjectFile(
          absolute_path=absolute_path,
          relative_path=relative_path,
          size_bytes=size_bytes,
          sha256=calculate_sha256(absolute_path),
          kind="text" if is_text_file(absolute_path) else "binary",
        )
      )

  project_files.sort(key=lambda item: item.relative_path.as_posix().lower())
  excluded.sort(key=lambda item: item[0].lower())
  return project_files, excluded
