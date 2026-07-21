from pathlib import Path
from unittest.mock import call, patch

import pytest

import electricity_predictor.worker.production as production
from electricity_predictor.worker.operational_pipeline import (
  run_application_pipeline,
)
from electricity_predictor.worker.production import (
  ensure_models_available,
  run_production_worker,
)


def test_production_imports_relocated_operational_pipeline() -> None:
  assert (
    production.run_application_pipeline
    is run_application_pipeline
  )


def test_production_worker_installs_models_before_operational_pipeline() -> None:
  execution_order: list[str] = []

  with (
    patch(
      "electricity_predictor.worker.production."
      "ensure_models_available",
      side_effect=lambda: execution_order.append("models"),
    ) as ensure_models,
    patch(
      "electricity_predictor.worker.production."
      "run_application_pipeline",
      side_effect=lambda: (
        execution_order.append("pipeline")
        or {
          "synchronized_rows": 2,
          "run_id": 19,
          "decisions": [],
        }
      ),
    ) as run_pipeline,
  ):
    result = run_production_worker()

  assert execution_order == [
    "models",
    "pipeline",
  ]
  assert result["run_id"] == 19
  assert ensure_models.call_args_list == [call()]
  assert run_pipeline.call_args_list == [call()]


def test_production_worker_stops_before_pipeline_when_models_fail() -> None:
  with (
    patch(
      "electricity_predictor.worker.production."
      "ensure_models_available",
      side_effect=RuntimeError("Models unavailable."),
    ),
    patch(
      "electricity_predictor.worker.production."
      "run_application_pipeline",
    ) as run_pipeline,
  ):
    with pytest.raises(
      RuntimeError,
      match="Models unavailable",
    ):
      run_production_worker()

  run_pipeline.assert_not_called()


def test_ensure_models_installs_complete_remote_release_configuration() -> None:
  with (
    patch.dict(
      "os.environ",
      {
        "MODEL_RELEASE_URL": "https://example.com/models.tar.gz",
        "MODEL_RELEASE_SHA256": "a" * 64,
      },
      clear=True,
    ),
    patch(
      "electricity_predictor.worker.production.load_dotenv"
    ),
    patch(
      "electricity_predictor.worker.production."
      "install_release_from_environment",
      return_value={"status": "installed"},
    ) as install_release,
  ):
    result = ensure_models_available()

  assert result == {"status": "installed"}
  install_release.assert_called_once()
  assert (
    install_release.call_args.kwargs["project_root"].name
    == "alberta-electricity-price-predictor"
  )


def test_ensure_models_rejects_partial_release_configuration() -> None:
  with (
    patch.dict(
      "os.environ",
      {
        "MODEL_RELEASE_URL": "https://example.com/models.tar.gz",
      },
      clear=True,
    ),
    patch(
      "electricity_predictor.worker.production.load_dotenv"
    ),
  ):
    with pytest.raises(
      RuntimeError,
      match="must be set together",
    ):
      ensure_models_available()


def test_ensure_models_accepts_valid_local_registry(
  tmp_path: Path,
) -> None:
  registry_path = tmp_path / "active_models.json"
  registry_path.write_text("{}", encoding="utf-8")

  with (
    patch.dict("os.environ", {}, clear=True),
    patch(
      "electricity_predictor.worker.production.load_dotenv"
    ),
    patch(
      "electricity_predictor.worker.production."
      "ACTIVE_MODEL_REGISTRY_PATH",
      registry_path,
    ),
    patch(
      "electricity_predictor.worker.production."
      "resolve_active_metadata_paths",
      return_value=(
        tmp_path / "regression.csv",
        tmp_path / "classification.csv",
        {"release_id": "local"},
      ),
    ),
  ):
    result = ensure_models_available()

  assert result["status"] == "local_registry"
  assert result["registry"] == {"release_id": "local"}


def test_ensure_models_rejects_missing_release_and_registry(
  tmp_path: Path,
) -> None:
  with (
    patch.dict("os.environ", {}, clear=True),
    patch(
      "electricity_predictor.worker.production.load_dotenv"
    ),
    patch(
      "electricity_predictor.worker.production."
      "ACTIVE_MODEL_REGISTRY_PATH",
      tmp_path / "missing.json",
    ),
  ):
    with pytest.raises(
      FileNotFoundError,
      match="No active models are available",
    ):
      ensure_models_available()
