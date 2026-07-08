from pathlib import Path

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.model_results import write_model_results
from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  build_naive_baseline_result,
  evaluate_naive_baseline,
  load_training_dataset,
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
from electricity_predictor.modeling.split import split_time_series_data


def run_regression_models() -> Path:
  """Train, tune, evaluate, and summarize the current regression model set."""
  configuration = load_configuration()

  training_dataset_path = Path("data/processed/training_dataset.csv")
  results_path = Path("reports/model_results.csv")
  modeling_config = configuration["modeling"]

  # Load the clean training dataset created by the feature pipeline.
  training_data = load_training_dataset(training_dataset_path)

  # Keep the chronological split stable to avoid future-to-past leakage.
  train_data, validation_data, test_data = split_time_series_data(
    data=training_data,
    train_ratio=modeling_config["train_ratio"],
    validation_ratio=modeling_config["validation_ratio"],
    test_ratio=modeling_config["test_ratio"],
  )

  # Results are collected in memory first, then written once to avoid duplicate rows.
  results = []

  # Baseline uses the protected test split because it is the benchmark future models must beat.
  print("Evaluating Naive Baseline prediction_column=actual_price_lag_1h on test split")
  baseline_scores = evaluate_naive_baseline(test_data)
  results.append(
    build_naive_baseline_result(
      scores=baseline_scores,
      row_count=len(test_data),
    )
  )

  # Linear Regression is the simplest learned model and gives a clean linear benchmark.
  print("Training Linear Regression fit_intercept=True on train split")
  linear_regression_model = train_linear_regression_model(train_data)
  linear_regression_scores = evaluate_linear_regression_model(
    model=linear_regression_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_linear_regression_result(
      scores=linear_regression_scores,
      row_count=len(validation_data),
      split="validation",
    )
  )

  # Base Ridge shows how the default regularized linear model performs before tuning.
  print("Training Ridge Regression alpha=1.0 on train split")
  ridge_model = train_ridge_regression_model(train_data)
  ridge_scores = evaluate_ridge_regression_model(
    model=ridge_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_ridge_regression_result(
      scores=ridge_scores,
      row_count=len(validation_data),
      split="validation",
    )
  )

  # Tuned Ridge selects alpha with TimeSeriesSplit inside train_data only.
  print("Tuning Ridge Regression with TimeSeriesSplit on train split")
  best_ridge_result = tune_ridge_alpha(train_data)
  best_alpha = best_ridge_result["alpha"]
  tuned_ridge_model = train_ridge_regression_model(
    train_data=train_data,
    alpha=best_alpha,
  )
  tuned_ridge_scores = evaluate_ridge_regression_model(
    model=tuned_ridge_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_tuned_ridge_result(
      scores=tuned_ridge_scores,
      row_count=len(validation_data),
      split="validation",
      best_alpha=best_alpha,
      cv_mae=best_ridge_result["cv_mae"],
      cv_rmse=best_ridge_result["cv_rmse"],
    )
  )

  # Base Lasso shows whether feature-selection regularization helps before tuning.
  print("Training Lasso Regression alpha=1.0 on train split")
  lasso_model = train_lasso_regression_model(train_data)
  lasso_scores = evaluate_lasso_regression_model(
    model=lasso_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_lasso_regression_result(
      scores=lasso_scores,
      row_count=len(validation_data),
      split="validation",
    )
  )

  # Tuned Lasso searches alpha values using chronological cross-validation.
  print("Tuning Lasso Regression with TimeSeriesSplit on train split")
  best_lasso_result = tune_lasso_alpha(train_data)
  best_lasso_alpha = best_lasso_result["alpha"]
  tuned_lasso_model = train_lasso_regression_model(
    train_data=train_data,
    alpha=best_lasso_alpha,
  )
  tuned_lasso_scores = evaluate_lasso_regression_model(
    model=tuned_lasso_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_tuned_lasso_result(
      scores=tuned_lasso_scores,
      row_count=len(validation_data),
      split="validation",
      best_alpha=best_lasso_alpha,
      cv_mae=best_lasso_result["cv_mae"],
      cv_rmse=best_lasso_result["cv_rmse"],
    )
  )

  # Base Elastic Net combines Ridge-style shrinkage with Lasso-style feature selection.
  print("Training Elastic Net Regression alpha=1.0 l1_ratio=0.5 on train split")
  elastic_net_model = train_elastic_net_regression_model(train_data)
  elastic_net_scores = evaluate_elastic_net_regression_model(
    model=elastic_net_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_elastic_net_regression_result(
      scores=elastic_net_scores,
      row_count=len(validation_data),
      split="validation",
    )
  )

  # Tuned Elastic Net searches both alpha and l1_ratio inside the train split.
  print("Tuning Elastic Net Regression with TimeSeriesSplit on train split")
  best_elastic_net_result = tune_elastic_net_config(train_data)
  best_elastic_net_config = best_elastic_net_result["config"]

  print(f"Training tuned Elastic Net {format_elastic_net_parameters(best_elastic_net_config)} on train split")
  tuned_elastic_net_model = train_elastic_net_regression_model(
    train_data=train_data,
    alpha=best_elastic_net_config["alpha"],
    l1_ratio=best_elastic_net_config["l1_ratio"],
  )
  tuned_elastic_net_scores = evaluate_elastic_net_regression_model(
    model=tuned_elastic_net_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_tuned_elastic_net_result(
      scores=tuned_elastic_net_scores,
      row_count=len(validation_data),
      split="validation",
      best_config=best_elastic_net_config,
      cv_mae=best_elastic_net_result["cv_mae"],
      cv_rmse=best_elastic_net_result["cv_rmse"],
    )
  )

  # Base Random Forest checks a simple non-linear model before tuning tree complexity.
  print("Training Random Forest base configuration on train split")
  random_forest_model = train_random_forest_model(
    train_data=train_data,
    n_estimators=RANDOM_FOREST_N_ESTIMATORS,
    max_depth=RANDOM_FOREST_MAX_DEPTH,
    min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
    random_state=RANDOM_FOREST_RANDOM_STATE,
  )
  random_forest_scores = evaluate_random_forest_model(
    model=random_forest_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_random_forest_result(
      scores=random_forest_scores,
      row_count=len(validation_data),
      split="validation",
      n_estimators=RANDOM_FOREST_N_ESTIMATORS,
      max_depth=RANDOM_FOREST_MAX_DEPTH,
      min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
      random_state=RANDOM_FOREST_RANDOM_STATE,
    )
  )

  # Tuned Random Forest searches tree settings with TimeSeriesSplit inside train_data only.
  print("Tuning Random Forest with TimeSeriesSplit on train split")
  best_random_forest_result = tune_random_forest_config(train_data)
  best_random_forest_config = best_random_forest_result["config"]

  print(
    "Training tuned Random Forest "
    f"{format_random_forest_parameters(best_random_forest_config, RANDOM_FOREST_RANDOM_STATE)} "
    "on train split"
  )
  tuned_random_forest_model = train_random_forest_model(
    train_data=train_data,
    n_estimators=best_random_forest_config["n_estimators"],
    max_depth=best_random_forest_config["max_depth"],
    min_samples_leaf=best_random_forest_config["min_samples_leaf"],
    random_state=RANDOM_FOREST_RANDOM_STATE,
  )
  tuned_random_forest_scores = evaluate_random_forest_model(
    model=tuned_random_forest_model,
    evaluation_data=validation_data,
  )
  results.append(
    build_tuned_random_forest_result(
      scores=tuned_random_forest_scores,
      row_count=len(validation_data),
      split="validation",
      best_config=best_random_forest_config,
      cv_mae=best_random_forest_result["cv_mae"],
      cv_rmse=best_random_forest_result["cv_rmse"],
    )
  )

  # Rewrite the summary from the current run so reports/model_results.csv stays clean.
  return write_model_results(
    results=results,
    output_path=results_path,
  )


if __name__ == "__main__":
  written_results_path = run_regression_models()

  print("Regression models completed")
  print("===========================")
  print(f"Results written to: {written_results_path}")
