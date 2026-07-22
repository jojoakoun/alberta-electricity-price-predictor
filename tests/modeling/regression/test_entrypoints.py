from importlib import import_module
from pathlib import Path
import re
from unittest.mock import Mock, sentinel

import pytest

from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH as SHARED_TRAINING_DATASET_PATH,
)
from electricity_predictor.modeling.model_results import (
  REGRESSION_VALIDATION_RESULTS_PATH,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MAKEFILE_PATH = PROJECT_ROOT / "Makefile"

ENTRYPOINT_CASES = (
  {
    "module": (
      "electricity_predictor.modeling.regression.linear."
      "linear_regression"
    ),
    "train": "train_linear_regression_model",
    "evaluate": "evaluate_linear_regression_model",
    "build_result": "build_linear_regression_result",
    "summary": "print_linear_regression_summary",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.ridge."
      "ridge_regression"
    ),
    "train": "train_ridge_regression_model",
    "evaluate": "evaluate_ridge_regression_model",
    "build_result": "build_ridge_regression_result",
    "summary": "print_ridge_regression_summary",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.ridge."
      "ridge_tuning"
    ),
    "tune": "tune_ridge_alpha",
    "tuning_result": {
      "alpha": 1.0,
      "cv_mae": 10.0,
      "cv_rmse": 20.0,
    },
    "train": "train_ridge_regression_model",
    "evaluate": "evaluate_ridge_regression_model",
    "build_result": "build_tuned_ridge_result",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.lasso."
      "lasso_regression"
    ),
    "train": "train_lasso_regression_model",
    "evaluate": "evaluate_lasso_regression_model",
    "build_result": "build_lasso_regression_result",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.lasso."
      "lasso_tuning"
    ),
    "tune": "tune_lasso_alpha",
    "tuning_result": {
      "alpha": 0.1,
      "cv_mae": 10.0,
      "cv_rmse": 20.0,
    },
    "train": "train_lasso_regression_model",
    "evaluate": "evaluate_lasso_regression_model",
    "build_result": "build_tuned_lasso_result",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.elastic_net."
      "elastic_net_regression"
    ),
    "train": "train_elastic_net_regression_model",
    "evaluate": "evaluate_elastic_net_regression_model",
    "build_result": "build_elastic_net_regression_result",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.elastic_net."
      "elastic_net_tuning"
    ),
    "tune": "tune_elastic_net_config",
    "tuning_result": {
      "config": {
        "alpha": 0.1,
        "l1_ratio": 0.5,
      },
      "cv_mae": 10.0,
      "cv_rmse": 20.0,
    },
    "train": "train_elastic_net_regression_model",
    "evaluate": "evaluate_elastic_net_regression_model",
    "build_result": "build_tuned_elastic_net_result",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.random_forest."
      "random_forest"
    ),
    "train": "train_random_forest_model",
    "evaluate": "evaluate_random_forest_model",
    "build_result": "build_random_forest_result",
    "summary": "print_random_forest_summary",
  },
  {
    "module": (
      "electricity_predictor.modeling.regression.random_forest."
      "random_forest_tuning"
    ),
    "tune": "tune_random_forest_config",
    "tuning_result": {
      "config": {
        "n_estimators": 100,
        "max_depth": 20,
        "min_samples_leaf": 5,
      },
      "cv_mae": 10.0,
      "cv_rmse": 20.0,
    },
    "train": "train_random_forest_model",
    "evaluate": "evaluate_random_forest_model",
    "build_result": "build_tuned_random_forest_result",
  },
)

MAKE_TARGETS = {
  "linear-regression": (
    "electricity_predictor.modeling.regression.linear."
    "linear_regression"
  ),
  "ridge-regression": (
    "electricity_predictor.modeling.regression.ridge."
    "ridge_regression"
  ),
  "lasso-regression": (
    "electricity_predictor.modeling.regression.lasso."
    "lasso_regression"
  ),
  "lasso-tuning": (
    "electricity_predictor.modeling.regression.lasso."
    "lasso_tuning"
  ),
  "elastic-net-regression": (
    "electricity_predictor.modeling.regression.elastic_net."
    "elastic_net_regression"
  ),
  "elastic-net-tuning": (
    "electricity_predictor.modeling.regression.elastic_net."
    "elastic_net_tuning"
  ),
}


def extract_make_target(
  makefile: str,
  target_name: str,
) -> str:
  """Return one Makefile target body."""
  pattern = re.compile(
    rf"(?ms)^{re.escape(target_name)}:\n"
    rf"(?P<body>.*?)"
    rf"(?=^[A-Za-z0-9_.-]+:|\Z)"
  )
  match = pattern.search(makefile)

  if match is None:
    raise AssertionError(f"Missing Makefile target: {target_name}")

  return match.group("body")


@pytest.mark.parametrize(
  "entrypoint_case",
  ENTRYPOINT_CASES,
  ids=lambda case: case["module"].rsplit(".", maxsplit=1)[-1],
)
def test_regression_module_exposes_explicit_main(entrypoint_case: dict) -> None:
  module = import_module(entrypoint_case["module"])

  assert callable(module.main)
  assert module.TRAINING_DATASET_PATH is SHARED_TRAINING_DATASET_PATH


@pytest.mark.parametrize(
  "entrypoint_case",
  ENTRYPOINT_CASES,
  ids=lambda case: case["module"].rsplit(".", maxsplit=1)[-1],
)
def test_main_forwards_shared_training_path_without_fitting(
  entrypoint_case: dict,
  monkeypatch: pytest.MonkeyPatch,
) -> None:
  module = import_module(entrypoint_case["module"])
  modeling_config = {"test": "modeling-config"}
  validation_data = [sentinel.validation_row]

  load_configuration = Mock(
    return_value={"modeling": modeling_config}
  )
  load_training_dataset = Mock(
    return_value=sentinel.training_data
  )
  split_time_series_data = Mock(
    return_value=(
      sentinel.train_data,
      validation_data,
      sentinel.test_data,
    )
  )
  train_model = Mock(return_value=sentinel.model)
  evaluate_model = Mock(
    return_value={
      "mae": 1.0,
      "rmse": 2.0,
    }
  )
  build_result = Mock(return_value=sentinel.result)
  append_model_result = Mock(
    return_value=REGRESSION_VALIDATION_RESULTS_PATH
  )

  monkeypatch.setattr(
    module,
    "load_configuration",
    load_configuration,
  )
  monkeypatch.setattr(
    module,
    "load_training_dataset",
    load_training_dataset,
  )
  monkeypatch.setattr(
    module,
    "split_time_series_data_from_config",
    split_time_series_data,
  )
  monkeypatch.setattr(
    module,
    entrypoint_case["train"],
    train_model,
  )
  monkeypatch.setattr(
    module,
    entrypoint_case["evaluate"],
    evaluate_model,
  )
  monkeypatch.setattr(
    module,
    entrypoint_case["build_result"],
    build_result,
  )
  monkeypatch.setattr(
    module,
    "append_model_result",
    append_model_result,
  )

  summary_function = entrypoint_case.get("summary")

  if summary_function is not None:
    monkeypatch.setattr(
      module,
      summary_function,
      Mock(),
    )

  tuning_function = entrypoint_case.get("tune")

  if tuning_function is not None:
    tune_model = Mock(
      return_value=entrypoint_case["tuning_result"]
    )
    monkeypatch.setattr(
      module,
      tuning_function,
      tune_model,
    )
  else:
    tune_model = None

  result = module.main()

  assert result is None
  load_training_dataset.assert_called_once_with(
    SHARED_TRAINING_DATASET_PATH
  )
  split_time_series_data.assert_called_once_with(
    data=sentinel.training_data,
    modeling_config=modeling_config,
  )

  if tune_model is not None:
    tune_model.assert_called_once_with(sentinel.train_data)

  assert train_model.call_count == 1
  assert evaluate_model.call_count == 1
  build_result.assert_called_once()
  append_model_result.assert_called_once_with(
    result=sentinel.result,
    output_path=REGRESSION_VALIDATION_RESULTS_PATH,
  )


@pytest.mark.parametrize(
  ("target_name", "module_path"),
  MAKE_TARGETS.items(),
)
def test_makefile_regression_target_uses_module_entrypoint(
  target_name: str,
  module_path: str,
) -> None:
  makefile = MAKEFILE_PATH.read_text(encoding="utf-8")
  target = extract_make_target(
    makefile=makefile,
    target_name=target_name,
  )

  assert f"$(PYTHON) -m {module_path}" in target
  assert "src/electricity_predictor/modeling/regression/" not in target
