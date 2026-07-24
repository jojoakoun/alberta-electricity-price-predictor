"""Define the paths that may enter a distributable project export."""

from __future__ import annotations

import fnmatch
from pathlib import Path, PurePosixPath


EXCLUDED_DIRECTORIES = {
  ".git",
  ".venv",
  "venv",
  "env",
  "node_modules",
  "dist",
  "build",
  "coverage",
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  ".ruff_cache",
  ".cache",
  ".parcel-cache",
  ".turbo",
  ".next",
  "context_exports",
  "docs",
  "reports",
  "models",
  "local",
  "logs",
  "phase7_manual_pipeline_checks",
  "project_cleanup_reports",
}

EXCLUDED_FILENAMES = {
  ".DS_Store",
}

EXCLUDED_NAME_PREFIXES = (
  "codex-",
  "claude-",
  "audit-",
)

SECRET_PATTERNS = {
  "*.pem",
  "*.key",
  "*.p12",
  "*.pfx",
  "id_rsa",
  "id_rsa.*",
  "credentials.json",
  "service-account*.json",
}

KNOWN_TEXT_NAMES = {
  "Makefile",
  "Dockerfile",
  "Procfile",
  ".gitignore",
  ".dockerignore",
  ".editorconfig",
  ".npmrc",
  ".nvmrc",
  ".python-version",
}

KNOWN_TEXT_SUFFIXES = {
  ".bash",
  ".cjs",
  ".conf",
  ".css",
  ".csv",
  ".dockerfile",
  ".env.example",
  ".gitkeep",
  ".graphql",
  ".html",
  ".ini",
  ".js",
  ".json",
  ".jsonl",
  ".jsx",
  ".lock",
  ".md",
  ".mjs",
  ".prisma",
  ".properties",
  ".py",
  ".rst",
  ".scss",
  ".sh",
  ".sql",
  ".svg",
  ".toml",
  ".txt",
  ".xml",
  ".yaml",
  ".yml",
  ".zsh",
}


def is_private_environment_filename(filename: str) -> bool:
  """Return whether an environment filename may contain private values."""
  return filename != ".env.example" and (
    filename == ".env" or filename.startswith(".env.")
  )


def exclusion_reason(relative_path: Path) -> str | None:
  """Return the stable exclusion reason for one repository-relative path."""
  if any(part in EXCLUDED_DIRECTORIES for part in relative_path.parts):
    return "generated/local-only directory"

  filename = relative_path.name

  if filename in EXCLUDED_FILENAMES:
    return "local artifact"

  if filename.startswith(EXCLUDED_NAME_PREFIXES):
    return "local audit artifact"

  if is_private_environment_filename(filename):
    return "environment or secret file"

  for pattern in SECRET_PATTERNS:
    if fnmatch.fnmatch(filename, pattern):
      return "credential or private key"

  return None


def validate_archive_path(path: str) -> None:
  """Reject unsafe or policy-excluded paths before archive verification."""
  parsed = PurePosixPath(path)

  if parsed.is_absolute() or ".." in parsed.parts:
    raise ValueError(f"Unsafe archive path: {path}")

  reason = exclusion_reason(Path(*parsed.parts))

  if reason:
    raise ValueError(f"Forbidden archive path: {path}")
