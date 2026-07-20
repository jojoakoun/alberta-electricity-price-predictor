import json
from pathlib import Path
import re


CONFIG_PATH = Path(
  "railway.worker.json"
)

MAKEFILE_PATH = Path(
  "Makefile"
)


def load_worker_config() -> dict:
  """Load the Railway worker configuration."""
  return json.loads(
    CONFIG_PATH.read_text(
      encoding="utf-8"
    )
  )


def load_makefile() -> str:
  """Load the project Makefile."""
  return MAKEFILE_PATH.read_text(
    encoding="utf-8"
  )


def extract_make_target(
  makefile: str,
  target_name: str,
) -> str:
  """Extract one Makefile target body."""
  pattern = re.compile(
    rf"(?ms)^{re.escape(target_name)}:\n"
    rf"(?P<body>.*?)"
    rf"(?=^[A-Za-z0-9_.-]+:|\Z)"
  )

  match = pattern.search(
    makefile
  )

  if match is None:
    raise AssertionError(
      f"Missing Makefile target: {target_name}"
    )

  return match.group(
    "body"
  )


def test_worker_uses_railpack() -> None:
  config = load_worker_config()

  assert (
    config["build"]["builder"]
    == "RAILPACK"
  )

  assert config[
    "build"
  ][
    "buildCommand"
  ] == (
    "pip install -r requirements.txt "
    "&& pip install -e ."
  )


def test_worker_uses_canonical_make_target() -> None:
  config = load_worker_config()

  assert config[
    "deploy"
  ][
    "startCommand"
  ] == "make worker-run"


def test_models_install_supports_remote_release() -> None:
  makefile = load_makefile()

  target = extract_make_target(
    makefile=makefile,
    target_name="models-install",
  )

  assert (
    "MODEL_RELEASE_URL"
    in target
  )

  assert (
    "MODEL_RELEASE_SHA256"
    in target
  )

  assert (
    "$(PYTHON) -m "
    "electricity_predictor.serving."
    "release_installer"
    in target
  )


def test_models_install_supports_local_registry() -> None:
  makefile = load_makefile()

  target = extract_make_target(
    makefile=makefile,
    target_name="models-install",
  )

  assert (
    "models/production/"
    "active_models.json"
    in target
  )

  assert (
    "Using local active model registry"
    in target
  )


def test_worker_prepares_models_before_refresh() -> None:
  makefile = load_makefile()

  target = extract_make_target(
    makefile=makefile,
    target_name="worker-run",
  )

  models_command = (
    "$(MAKE) models-install"
  )

  refresh_command = (
    "$(MAKE) app-refresh"
  )

  assert models_command in target
  assert refresh_command in target

  assert target.index(
    models_command
  ) < target.index(
    refresh_command
  )


def test_legacy_railway_alias_uses_worker_run() -> None:
  makefile = load_makefile()

  target = extract_make_target(
    makefile=makefile,
    target_name="railway-worker",
  )

  assert (
    "$(MAKE) worker-run"
    in target
  )


def test_worker_has_hourly_cron_schedule() -> None:
  config = load_worker_config()

  assert config[
    "deploy"
  ][
    "cronSchedule"
  ] == "15 * * * *"

  assert config[
    "deploy"
  ][
    "restartPolicyType"
  ] == "NEVER"
