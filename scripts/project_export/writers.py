"""Write deterministic project-export manifests, context, and archives."""

from __future__ import annotations

import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from .inventory import ProjectFile


MAX_INLINE_TEXT_BYTES = 2 * 1024 * 1024


def run_command(command: list[str], root: Path) -> str:
  """Capture diagnostic command output without making export creation fail."""
  try:
    result = subprocess.run(
      command,
      cwd=root,
      check=False,
      capture_output=True,
      text=True,
    )
  except OSError as error:
    return f"Command unavailable: {error}"

  output = result.stdout

  if result.stderr:
    output += result.stderr

  return output.rstrip()


def write_manifests(
  files: list[ProjectFile],
  excluded: list[tuple[str, str]],
  manifest_path: Path,
  excluded_path: Path,
) -> None:
  """Write stable included and excluded path inventories."""
  manifest_path.parent.mkdir(parents=True, exist_ok=True)
  manifest_lines = ["path\tsize_bytes\tsha256\tkind"]

  for item in files:
    manifest_lines.append(
      "\t".join([
        item.relative_path.as_posix(),
        str(item.size_bytes),
        item.sha256,
        item.kind,
      ])
    )

  manifest_path.write_text(
    "\n".join(manifest_lines) + "\n",
    encoding="utf-8",
  )

  excluded_lines = ["path\treason"]
  excluded_lines.extend(f"{path}\t{reason}" for path, reason in excluded)
  excluded_path.write_text(
    "\n".join(excluded_lines) + "\n",
    encoding="utf-8",
  )


def append_command_section(
  output: list[str],
  title: str,
  command: list[str],
  root: Path,
) -> None:
  output.extend(["", f"===== {title} =====", run_command(command, root)])


def large_text_preview(path: Path) -> str:
  """Return the established bounded preview for large text files."""
  try:
    with path.open("r", encoding="utf-8", errors="replace") as stream:
      first_lines: list[str] = []

      for _ in range(20):
        line = stream.readline()

        if not line:
          break

        first_lines.append(line.rstrip())

    return "\n".join([
      "[Large text file: full content is in the ZIP]",
      "",
      "----- FIRST 20 LINES -----",
      *first_lines,
    ])
  except OSError as error:
    return f"[Unable to preview file: {error}]"


def write_context(
  files: list[ProjectFile],
  excluded: list[tuple[str, str]],
  root: Path,
  context_path: Path,
  manifest_path: Path,
  excluded_path: Path,
) -> None:
  """Write the human-readable project context without changing its sections."""
  # Git diagnostics must use the same allowlist as the archive. Otherwise a
  # tracked private file could leak through a raw status or diff section even
  # though the inventory correctly excluded it.
  included_pathspec = [
    (
      ":(top,literal)"
      f"{item.relative_path.as_posix()}"
    )
    for item in files
  ]
  if not included_pathspec:
    included_pathspec = [
      ":(top,literal)__wattwise_export_empty_inventory__",
    ]

  scoped_paths = ["--", *included_pathspec]

  output: list[str] = [
    "===== PROJECT CONTEXT GENERATED AT =====",
    datetime.now().astimezone().isoformat(),
    "",
    "===== EXPORT POLICY =====",
    "This export includes project-relevant distributable files.",
    (
      "Dependencies, generated builds, caches, Git metadata, virtual "
      "environments, local-only evidence, and secret files are excluded."
    ),
    (
      "Large text files and binary files are represented in this document by "
      "metadata and are included in the ZIP archive."
    ),
    "",
    "===== EXPORT SUMMARY =====",
    f"Included files: {len(files)}",
    f"Excluded paths: {len(excluded)}",
    f"Inline text limit: {MAX_INLINE_TEXT_BYTES} bytes",
  ]

  command_sections = [
    ("BRANCH", ["git", "branch", "--show-current"]),
    ("HEAD COMMIT", ["git", "log", "-1", "--decorate", "--oneline"]),
    (
      "GIT STATUS",
      ["git", "status", "--short", "--no-renames", *scoped_paths],
    ),
    (
      "GIT STATUS INCLUDING IGNORED FILES",
      [
        "git",
        "status",
        "--short",
        "--ignored",
        "--no-renames",
        *scoped_paths,
      ],
    ),
    (
      "GIT DIFF STAT",
      ["git", "diff", "--stat", "--no-renames", *scoped_paths],
    ),
    (
      "GIT DIFF",
      ["git", "diff", "--no-renames", *scoped_paths],
    ),
    ("RECENT COMMITS", ["git", "log", "--oneline", "-20"]),
    ("PYTHON VERSION", ["python3", "--version"]),
    ("NODE VERSION", ["node", "--version"]),
    ("NPM VERSION", ["npm", "--version"]),
    ("DOCKER VERSION", ["docker", "--version"]),
  ]

  for title, command in command_sections:
    append_command_section(output, title, command, root)

  output.extend([
    "",
    "===== INCLUDED FILE INVENTORY =====",
    manifest_path.read_text(encoding="utf-8").rstrip(),
    "",
    "===== INTENTIONALLY EXCLUDED PATHS =====",
    excluded_path.read_text(encoding="utf-8").rstrip(),
    "",
    "===== FILE CONTENTS =====",
  ])

  for item in files:
    output.extend([
      "",
      f"===== {item.relative_path.as_posix()} =====",
      f"[size={item.size_bytes}; sha256={item.sha256}; kind={item.kind}]",
    ])

    if item.kind == "binary":
      output.append("[Binary file: full file is included in the ZIP archive]")
      continue

    if item.size_bytes > MAX_INLINE_TEXT_BYTES:
      output.append(large_text_preview(item.absolute_path))
      continue

    try:
      content = item.absolute_path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
      output.append(f"[Unable to read file: {error}]")
      continue

    output.append(content.rstrip())

  context_path.write_text("\n".join(output) + "\n", encoding="utf-8")


def write_zip(files: list[ProjectFile], zip_path: Path) -> None:
  """Write files under their repository-relative POSIX paths."""
  zip_path.parent.mkdir(parents=True, exist_ok=True)

  if zip_path.exists():
    zip_path.unlink()

  with zipfile.ZipFile(
    zip_path,
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=6,
  ) as archive:
    for item in files:
      archive.write(item.absolute_path, arcname=item.relative_path.as_posix())
