"""Deployment contract tests for the scheduled Railway worker."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKER_CONFIG = ROOT / "railway.worker.json"
PYPROJECT = ROOT / "pyproject.toml"
MAKEFILE = ROOT / "Makefile"


def load_worker_config() -> dict:
  """Load the Railway worker configuration."""
  return json.loads(
    WORKER_CONFIG.read_text(encoding="utf-8")
  )


def collect_strings(value) -> list[str]:
  """Collect every string contained in nested JSON data."""
  if isinstance(value, str):
    return [value]

  if isinstance(value, list):
    strings = []
    for item in value:
      strings.extend(collect_strings(item))
    return strings

  if isinstance(value, dict):
    strings = []
    for item in value.values():
      strings.extend(collect_strings(item))
    return strings

  return []


def normalize_whitespace(value: str) -> str:
  """Collapse formatting whitespace for command comparisons."""
  return " ".join(value.split())


def test_worker_config_uses_installed_entry_point() -> None:
  """Railway must invoke the installed worker directly."""
  commands = " ".join(
    collect_strings(load_worker_config())
  )

  assert "wattwise-worker" in commands


def test_worker_config_does_not_use_removed_make_aliases() -> None:
  """Deployment must not depend on legacy Makefile aliases."""
  commands = " ".join(
    collect_strings(load_worker_config())
  )

  removed_aliases = (
    "make worker-run",
    "make sync-and-predict",
    "make models-install",
  )

  for alias in removed_aliases:
    assert alias not in commands


def test_python_package_defines_worker_command() -> None:
  """The installed command must be declared by the package."""
  pyproject = PYPROJECT.read_text(encoding="utf-8")

  assert "wattwise-worker" in pyproject
  assert (
    "electricity_predictor.worker.production_worker"
    in pyproject
  )


def test_sync_uses_canonical_prediction_pipeline() -> None:
  """The canonical sync command must call the worker pipeline."""
  makefile = normalize_whitespace(
    MAKEFILE.read_text(encoding="utf-8")
  )

  assert (
    "electricity_predictor.worker."
    "application_prediction_pipeline"
    in makefile
  )
