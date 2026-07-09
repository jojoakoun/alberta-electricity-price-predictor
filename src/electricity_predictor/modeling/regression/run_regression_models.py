from pathlib import Path

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import build_target_column_name
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
  """Train, tune, evaluate, and summarize regression models for each horizon."""
  configuration = load_configuration()

  training_dataset_path = Path("data/processed/training_dataset.csv")
  results_path = Path("reports/model_results.csv")
  modeling_config = configuration["modeling"]

  # Horizons define how far into the future each model is trying to predict.
  # Example: horizon 3 means the target is actual_price_target_3h.
  horizons_hours = modeling_config["horizons_hours"]

  # This dataset is produced after feature engineering and training-data cleaning.
  # At this stage, rows with missing lags, rolling features, or horizon targets
  # have already been removed.
  training_data = load_training_dataset(training_dataset_path)

  # The split must stay chronological because this is time-series data.
  # We do not shuffle rows: older data trains the models, newer data validates them,
  # and the newest block remains the protected test split.
  train_data, validation_data, test_data = split_time_series_data(
    data=training_data,
    train_ratio=modeling_config["train_ratio"],
    validation_ratio=modeling_config["validation_ratio"],
    test_ratio=modeling_config["test_ratio"],
  )

  # Each model result is stored in memory first.
  # At the end, we rewrite reports/model_results.csv once so repeated runs do not
  # keep appending duplicate rows.
  results = []

  for horizon_hours in horizons_hours:
    # Convert a horizon number into the exact target column name used in the dataset.
    # Example: 24 becomes actual_price_target_24h.
    target_column = build_target_column_name(horizon_hours)

    print("")
    print(f"Regression horizon: {horizon_hours}h")
    print("=" * 32)
    print(f"Target column: {target_column}")

    # The naive baseline does not learn. It predicts the future target using the
    # previous-hour actual price. This gives us a simple benchmark that learned
    # models should beat.
    print("Evaluating Naive Baseline prediction_column=actual_price_lag_1h on test split")
    baseline_scores = evaluate_naive_baseline(
      data=test_data,
      target_column=target_column,
    )
    results.append(
      build_naive_baseline_result(
        scores=baseline_scores,
        row_count=len(test_data),
        horizon_hours=horizon_hours,
      )
    )

    # Linear Regression is the simplest learned benchmark.
    # It helps us see whether the engineered features have a basic linear
    # relationship with the selected future price target.
    print("Training Linear Regression fit_intercept=True on train split")
    linear_regression_model = train_linear_regression_model(
      train_data=train_data,
      target_column=target_column,
    )
    linear_regression_scores = evaluate_linear_regression_model(
      model=linear_regression_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_linear_regression_result(
        scores=linear_regression_scores,
        row_count=len(validation_data),
        split="validation",
        horizon_hours=horizon_hours,
      )
    )

    # Ridge is Linear Regression with coefficient shrinkage.
    # This is useful when features are correlated, because Ridge can reduce unstable
    # coefficients without removing features completely.
    print("Training Ridge Regression alpha=1.0 on train split")
    ridge_model = train_ridge_regression_model(
      train_data=train_data,
      target_column=target_column,
    )
    ridge_scores = evaluate_ridge_regression_model(
      model=ridge_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_ridge_regression_result(
        scores=ridge_scores,
        row_count=len(validation_data),
        split="validation",
        horizon_hours=horizon_hours,
      )
    )

    # Tuned Ridge searches for the best alpha value using TimeSeriesSplit.
    # The tuning happens only inside train_data, so validation_data remains a clean
    # holdout split for model comparison.
    print("Tuning Ridge Regression with TimeSeriesSplit on train split")
    best_ridge_result = tune_ridge_alpha(
      train_data=train_data,
      target_column=target_column,
    )
    best_alpha = best_ridge_result["alpha"]
    tuned_ridge_model = train_ridge_regression_model(
      train_data=train_data,
      alpha=best_alpha,
      target_column=target_column,
    )
    tuned_ridge_scores = evaluate_ridge_regression_model(
      model=tuned_ridge_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_tuned_ridge_result(
        scores=tuned_ridge_scores,
        row_count=len(validation_data),
        split="validation",
        best_alpha=best_alpha,
        cv_mae=best_ridge_result["cv_mae"],
        cv_rmse=best_ridge_result["cv_rmse"],
        horizon_hours=horizon_hours,
      )
    )

    # Lasso can shrink weak feature coefficients to zero.
    # This gives us a regularized linear model that can behave like a simple
    # feature-selection method.
    print("Training Lasso Regression alpha=1.0 on train split")
    lasso_model = train_lasso_regression_model(
      train_data=train_data,
      target_column=target_column,
    )
    lasso_scores = evaluate_lasso_regression_model(
      model=lasso_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_lasso_regression_result(
        scores=lasso_scores,
        row_count=len(validation_data),
        split="validation",
        horizon_hours=horizon_hours,
      )
    )

    # Tuned Lasso searches alpha values using only the training split.
    # The selected alpha is then retrained on the full train split before validation.
    print("Tuning Lasso Regression with TimeSeriesSplit on train split")
    best_lasso_result = tune_lasso_alpha(
      train_data=train_data,
      target_column=target_column,
    )
    best_lasso_alpha = best_lasso_result["alpha"]
    tuned_lasso_model = train_lasso_regression_model(
      train_data=train_data,
      alpha=best_lasso_alpha,
      target_column=target_column,
    )
    tuned_lasso_scores = evaluate_lasso_regression_model(
      model=tuned_lasso_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_tuned_lasso_result(
        scores=tuned_lasso_scores,
        row_count=len(validation_data),
        split="validation",
        best_alpha=best_lasso_alpha,
        cv_mae=best_lasso_result["cv_mae"],
        cv_rmse=best_lasso_result["cv_rmse"],
        horizon_hours=horizon_hours,
      )
    )

    # Elastic Net combines Ridge and Lasso behavior.
    # alpha controls the total regularization strength, and l1_ratio controls the
    # balance between Ridge-style shrinkage and Lasso-style feature selection.
    print("Training Elastic Net Regression alpha=1.0 l1_ratio=0.5 on train split")
    elastic_net_model = train_elastic_net_regression_model(
      train_data=train_data,
      target_column=target_column,
    )
    elastic_net_scores = evaluate_elastic_net_regression_model(
      model=elastic_net_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_elastic_net_regression_result(
        scores=elastic_net_scores,
        row_count=len(validation_data),
        split="validation",
        horizon_hours=horizon_hours,
      )
    )

    # Tuned Elastic Net searches both alpha and l1_ratio.
    # This is more expensive than Ridge or Lasso tuning, but it gives the model
    # flexibility to choose the best regularization mix.
    print("Tuning Elastic Net Regression with TimeSeriesSplit on train split")
    best_elastic_net_result = tune_elastic_net_config(
      train_data=train_data,
      target_column=target_column,
    )
    best_elastic_net_config = best_elastic_net_result["config"]

    print(f"Training tuned Elastic Net {format_elastic_net_parameters(best_elastic_net_config)} on train split")
    tuned_elastic_net_model = train_elastic_net_regression_model(
      train_data=train_data,
      alpha=best_elastic_net_config["alpha"],
      l1_ratio=best_elastic_net_config["l1_ratio"],
      target_column=target_column,
    )
    tuned_elastic_net_scores = evaluate_elastic_net_regression_model(
      model=tuned_elastic_net_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_tuned_elastic_net_result(
        scores=tuned_elastic_net_scores,
        row_count=len(validation_data),
        split="validation",
        best_config=best_elastic_net_config,
        cv_mae=best_elastic_net_result["cv_mae"],
        cv_rmse=best_elastic_net_result["cv_rmse"],
        horizon_hours=horizon_hours,
      )
    )

    # Random Forest is the first non-linear model in this workflow.
    # It can capture interactions between time features, load/forecast signals,
    # lags, and rolling price summaries.
    print("Training Random Forest base configuration on train split")
    random_forest_model = train_random_forest_model(
      train_data=train_data,
      n_estimators=RANDOM_FOREST_N_ESTIMATORS,
      max_depth=RANDOM_FOREST_MAX_DEPTH,
      min_samples_leaf=RANDOM_FOREST_MIN_SAMPLES_LEAF,
      random_state=RANDOM_FOREST_RANDOM_STATE,
      target_column=target_column,
    )
    random_forest_scores = evaluate_random_forest_model(
      model=random_forest_model,
      evaluation_data=validation_data,
      target_column=target_column,
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
        horizon_hours=horizon_hours,
      )
    )

    # Tuned Random Forest searches a small set of tree configurations.
    # The search is intentionally limited so the workflow remains practical while
    # still testing whether tree depth and leaf size improve validation MAE.
    print("Tuning Random Forest with TimeSeriesSplit on train split")
    best_random_forest_result = tune_random_forest_config(
      train_data=train_data,
      target_column=target_column,
    )
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
      target_column=target_column,
    )
    tuned_random_forest_scores = evaluate_random_forest_model(
      model=tuned_random_forest_model,
      evaluation_data=validation_data,
      target_column=target_column,
    )
    results.append(
      build_tuned_random_forest_result(
        scores=tuned_random_forest_scores,
        row_count=len(validation_data),
        split="validation",
        best_config=best_random_forest_config,
        cv_mae=best_random_forest_result["cv_mae"],
        cv_rmse=best_random_forest_result["cv_rmse"],
        horizon_hours=horizon_hours,
      )
    )

  # The output CSV now contains one row per model per horizon.
  # This structure lets us compare models separately for 1h, 3h, 6h, 12h, and 24h
  # instead of pretending that one global score represents all forecast distances.
  return write_model_results(
    results=results,
    output_path=results_path,
  )


if __name__ == "__main__":
  written_results_path = run_regression_models()

  print("")
  print("Regression models completed")
  print("===========================")
  print(f"Results written to: {written_results_path}")
