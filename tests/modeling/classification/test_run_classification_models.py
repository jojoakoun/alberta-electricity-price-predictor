from importlib import import_module
from inspect import signature
from pathlib import Path
from unittest.mock import Mock, call

from electricity_predictor.modeling.classification import run_classification_models as workflow
from electricity_predictor.modeling.model_results import (
  CLASSIFICATION_VALIDATION_RESULTS_PATH,
)


CLASSIFICATION_RUNNERS = (
  (
    "electricity_predictor.modeling.classification.baseline.naive_spike_baseline",
    "run_classification_baseline",
  ),
  (
    "electricity_predictor.modeling.classification.logistic.logistic_regression",
    "run_logistic_regression",
  ),
  (
    "electricity_predictor.modeling.classification.logistic.logistic_tuning",
    "run_tuned_logistic_regression",
  ),
  (
    "electricity_predictor.modeling.classification.random_forest.random_forest_classifier",
    "run_random_forest_classifier",
  ),
  (
    "electricity_predictor.modeling.classification.random_forest.random_forest_tuning",
    "run_tuned_random_forest",
  ),
  (
    "electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_classifier",
    "run_gradient_boosting_classifier",
  ),
  (
    "electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_tuning",
    "run_tuned_gradient_boosting",
  ),
)


def test_classification_workflow_resets_its_own_report_and_preserves_order(
  monkeypatch,
) -> None:
  reset_results = Mock()
  monkeypatch.setattr(workflow, "write_model_results", reset_results)

  ordered_calls = Mock()
  runner_names = [
    "run_classification_baseline",
    "run_logistic_regression",
    "run_tuned_logistic_regression",
    "run_random_forest_classifier",
    "run_tuned_random_forest",
    "run_gradient_boosting_classifier",
    "run_tuned_gradient_boosting",
  ]
  for runner_name in runner_names:
    monkeypatch.setattr(
      workflow,
      runner_name,
      Mock(
        side_effect=lambda runner_name=runner_name, **kwargs: ordered_calls(
          runner_name,
          **kwargs,
        )
      ),
    )

  result = workflow.run_classification_models(
    training_dataset_path=Path("training.csv"),
    results_path=Path("classification.csv"),
  )

  assert result == Path("classification.csv")
  reset_results.assert_called_once_with(
    results=[],
    output_path=Path("classification.csv"),
  )
  assert ordered_calls.call_args_list == [
    call(
      runner_name,
      training_dataset_path=Path("training.csv"),
      results_path=Path("classification.csv"),
    )
    for runner_name in runner_names
  ]


def test_all_classification_family_defaults_use_classification_report() -> None:
  for module_name, runner_name in CLASSIFICATION_RUNNERS:
    runner = getattr(import_module(module_name), runner_name)

    assert (
      signature(runner).parameters["results_path"].default
      == CLASSIFICATION_VALIDATION_RESULTS_PATH
    )


def test_classification_orchestrator_default_uses_classification_report() -> None:
  assert (
    signature(workflow.run_classification_models)
    .parameters["results_path"]
    .default
    == CLASSIFICATION_VALIDATION_RESULTS_PATH
  )
