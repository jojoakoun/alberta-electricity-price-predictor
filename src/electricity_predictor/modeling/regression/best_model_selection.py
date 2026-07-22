from pathlib import Path

import pandas as pd

from electricity_predictor.modeling.model_results import (
  REGRESSION_VALIDATION_RESULTS_PATH,
)

# These are the only regression metrics we allow for best-model selection.
# Lower MAE and lower RMSE both mean better prediction performance.
VALID_SELECTION_METRICS = ["mae", "rmse"]

# MAE is the default selection criterion because it is easier to interpret:
# on average, how many dollars per MWh the model is wrong by.
DEFAULT_SELECTION_METRIC = "mae"


def load_model_results(file_path: Path) -> pd.DataFrame:
  """Load the regression model results summary."""
  if not file_path.exists():
    raise FileNotFoundError(f"Model results file not found: {file_path}")

  # The results CSV is produced by run_regression_models.py.
  return pd.read_csv(file_path)


def validate_model_results_columns(results: pd.DataFrame) -> None:
  """Validate that the model results file has the columns needed for selection."""
  required_columns = {
    "model_name",
    "task",
    "horizon_hours",
    "split",
    "mae",
    "rmse",
    "model_parameters",
  }

  missing_columns = required_columns - set(results.columns)

  if missing_columns:
    raise ValueError(f"Model results file is missing columns: {sorted(missing_columns)}")


def validate_selection_metric(metric: str) -> None:
  """Validate that the selected metric is supported for regression model selection."""
  if metric not in VALID_SELECTION_METRICS:
    raise ValueError(f"Selection metric must be one of: {VALID_SELECTION_METRICS}")


def filter_validation_regression_results(results: pd.DataFrame) -> pd.DataFrame:
  """Keep only validation regression rows that can be used for model selection."""
  validate_model_results_columns(results)

  # Classification rows are excluded because they use different metrics.
  regression_results = results[results["task"] == "regression"].copy()

  # Validation is the model-selection split. The protected test split is not used here.
  validation_results = regression_results[regression_results["split"] == "validation"].copy()

  # Rows without a horizon cannot participate in multi-horizon model selection.
  validation_results = validation_results[validation_results["horizon_hours"].notna()].copy()

  # Rows without MAE cannot participate because MAE is the default selection metric.
  validation_results = validation_results[validation_results["mae"].notna()].copy()

  return validation_results


def select_best_regression_model(
  results: pd.DataFrame,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> dict:
  """Select the single best validation regression model using the lowest metric."""
  validate_selection_metric(metric)

  validation_results = filter_validation_regression_results(results)

  if validation_results.empty:
    raise ValueError("No validation regression results available for model selection.")

  validation_results[metric] = pd.to_numeric(validation_results[metric], errors="coerce")
  validation_results = validation_results[validation_results[metric].notna()].copy()

  if validation_results.empty:
    raise ValueError(f"No usable {metric} values available for model selection.")

  # This function is kept for backward compatibility with older tests and scripts.
  # Multi-horizon selection should normally use select_best_regression_models_by_horizon().
  best_model = validation_results.sort_values(metric, ascending=True).iloc[0]

  return best_model.to_dict()


def select_best_regression_models_by_horizon(
  results: pd.DataFrame,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> list[dict]:
  """Select the best validation regression model separately for each horizon."""
  validate_selection_metric(metric)

  validation_results = filter_validation_regression_results(results)

  if validation_results.empty:
    raise ValueError("No validation regression results available for model selection.")

  # Convert the metric once before grouping so every horizon uses numeric comparisons.
  validation_results[metric] = pd.to_numeric(validation_results[metric], errors="coerce")
  validation_results = validation_results[validation_results[metric].notna()].copy()

  if validation_results.empty:
    raise ValueError(f"No usable {metric} values available for model selection.")

  selected_models = []

  # Each horizon represents a different prediction problem, so each one gets its own winner.
  for horizon_hours, horizon_results in validation_results.groupby("horizon_hours"):
    best_model = horizon_results.sort_values(metric, ascending=True).iloc[0].to_dict()
    selected_models.append(best_model)

  # Keep output stable and readable: 1h, 3h, 6h, 12h, 24h.
  return sorted(selected_models, key=lambda row: row["horizon_hours"])


def add_selection_metadata(
  best_model: dict,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> dict:
  """Add clear selection metadata to one selected model row."""
  selected_model = best_model.copy()

  selected_model["selection_metric"] = metric
  selected_model["selection_rule"] = f"lowest_validation_{metric}_within_horizon"

  # Include the horizon in the explanation so the output does not look like one global winner.
  selected_model["selection_reason"] = (
    f"Selected because it has the lowest validation {metric.upper()} "
    f"among regression models for the {selected_model['horizon_hours']}h horizon."
  )

  return selected_model


def add_selection_metadata_to_models(
  best_models: list[dict],
  metric: str = DEFAULT_SELECTION_METRIC,
) -> list[dict]:
  """Add selection metadata to all selected horizon winners."""
  return [
    add_selection_metadata(best_model=best_model, metric=metric)
    for best_model in best_models
  ]


def write_best_regression_model(best_model: dict, output_path: Path) -> Path:
  """Write one selected best regression model to a CSV file."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  best_model_data = pd.DataFrame([best_model])
  best_model_data.to_csv(output_path, index=False)

  return output_path


def write_best_regression_models(best_models: list[dict], output_path: Path) -> Path:
  """Write selected best regression models to a multi-row CSV file."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # One row per horizon makes the file useful for later final evaluation or model saving.
  best_models_data = pd.DataFrame(best_models)
  best_models_data.to_csv(output_path, index=False)

  return output_path


def print_best_models_summary(best_models: list[dict], output_path: Path) -> None:
  """Print a readable summary of the selected regression models."""
  print("Best regression models by horizon")
  print("=================================")

  for best_model in best_models:
    print("")
    print(f"Horizon: {best_model['horizon_hours']}h")
    print(f"Model: {best_model['model_name']}")
    print(f"Selection metric: {best_model['selection_metric']}")
    print(f"Selection rule: {best_model['selection_rule']}")
    print(f"Split used for selection: {best_model['split']}")
    print(f"MAE: {best_model['mae']:.4f}")
    print(f"RMSE: {best_model['rmse']:.4f}")
    print(f"Parameters: {best_model['model_parameters']}")
    print(f"Reason: {best_model['selection_reason']}")

  print("")
  print(f"Selection file written to: {output_path}")


if __name__ == "__main__":
  model_results_path = REGRESSION_VALIDATION_RESULTS_PATH
  best_model_path = Path("reports/best_regression_model.csv")

  model_results = load_model_results(model_results_path)

  best_regression_models = select_best_regression_models_by_horizon(
    results=model_results,
    metric=DEFAULT_SELECTION_METRIC,
  )

  # Add metadata so each selected row explains its own selection rule.
  best_regression_models = add_selection_metadata_to_models(
    best_models=best_regression_models,
    metric=DEFAULT_SELECTION_METRIC,
  )

  written_path = write_best_regression_models(
    best_models=best_regression_models,
    output_path=best_model_path,
  )

  print_best_models_summary(
    best_models=best_regression_models,
    output_path=written_path,
  )
