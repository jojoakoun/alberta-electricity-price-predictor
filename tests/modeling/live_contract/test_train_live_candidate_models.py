"""Tests for the isolated live candidate model bundle."""

import json
from pathlib import Path

import pytest
from sklearn.ensemble import (
  GradientBoostingClassifier,
  HistGradientBoostingRegressor,
)

from electricity_predictor.modeling.live_contract.train_live_candidate_models import (
  CLASSIFICATION_RESULTS_PATH,
  REGRESSION_RESULTS_PATH,
  build_classification_model,
  build_regression_model,
  parse_classification_parameters,
)


def test_candidate_validation_results_use_generated_report_paths():
  assert REGRESSION_RESULTS_PATH == Path(
    "reports/live_regression_validation_results.csv"
  )

  assert CLASSIFICATION_RESULTS_PATH == Path(
    "reports/live_classification_validation_results.csv"
  )

  assert (
    "phase7_manual_pipeline_checks"
    not in REGRESSION_RESULTS_PATH.parts
  )

  assert (
    "phase7_manual_pipeline_checks"
    not in CLASSIFICATION_RESULTS_PATH.parts
  )


def test_build_regression_model_uses_selected_parameters():
  model = build_regression_model({
    "learning_rate": 0.1,
    "max_iter": 100,
    "max_leaf_nodes": 31,
    "min_samples_leaf": 20,
    "l2_regularization": 1.0,
  })

  assert isinstance(
    model,
    HistGradientBoostingRegressor,
  )

  assert model.learning_rate == pytest.approx(
    0.1
  )

  assert model.max_iter == 100
  assert model.max_leaf_nodes == 31


def test_build_gradient_boosting_classifier_from_json_parameters():
  parameters = {
    "model_family":
      "gradient_boosting",
    "model_name":
      "gradient_boosting_classifier_tuned",
    "n_estimators":
      200,
    "learning_rate":
      0.05,
    "max_depth":
      2,
  }

  model = build_classification_model({
    "model_parameters":
      json.dumps(parameters),
  })

  assert isinstance(
    model,
    GradientBoostingClassifier,
  )

  assert model.n_estimators == 200
  assert model.learning_rate == pytest.approx(
    0.05
  )
  assert model.max_depth == 2


def test_invalid_classification_parameter_json_is_rejected():
  with pytest.raises(
    ValueError,
    match="valid JSON",
  ):
    parse_classification_parameters(
      "not-json"
    )


def test_unknown_classification_family_is_rejected():
  with pytest.raises(
    ValueError,
    match="Unsupported classification model family",
  ):
    build_classification_model({
      "model_parameters":
        json.dumps({
          "model_family":
            "unsupported",
        }),
    })

def test_regression_candidates_use_requested_artifact_directory(
  tmp_path,
  monkeypatch,
):
  import pandas as pd

  from electricity_predictor.modeling.live_contract import (
    train_live_candidate_models as trainer,
  )

  training_data = pd.DataFrame({
    column: [1.0, 2.0]
    for column in trainer.SELECTED_LIVE_FEATURE_COLUMNS
  })

  training_data[
    trainer.DATETIME_COLUMN
  ] = pd.to_datetime([
    "2026-01-01T00:00:00Z",
    "2026-01-01T01:00:00Z",
  ])

  training_data[
    "actual_price_target_1h"
  ] = [10.0, 11.0]

  results = pd.DataFrame([{
    "horizon_hours": 1,
    "validation_mae": 1.0,
    "validation_rmse": 2.0,
    "learning_rate": 0.1,
    "max_iter": 10,
    "max_leaf_nodes": 5,
    "min_samples_leaf": 2,
    "l2_regularization": 0.0,
  }])

  class FakeModel:
    def fit(self, features, target):
      return self

  saved_paths = []

  monkeypatch.setattr(
    trainer,
    "build_regression_model",
    lambda result: FakeModel(),
  )

  monkeypatch.setattr(
    trainer.joblib,
    "dump",
    lambda model, path: saved_paths.append(path),
  )

  monkeypatch.setattr(
    trainer,
    "calculate_sha256",
    lambda path: "test-sha256",
  )

  artifact_directory = (
    tmp_path
    / "candidate"
    / "regression"
  )

  metadata = trainer.train_regression_candidates(
    training_data=training_data,
    results=results,
    artifact_directory=artifact_directory,
  )

  expected_path = (
    artifact_directory
    / "live_regression_model_1h.joblib"
  )

  assert saved_paths == [expected_path]

  assert metadata[0][
    "artifact_path"
  ] == str(expected_path)


def test_classification_candidates_use_requested_artifact_directory(
  tmp_path,
  monkeypatch,
):
  import pandas as pd

  from electricity_predictor.modeling.live_contract import (
    train_live_candidate_models as trainer,
  )

  training_data = pd.DataFrame({
    column: [1.0, 2.0, 3.0, 4.0]
    for column in trainer.SELECTED_LIVE_FEATURE_COLUMNS
  })

  training_data[
    trainer.DATETIME_COLUMN
  ] = pd.to_datetime([
    "2026-01-01T00:00:00Z",
    "2026-01-01T01:00:00Z",
    "2026-01-01T02:00:00Z",
    "2026-01-01T03:00:00Z",
  ])

  training_data[
    "actual_price_target_1h"
  ] = [10.0, 100.0, 20.0, 120.0]

  results = pd.DataFrame([{
    "horizon_hours": 1,
    "model_name": "test_classifier",
    "model_family": "hist_gradient_boosting",
    "model_parameters": "{}",
    "spike_threshold": 50.0,
    "decision_threshold": 0.5,
    "validation_f1": 0.6,
    "validation_pr_auc": 0.7,
  }])

  class FakeModel:
    def fit(
      self,
      features,
      target,
      sample_weight=None,
    ):
      return self

  saved_paths = []

  monkeypatch.setattr(
    trainer,
    "build_classification_model",
    lambda result: FakeModel(),
  )

  monkeypatch.setattr(
    trainer,
    "compute_sample_weight",
    lambda class_weight, y: [1.0] * len(y),
  )

  monkeypatch.setattr(
    trainer.joblib,
    "dump",
    lambda model, path: saved_paths.append(path),
  )

  monkeypatch.setattr(
    trainer,
    "calculate_sha256",
    lambda path: "test-sha256",
  )

  artifact_directory = (
    tmp_path
    / "candidate"
    / "classification"
  )

  metadata = (
    trainer.train_classification_candidates(
      training_data=training_data,
      results=results,
      artifact_directory=artifact_directory,
    )
  )

  expected_path = (
    artifact_directory
    / "live_classification_model_1h.joblib"
  )

  assert saved_paths == [expected_path]

  assert metadata[0][
    "artifact_path"
  ] == str(expected_path)


def test_write_manifest_uses_requested_path(
  tmp_path,
):
  import json

  from electricity_predictor.modeling.live_contract import (
    train_live_candidate_models as trainer,
  )

  manifest_path = (
    tmp_path
    / "candidate"
    / "live_bundle_manifest.json"
  )

  manifest = trainer.write_manifest(
    regression_metadata=[],
    classification_metadata=[],
    manifest_path=manifest_path,
  )

  assert manifest_path.exists()

  written_manifest = json.loads(
    manifest_path.read_text(
      encoding="utf-8"
    )
  )

  assert written_manifest == manifest

  assert manifest[
    "active_registry_modified"
  ] is False

  assert manifest[
    "protected_test_used"
  ] is False
