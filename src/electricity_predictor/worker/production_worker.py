"""Start the production worker that installs models, refreshes prices and predicts."""

import os

from dotenv import load_dotenv

from electricity_predictor.worker.application_prediction_pipeline import (
  run_application_prediction_pipeline,
)
from electricity_predictor.config import PROJECT_ROOT
from electricity_predictor.serving.model_registry import (
  ACTIVE_MODEL_REGISTRY_PATH,
  resolve_active_metadata_paths,
)
from electricity_predictor.serving.release_installer import (
  MODEL_RELEASE_SHA256_ENV,
  MODEL_RELEASE_URL_ENV,
  install_release_from_environment,
)


def ensure_models_available() -> dict:
  """Install a configured release or validate a development registry.

  Production release URL and checksum values are inseparable. Local registry
  fallback exists for development only and still validates both active tasks.
  """
  load_dotenv(PROJECT_ROOT / ".env")

  release_url = os.environ.get(
    MODEL_RELEASE_URL_ENV
  )
  release_sha256 = os.environ.get(
    MODEL_RELEASE_SHA256_ENV
  )

  if release_url or release_sha256:
    if not release_url or not release_sha256:
      raise RuntimeError(
        "MODEL_RELEASE_URL and MODEL_RELEASE_SHA256 "
        "must be set together."
      )

    return install_release_from_environment(
      project_root=PROJECT_ROOT
    )

  registry_path = (
    PROJECT_ROOT / ACTIVE_MODEL_REGISTRY_PATH
  )

  if not registry_path.is_file():
    raise FileNotFoundError(
      "No active models are available. Production requires "
      "MODEL_RELEASE_URL and MODEL_RELEASE_SHA256."
    )

  (
    regression_metadata_path,
    classification_metadata_path,
    registry,
  ) = resolve_active_metadata_paths(
    registry_path=registry_path
  )

  return {
    "status": "local_registry",
    "registry": registry,
    "regression_metadata_path": str(
      regression_metadata_path
    ),
    "classification_metadata_path": str(
      classification_metadata_path
    ),
  }


def run_production_prediction_worker() -> dict:
  """Prepare models, synchronize operational data, and predict."""
  ensure_models_available()

  return run_application_prediction_pipeline()


def main() -> None:
  """Run one complete production worker cycle."""
  result = run_production_prediction_worker()

  print(
    "Production worker completed. "
    f"Synchronized rows: {result['synchronized_rows']}. "
    f"Run ID: {result['run_id']}."
  )


if __name__ == "__main__":
  main()
