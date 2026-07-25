from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import build_target_column_name
from electricity_predictor.modeling.model_results import (
  REGRESSION_VALIDATION_RESULTS_PATH,
  write_model_results,
)
from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  REGRESSION_BASELINE_CONFIGS,
  build_rule_baseline_result,
  evaluate_rule_baseline,
)
from electricity_predictor.modeling.regression.elastic_net.elastic_net_regression import (
  build_elastic_net_regression_result,
  evaluate_elastic_net_regression_model,
  train_elastic_net_regression_model,
)
from electricity_predictor.modeling.regression.elastic_net.elastic_net_tuning import (
  build_tuned_elastic_net_result,
  format_elastic_net_parameters,
  tune_elastic_net_config,
)
from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting import (
  HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
  HIST_GRADIENT_BOOSTING_LEARNING_RATE,
  HIST_GRADIENT_BOOSTING_LOSS,
  HIST_GRADIENT_BOOSTING_MAX_ITER,
  HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
  HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
  HIST_GRADIENT_BOOSTING_RANDOM_STATE,
  build_hist_gradient_boosting_result,
  evaluate_hist_gradient_boosting_model,
  train_hist_gradient_boosting_model,
)
from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting_tuning import (
  build_tuned_hist_gradient_boosting_result,
  format_hist_gradient_boosting_tuning_parameters,
  tune_hist_gradient_boosting_config,
)
from electricity_predictor.modeling.regression.lasso.lasso_regression import (
  build_lasso_regression_result,
  evaluate_lasso_regression_model,
  train_lasso_regression_model,
)
from electricity_predictor.modeling.regression.lasso.lasso_tuning import (
  build_tuned_lasso_result,
  tune_lasso_alpha,
)
from electricity_predictor.modeling.regression.linear.linear_regression import (
  build_linear_regression_result,
  evaluate_linear_regression_model,
  train_linear_regression_model,
)
from electricity_predictor.modeling.regression.random_forest.random_forest import (
  RANDOM_FOREST_MAX_DEPTH,
  RANDOM_FOREST_MIN_SAMPLES_LEAF,
  RANDOM_FOREST_N_ESTIMATORS,
  RANDOM_FOREST_RANDOM_STATE,
  build_random_forest_result,
  evaluate_random_forest_model,
  train_random_forest_model,
)
from electricity_predictor.modeling.regression.random_forest.random_forest_tuning import (
  build_tuned_random_forest_result,
  format_random_forest_parameters,
  tune_random_forest_config,
)
from electricity_predictor.modeling.regression.ridge.ridge_regression import (
  build_ridge_regression_result,
  evaluate_ridge_regression_model,
  train_ridge_regression_model,
)
from electricity_predictor.modeling.regression.ridge.ridge_tuning import (
  build_tuned_ridge_result,
  tune_ridge_alpha,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


def run_baseline_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Evaluate every simple regression benchmark for one horizon."""
  results = []

  for baseline_config in REGRESSION_BASELINE_CONFIGS:
    model_name = baseline_config["model_name"]
    prediction_column = baseline_config["prediction_column"]
    description = baseline_config["description"]

    print(
      "Evaluating regression baseline "
      f"{model_name} prediction_column={prediction_column} "
      "on validation split"
    )

    scores = evaluate_rule_baseline(
      data=validation_data,
      prediction_column=prediction_column,
      target_column=target_column,
    )

    results.append(
      build_rule_baseline_result(
        scores=scores,
        row_count=len(validation_data),
        model_name=model_name,
        prediction_column=prediction_column,
        description=description,
        split="validation",
        horizon_hours=horizon_hours,
      )
    )

  return results


def run_linear_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Train and evaluate the linear benchmark for one horizon."""
  print("Training Linear Regression fit_intercept=True on train split")
  model = train_linear_regression_model(
    train_data=train_data,
    target_column=target_column,
  )
  scores = evaluate_linear_regression_model(
    model=model,
    evaluation_data=validation_data,
    target_column=target_column,
  )

  return [
    build_linear_regression_result(
      scores=scores,
      row_count=len(validation_data),
      split="validation",
      horizon_hours=horizon_hours,
    )
  ]


def run_ridge_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Evaluate base and tuned Ridge designs for one horizon."""
  print("Training Ridge Regression alpha=1.0 on train split")
  base_model = train_ridge_regression_model(
    train_data=train_data,
    target_column=target_column,
  )
  base_scores = evaluate_ridge_regression_model(
    model=base_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  base_result = build_ridge_regression_result(
    scores=base_scores,
    row_count=len(validation_data),
    split="validation",
    horizon_hours=horizon_hours,
  )

  print("Tuning Ridge Regression with TimeSeriesSplit on train split")
  tuning_result = tune_ridge_alpha(
    train_data=train_data,
    target_column=target_column,
  )
  best_alpha = tuning_result["alpha"]
  tuned_model = train_ridge_regression_model(
    train_data=train_data,
    alpha=best_alpha,
    target_column=target_column,
  )
  tuned_scores = evaluate_ridge_regression_model(
    model=tuned_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  tuned_result = build_tuned_ridge_result(
    scores=tuned_scores,
    row_count=len(validation_data),
    split="validation",
    best_alpha=best_alpha,
    cv_mae=tuning_result["cv_mae"],
    cv_rmse=tuning_result["cv_rmse"],
    horizon_hours=horizon_hours,
  )

  return [base_result, tuned_result]


def run_lasso_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Evaluate base and tuned Lasso designs for one horizon."""
  print("Training Lasso Regression alpha=1.0 on train split")
  base_model = train_lasso_regression_model(
    train_data=train_data,
    target_column=target_column,
  )
  base_scores = evaluate_lasso_regression_model(
    model=base_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  base_result = build_lasso_regression_result(
    scores=base_scores,
    row_count=len(validation_data),
    split="validation",
    horizon_hours=horizon_hours,
  )

  print("Tuning Lasso Regression with TimeSeriesSplit on train split")
  tuning_result = tune_lasso_alpha(
    train_data=train_data,
    target_column=target_column,
  )
  best_alpha = tuning_result["alpha"]
  tuned_model = train_lasso_regression_model(
    train_data=train_data,
    alpha=best_alpha,
    target_column=target_column,
  )
  tuned_scores = evaluate_lasso_regression_model(
    model=tuned_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  tuned_result = build_tuned_lasso_result(
    scores=tuned_scores,
    row_count=len(validation_data),
    split="validation",
    best_alpha=best_alpha,
    cv_mae=tuning_result["cv_mae"],
    cv_rmse=tuning_result["cv_rmse"],
    horizon_hours=horizon_hours,
  )

  return [base_result, tuned_result]


def run_elastic_net_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Evaluate base and tuned Elastic Net designs for one horizon."""
  print("Training Elastic Net Regression alpha=1.0 l1_ratio=0.5 on train split")
  base_model = train_elastic_net_regression_model(
    train_data=train_data,
    target_column=target_column,
  )
  base_scores = evaluate_elastic_net_regression_model(
    model=base_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  base_result = build_elastic_net_regression_result(
    scores=base_scores,
    row_count=len(validation_data),
    split="validation",
    horizon_hours=horizon_hours,
  )

  print("Tuning Elastic Net Regression with TimeSeriesSplit on train split")
  tuning_result = tune_elastic_net_config(
    train_data=train_data,
    target_column=target_column,
  )
  best_config = tuning_result["config"]

  print(f"Training tuned Elastic Net {format_elastic_net_parameters(best_config)} on train split")
  tuned_model = train_elastic_net_regression_model(
    train_data=train_data,
    alpha=best_config["alpha"],
    l1_ratio=best_config["l1_ratio"],
    target_column=target_column,
  )
  tuned_scores = evaluate_elastic_net_regression_model(
    model=tuned_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  tuned_result = build_tuned_elastic_net_result(
    scores=tuned_scores,
    row_count=len(validation_data),
    split="validation",
    best_config=best_config,
    cv_mae=tuning_result["cv_mae"],
    cv_rmse=tuning_result["cv_rmse"],
    horizon_hours=horizon_hours,
  )

  return [base_result, tuned_result]


def run_random_forest_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Evaluate base and tuned Random Forest designs for one horizon."""
  print("Training Random Forest base configuration on train split")
  base_model = train_random_forest_model(
    train_data=train_data,
    n_estimators=RANDOM_FOREST_N_ESTIMATORS,
    max_depth=RANDOM_FOREST_MAX_DEPTH,
    min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
    random_state=RANDOM_FOREST_RANDOM_STATE,
    target_column=target_column,
  )
  base_scores = evaluate_random_forest_model(
    model=base_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  base_result = build_random_forest_result(
    scores=base_scores,
    row_count=len(validation_data),
    split="validation",
    n_estimators=RANDOM_FOREST_N_ESTIMATORS,
    max_depth=RANDOM_FOREST_MAX_DEPTH,
    min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
    random_state=RANDOM_FOREST_RANDOM_STATE,
    horizon_hours=horizon_hours,
  )

  print("Tuning Random Forest with TimeSeriesSplit on train split")
  tuning_result = tune_random_forest_config(
    train_data=train_data,
    target_column=target_column,
  )
  best_config = tuning_result["config"]

  print(
    "Training tuned Random Forest "
    f"{format_random_forest_parameters(best_config, RANDOM_FOREST_RANDOM_STATE)} "
    "on train split"
  )
  tuned_model = train_random_forest_model(
    train_data=train_data,
    n_estimators=best_config["n_estimators"],
    max_depth=best_config["max_depth"],
    min_samples_leaf=best_config["min_samples_leaf"],
    random_state=RANDOM_FOREST_RANDOM_STATE,
    target_column=target_column,
  )
  tuned_scores = evaluate_random_forest_model(
    model=tuned_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  tuned_result = build_tuned_random_forest_result(
    scores=tuned_scores,
    row_count=len(validation_data),
    split="validation",
    best_config=best_config,
    cv_mae=tuning_result["cv_mae"],
    cv_rmse=tuning_result["cv_rmse"],
    horizon_hours=horizon_hours,
  )

  return [base_result, tuned_result]


def run_hist_gradient_boosting_family(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
  horizon_hours: int,
) -> list[dict]:
  """Evaluate base and tuned HistGradientBoosting designs for one horizon."""
  print(
    "Training HistGradientBoosting base configuration "
    "on train split"
  )
  base_model = train_hist_gradient_boosting_model(
    train_data=train_data,
    loss=HIST_GRADIENT_BOOSTING_LOSS,
    learning_rate=HIST_GRADIENT_BOOSTING_LEARNING_RATE,
    max_iter=HIST_GRADIENT_BOOSTING_MAX_ITER,
    max_leaf_nodes=HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
    min_samples_leaf=HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
    l2_regularization=HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
    early_stopping=HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
    random_state=HIST_GRADIENT_BOOSTING_RANDOM_STATE,
    target_column=target_column,
  )
  base_scores = evaluate_hist_gradient_boosting_model(
    model=base_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  base_result = build_hist_gradient_boosting_result(
    scores=base_scores,
    row_count=len(validation_data),
    split="validation",
    loss=HIST_GRADIENT_BOOSTING_LOSS,
    learning_rate=HIST_GRADIENT_BOOSTING_LEARNING_RATE,
    max_iter=HIST_GRADIENT_BOOSTING_MAX_ITER,
    max_leaf_nodes=HIST_GRADIENT_BOOSTING_MAX_LEAF_NODES,
    min_samples_leaf=HIST_GRADIENT_BOOSTING_MIN_SAMPLES_LEAF,
    l2_regularization=HIST_GRADIENT_BOOSTING_L2_REGULARIZATION,
    early_stopping=HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
    random_state=HIST_GRADIENT_BOOSTING_RANDOM_STATE,
    horizon_hours=horizon_hours,
  )

  print(
    "Tuning HistGradientBoosting with TimeSeriesSplit "
    "on train split"
  )
  tuning_result = tune_hist_gradient_boosting_config(
    train_data=train_data,
    target_column=target_column,
  )
  best_config = tuning_result["config"]

  print(
    "Training tuned HistGradientBoosting "
    f"{format_hist_gradient_boosting_tuning_parameters(best_config)} "
    "on train split"
  )
  tuned_model = train_hist_gradient_boosting_model(
    train_data=train_data,
    loss=HIST_GRADIENT_BOOSTING_LOSS,
    learning_rate=best_config["learning_rate"],
    max_iter=best_config["max_iter"],
    max_leaf_nodes=best_config["max_leaf_nodes"],
    min_samples_leaf=best_config["min_samples_leaf"],
    l2_regularization=best_config["l2_regularization"],
    early_stopping=HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
    random_state=HIST_GRADIENT_BOOSTING_RANDOM_STATE,
    target_column=target_column,
  )
  tuned_scores = evaluate_hist_gradient_boosting_model(
    model=tuned_model,
    evaluation_data=validation_data,
    target_column=target_column,
  )
  tuned_result = build_tuned_hist_gradient_boosting_result(
    scores=tuned_scores,
    row_count=len(validation_data),
    split="validation",
    best_config=best_config,
    cv_mae=tuning_result["cv_mae"],
    cv_rmse=tuning_result["cv_rmse"],
    horizon_hours=horizon_hours,
  )

  return [base_result, tuned_result]


# Order is part of the comparison contract and therefore remains explicit.
REGRESSION_FAMILY_RUNNERS = (
  run_baseline_family,
  run_linear_family,
  run_ridge_family,
  run_lasso_family,
  run_elastic_net_family,
  run_random_forest_family,
  run_hist_gradient_boosting_family,
)


def run_regression_models() -> Path:
  """Train, tune, evaluate, and summarize regression models for each horizon."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]
  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
  )

  results = []

  for horizon_hours in horizons_hours:
    target_column = build_target_column_name(horizon_hours)

    print("")
    print(f"Regression horizon: {horizon_hours}h")
    print("=" * 32)
    print(f"Target column: {target_column}")

    for run_family in REGRESSION_FAMILY_RUNNERS:
      results.extend(
        run_family(
          train_data=train_data,
          validation_data=validation_data,
          target_column=target_column,
          horizon_hours=horizon_hours,
        )
      )

  return write_model_results(
    results=results,
    output_path=REGRESSION_VALIDATION_RESULTS_PATH,
  )


if __name__ == "__main__":
  written_results_path = run_regression_models()

  print("")
  print("Regression models completed")
  print("===========================")
  print(f"Results written to: {written_results_path}")
