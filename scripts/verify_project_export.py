#!/usr/bin/env python3

"""Verify the ignored WattWise project export without extracting it."""

from __future__ import annotations

from pathlib import Path

from project_export.verification import verify_project_export


ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR = ROOT / "context_exports"
ZIP_PATH = EXPORT_DIR / "alberta-electricity-price-predictor.zip"
MANIFEST_PATH = EXPORT_DIR / "project_files_manifest.txt"
CONTEXT_PATH = EXPORT_DIR / "project_context_full.txt"
EXCLUDED_PATH = EXPORT_DIR / "project_excluded_manifest.txt"


def main() -> None:
  """Verify the configured export outputs and print the stable summary."""
  verified_count = verify_project_export(
    zip_path=ZIP_PATH,
    manifest_path=MANIFEST_PATH,
    context_path=CONTEXT_PATH,
    excluded_path=EXCLUDED_PATH,
  )

  print(f"Verified files: {verified_count}")
  print("Missing manifest files: 0")
  print("Unexpected ZIP files: 0")
  print("Checksum mismatches: 0")
  print("Forbidden exported paths: 0")
  print("Project export verification passed.")


if __name__ == "__main__":
  main()
