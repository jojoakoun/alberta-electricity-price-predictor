from __future__ import annotations

from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.live_contract import (
  refit_live_models as refit_module,
)


def test_refit_module_has_no_activation_ownership():
  source_path = Path(
    refit_module.__file__
  )

  source = source_path.read_text(
    encoding="utf-8"
  )

  forbidden_fragments = (
    "activate_final_models",
    "ACTIVE_REGISTRY_PATH",
    "models/production/active_models.json",
    "write_active_registry",
    "initialize_active_registry",
    "read_active_registry",
    "os.replace",
  )

  for fragment in forbidden_fragments:
    assert fragment not in source


def test_refit_live_models_installs_bundle_without_registry_change(
  tmp_path,
  monkeypatch,
):
  training_data = pd.DataFrame({
    "datetime_universal_time":
      pd.to_datetime([
        "2026-01-01T00:00:00Z",
        "2026-01-01T01:00:00Z",
      ]),
  })

  temporary_root = (
    tmp_path
    / ".refit-tmp"
  )

  final_root = (
    tmp_path
    / "live-refit"
  )

  registry_path = (
    tmp_path
    / "active_models.json"
  )

  original_registry = (
    '{"registry":"must-remain-unchanged"}\n'
  )

  registry_path.write_text(
    original_registry,
    encoding="utf-8",
  )

  monkeypatch.setattr(
    refit_module,
    "TEMP_ROOT",
    temporary_root,
  )

  monkeypatch.setattr(
    refit_module,
    "FINAL_ROOT",
    final_root,
  )

  monkeypatch.setattr(
    refit_module,
    "load_training_data",
    lambda: training_data,
  )

  monkeypatch.setattr(
    refit_module,
    "load_candidate_metadata",
    lambda task: pd.DataFrame([{
      "task":
        task,
    }]),
  )

  def build_metadata(
    task_name: str,
  ) -> pd.DataFrame:
    artifact_name = (
      f"{task_name}_1h.joblib"
    )

    temporary_artifact = (
      refit_module.TEMP_ROOT
      / artifact_name
    )

    temporary_artifact.write_bytes(
      b"test-model"
    )

    return pd.DataFrame([{
      "horizon_hours":
        1,
      "artifact_path":
        str(
          refit_module.FINAL_ROOT
          / artifact_name
        ),
    }])

  monkeypatch.setattr(
    refit_module,
    "fit_regression_models",
    lambda data, metadata: (
      build_metadata(
        "regression"
      )
    ),
  )

  monkeypatch.setattr(
    refit_module,
    "fit_classification_models",
    lambda data, metadata: (
      build_metadata(
        "classification"
      )
    ),
  )

  class Predictor:
    def predict(self, features):
      return [
        0.0
      ]

  monkeypatch.setattr(
    refit_module.joblib,
    "load",
    lambda path: Predictor(),
  )

  result = (
    refit_module.refit_live_models()
  )

  assert final_root.is_dir()

  assert (
    final_root
    / "regression_metadata.csv"
  ).is_file()

  assert (
    final_root
    / "classification_metadata.csv"
  ).is_file()

  assert (
    final_root
    / "manifest.json"
  ).is_file()

  assert result[
    "final_model_directory"
  ] == str(
    final_root
  )

  assert result[
    "activation_performed"
  ] is False

  assert registry_path.read_text(
    encoding="utf-8"
  ) == original_registry
