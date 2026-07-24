"""Tests for the isolated live candidate model bundle."""

import json
from pathlib import Path

import pytest
from sklearn.ensemble import (
  GradientBoostingClassifier,
  HistGradientBoostingRegressor,
)

from electricity_predictor.modeling.live_contract.save_candidate_models import (
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
