#!/usr/bin/env python3

"""Create the ignored WattWise project context and archive outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

from project_export.inventory import collect_project_files
from project_export.writers import (
  write_context,
  write_manifests,
  write_zip,
)


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "context_exports"
CONTEXT_PATH = EXPORT_DIR / "project_context_full.txt"
ZIP_PATH = EXPORT_DIR / "alberta-electricity-price-predictor.zip"
MANIFEST_PATH = EXPORT_DIR / "project_files_manifest.txt"
EXCLUDED_PATH = EXPORT_DIR / "project_excluded_manifest.txt"


def main() -> None:
  """Create the requested export formats using the shared safety policy."""
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "--mode",
    choices={"context", "zip", "all"},
    default="all",
  )
  arguments = parser.parse_args()

  files, excluded = collect_project_files(ROOT)
  write_manifests(
    files=files,
    excluded=excluded,
    manifest_path=MANIFEST_PATH,
    excluded_path=EXCLUDED_PATH,
  )

  if arguments.mode in {"context", "all"}:
    write_context(
      files=files,
      excluded=excluded,
      root=ROOT,
      context_path=CONTEXT_PATH,
      manifest_path=MANIFEST_PATH,
      excluded_path=EXCLUDED_PATH,
    )

  if arguments.mode in {"zip", "all"}:
    write_zip(files=files, zip_path=ZIP_PATH)

  print(f"Included project files: {len(files)}")

  if CONTEXT_PATH.exists():
    print(f"Text context: {CONTEXT_PATH.relative_to(ROOT)}")

  if ZIP_PATH.exists():
    print(f"ZIP archive: {ZIP_PATH.relative_to(ROOT)}")

  print(f"Included manifest: {MANIFEST_PATH.relative_to(ROOT)}")
  print(f"Excluded manifest: {EXCLUDED_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
  main()
