from pathlib import Path
from unittest.mock import Mock, call, sentinel

from electricity_predictor.modeling.model_results import (
  REGRESSION_VALIDATION_RESULTS_PATH,
)
from electricity_predictor.modeling.regression import run_regression_models as workflow
from electricity_predictor.modeling.regression.elastic_net import (
  elastic_net_tuning,
)
from electricity_predictor.modeling.regression.lasso import lasso_tuning
from electricity_predictor.modeling.regression.random_forest import (
  random_forest_tuning,
)
from electricity_predictor.modeling.regression.ridge import ridge_tuning


def test_family_runner_order_is_explicit() -> None:
  assert [runner.__name__ for runner in workflow.REGRESSION_FAMILY_RUNNERS] == [
    "run_baseline_family",
    "run_linear_family",
    "run_ridge_family",
    "run_lasso_family",
    "run_elastic_net_family",
    "run_random_forest_family",
  ]


def test_existing_tuning_search_spaces_remain_unchanged() -> None:
  assert ridge_tuning.RIDGE_ALPHAS == [0.1, 1.0, 10.0, 100.0]
  assert lasso_tuning.LASSO_ALPHAS == [0.001, 0.01, 0.1, 1.0, 10.0]
  assert elastic_net_tuning.ELASTIC_NET_CONFIGS == [
    {"alpha": 0.001, "l1_ratio": 0.2},
    {"alpha": 0.001, "l1_ratio": 0.5},
    {"alpha": 0.001, "l1_ratio": 0.8},
    {"alpha": 0.01, "l1_ratio": 0.2},
    {"alpha": 0.01, "l1_ratio": 0.5},
    {"alpha": 0.01, "l1_ratio": 0.8},
    {"alpha": 0.1, "l1_ratio": 0.2},
    {"alpha": 0.1, "l1_ratio": 0.5},
    {"alpha": 0.1, "l1_ratio": 0.8},
    {"alpha": 1.0, "l1_ratio": 0.5},
  ]
  assert random_forest_tuning.RANDOM_FOREST_CONFIGS == [
    {"n_estimators": 100, "max_depth": None, "min_samples_leaf": 1},
    {"n_estimators": 100, "max_depth": 10, "min_samples_leaf": 1},
    {"n_estimators": 100, "max_depth": 20, "min_samples_leaf": 1},
    {"n_estimators": 100, "max_depth": 20, "min_samples_leaf": 5},
    {"n_estimators": 200, "max_depth": 20, "min_samples_leaf": 5},
  ]


def test_orchestrator_preserves_horizon_and_family_order_without_training(
  monkeypatch,
) -> None:
  modeling_config = {"horizons_hours": [1, 3]}
  family_calls = []
  family_runners = []

  for family_name in ["baseline", "linear", "ridge"]:
    def run_family(*, family_name=family_name, **kwargs):
      family_calls.append((family_name, kwargs))
      return [f"{family_name}-{kwargs['horizon_hours']}"]

    family_runners.append(run_family)

  monkeypatch.setattr(
    workflow,
    "load_configuration",
    Mock(return_value={"modeling": modeling_config}),
  )
  monkeypatch.setattr(
    workflow,
    "load_training_dataset",
    Mock(return_value=sentinel.training_data),
  )
  monkeypatch.setattr(
    workflow,
    "split_time_series_data_from_config",
    Mock(
      return_value=(
        sentinel.train_data,
        sentinel.validation_data,
        sentinel.test_data,
      )
    ),
  )
  monkeypatch.setattr(
    workflow,
    "REGRESSION_FAMILY_RUNNERS",
    tuple(family_runners),
  )
  write_results = Mock(return_value=Path("written.csv"))
  monkeypatch.setattr(workflow, "write_model_results", write_results)

  assert workflow.run_regression_models() == Path("written.csv")
  assert [name for name, _ in family_calls] == [
    "baseline",
    "linear",
    "ridge",
    "baseline",
    "linear",
    "ridge",
  ]
  assert [arguments["target_column"] for _, arguments in family_calls] == [
    "actual_price_target_1h",
    "actual_price_target_1h",
    "actual_price_target_1h",
    "actual_price_target_3h",
    "actual_price_target_3h",
    "actual_price_target_3h",
  ]
  assert all(
    arguments["train_data"] is sentinel.train_data
    and arguments["validation_data"] is sentinel.validation_data
    for _, arguments in family_calls
  )
  write_results.assert_called_once_with(
    results=[
      "baseline-1",
      "linear-1",
      "ridge-1",
      "baseline-3",
      "linear-3",
      "ridge-3",
    ],
    output_path=REGRESSION_VALIDATION_RESULTS_PATH,
  )


def test_baseline_and_linear_runners_preserve_result_contract(monkeypatch) -> None:
  baseline_evaluate = Mock(return_value=sentinel.baseline_scores)
  baseline_build = Mock(return_value=sentinel.baseline_result)
  linear_train = Mock(return_value=sentinel.linear_model)
  linear_evaluate = Mock(return_value=sentinel.linear_scores)
  linear_build = Mock(return_value=sentinel.linear_result)

  monkeypatch.setattr(workflow, "evaluate_naive_baseline", baseline_evaluate)
  monkeypatch.setattr(workflow, "build_naive_baseline_result", baseline_build)
  monkeypatch.setattr(workflow, "train_linear_regression_model", linear_train)
  monkeypatch.setattr(workflow, "evaluate_linear_regression_model", linear_evaluate)
  monkeypatch.setattr(workflow, "build_linear_regression_result", linear_build)

  assert workflow.run_baseline_family(
    train_data=sentinel.train_data,
    validation_data=[sentinel.validation_row],
    target_column="target_6h",
    horizon_hours=6,
  ) == [sentinel.baseline_result]
  baseline_evaluate.assert_called_once_with(
    data=[sentinel.validation_row],
    target_column="target_6h",
  )
  baseline_build.assert_called_once_with(
    scores=sentinel.baseline_scores,
    row_count=1,
    split="validation",
    horizon_hours=6,
  )

  assert workflow.run_linear_family(
    train_data=sentinel.train_data,
    validation_data=[sentinel.validation_row],
    target_column="target_6h",
    horizon_hours=6,
  ) == [sentinel.linear_result]
  linear_train.assert_called_once_with(
    train_data=sentinel.train_data,
    target_column="target_6h",
  )
  linear_evaluate.assert_called_once_with(
    model=sentinel.linear_model,
    evaluation_data=[sentinel.validation_row],
    target_column="target_6h",
  )
  linear_build.assert_called_once_with(
    scores=sentinel.linear_scores,
    row_count=1,
    split="validation",
    horizon_hours=6,
  )


def test_ridge_runner_preserves_base_and_tuned_parameters(monkeypatch) -> None:
  train = Mock(side_effect=[sentinel.base_model, sentinel.tuned_model])
  evaluate = Mock(side_effect=[sentinel.base_scores, sentinel.tuned_scores])
  tune = Mock(return_value={"alpha": 10.0, "cv_mae": 2.5, "cv_rmse": 4.5})
  build_base = Mock(return_value=sentinel.base_result)
  build_tuned = Mock(return_value=sentinel.tuned_result)
  monkeypatch.setattr(workflow, "train_ridge_regression_model", train)
  monkeypatch.setattr(workflow, "evaluate_ridge_regression_model", evaluate)
  monkeypatch.setattr(workflow, "tune_ridge_alpha", tune)
  monkeypatch.setattr(workflow, "build_ridge_regression_result", build_base)
  monkeypatch.setattr(workflow, "build_tuned_ridge_result", build_tuned)

  results = workflow.run_ridge_family(
    train_data=sentinel.train_data,
    validation_data=[sentinel.validation_row],
    target_column="target_12h",
    horizon_hours=12,
  )

  assert results == [sentinel.base_result, sentinel.tuned_result]
  assert train.call_args_list == [
    call(train_data=sentinel.train_data, target_column="target_12h"),
    call(train_data=sentinel.train_data, alpha=10.0, target_column="target_12h"),
  ]
  tune.assert_called_once_with(
    train_data=sentinel.train_data,
    target_column="target_12h",
  )
  build_tuned.assert_called_once_with(
    scores=sentinel.tuned_scores,
    row_count=1,
    split="validation",
    best_alpha=10.0,
    cv_mae=2.5,
    cv_rmse=4.5,
    horizon_hours=12,
  )


def test_lasso_runner_preserves_base_and_tuned_parameters(monkeypatch) -> None:
  train = Mock(side_effect=[sentinel.base_model, sentinel.tuned_model])
  evaluate = Mock(side_effect=[sentinel.base_scores, sentinel.tuned_scores])
  tune = Mock(return_value={"alpha": 0.1, "cv_mae": 2.5, "cv_rmse": 4.5})
  monkeypatch.setattr(workflow, "train_lasso_regression_model", train)
  monkeypatch.setattr(workflow, "evaluate_lasso_regression_model", evaluate)
  monkeypatch.setattr(workflow, "tune_lasso_alpha", tune)
  monkeypatch.setattr(
    workflow,
    "build_lasso_regression_result",
    Mock(return_value=sentinel.base_result),
  )
  monkeypatch.setattr(
    workflow,
    "build_tuned_lasso_result",
    Mock(return_value=sentinel.tuned_result),
  )

  assert workflow.run_lasso_family(
    train_data=sentinel.train_data,
    validation_data=[sentinel.validation_row],
    target_column="target_3h",
    horizon_hours=3,
  ) == [sentinel.base_result, sentinel.tuned_result]
  assert train.call_args_list == [
    call(train_data=sentinel.train_data, target_column="target_3h"),
    call(train_data=sentinel.train_data, alpha=0.1, target_column="target_3h"),
  ]
  tune.assert_called_once_with(
    train_data=sentinel.train_data,
    target_column="target_3h",
  )


def test_elastic_net_runner_preserves_base_and_tuned_parameters(monkeypatch) -> None:
  train = Mock(side_effect=[sentinel.base_model, sentinel.tuned_model])
  evaluate = Mock(side_effect=[sentinel.base_scores, sentinel.tuned_scores])
  tune = Mock(
    return_value={
      "config": {"alpha": 0.01, "l1_ratio": 0.8},
      "cv_mae": 2.5,
      "cv_rmse": 4.5,
    }
  )
  monkeypatch.setattr(workflow, "train_elastic_net_regression_model", train)
  monkeypatch.setattr(workflow, "evaluate_elastic_net_regression_model", evaluate)
  monkeypatch.setattr(workflow, "tune_elastic_net_config", tune)
  monkeypatch.setattr(
    workflow,
    "format_elastic_net_parameters",
    Mock(return_value="alpha=0.01; l1_ratio=0.8; max_iter=10000"),
  )
  monkeypatch.setattr(
    workflow,
    "build_elastic_net_regression_result",
    Mock(return_value=sentinel.base_result),
  )
  monkeypatch.setattr(
    workflow,
    "build_tuned_elastic_net_result",
    Mock(return_value=sentinel.tuned_result),
  )

  assert workflow.run_elastic_net_family(
    train_data=sentinel.train_data,
    validation_data=[sentinel.validation_row],
    target_column="target_1h",
    horizon_hours=1,
  ) == [sentinel.base_result, sentinel.tuned_result]
  assert train.call_args_list == [
    call(train_data=sentinel.train_data, target_column="target_1h"),
    call(
      train_data=sentinel.train_data,
      alpha=0.01,
      l1_ratio=0.8,
      target_column="target_1h",
    ),
  ]


def test_random_forest_runner_preserves_base_and_tuned_parameters(monkeypatch) -> None:
  train = Mock(side_effect=[sentinel.base_model, sentinel.tuned_model])
  evaluate = Mock(side_effect=[sentinel.base_scores, sentinel.tuned_scores])
  tune = Mock(
    return_value={
      "config": {
        "n_estimators": 200,
        "max_depth": 20,
        "min_samples_leaf": 5,
      },
      "cv_mae": 2.5,
      "cv_rmse": 4.5,
    }
  )
  monkeypatch.setattr(workflow, "train_random_forest_model", train)
  monkeypatch.setattr(workflow, "evaluate_random_forest_model", evaluate)
  monkeypatch.setattr(workflow, "tune_random_forest_config", tune)
  monkeypatch.setattr(
    workflow,
    "format_random_forest_parameters",
    Mock(return_value="parameters"),
  )
  monkeypatch.setattr(
    workflow,
    "build_random_forest_result",
    Mock(return_value=sentinel.base_result),
  )
  monkeypatch.setattr(
    workflow,
    "build_tuned_random_forest_result",
    Mock(return_value=sentinel.tuned_result),
  )

  assert workflow.run_random_forest_family(
    train_data=sentinel.train_data,
    validation_data=[sentinel.validation_row],
    target_column="target_24h",
    horizon_hours=24,
  ) == [sentinel.base_result, sentinel.tuned_result]
  assert train.call_args_list == [
    call(
      train_data=sentinel.train_data,
      n_estimators=workflow.RANDOM_FOREST_N_ESTIMATORS,
      max_depth=workflow.RANDOM_FOREST_MAX_DEPTH,
      min_samples_leaf=workflow.RANDOM_FOREST_MIN_SAMPLES_LEAF,
      random_state=workflow.RANDOM_FOREST_RANDOM_STATE,
      target_column="target_24h",
    ),
    call(
      train_data=sentinel.train_data,
      n_estimators=200,
      max_depth=20,
      min_samples_leaf=5,
      random_state=workflow.RANDOM_FOREST_RANDOM_STATE,
      target_column="target_24h",
    ),
  ]
