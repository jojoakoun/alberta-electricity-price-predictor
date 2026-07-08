from pathlib import Path

import pandas as pd


# These are the only regression metrics we allow for best-model selection.
# Lower MAE and lower RMSE both mean better prediction performance.
VALID_SELECTION_METRICS = ["mae", "rmse"]

# MAE is the default selection criterion because it is easier to interpret:
# on average, how many dollars per MWh the model is wrong by.
DEFAULT_SELECTION_METRIC = "mae"


def load_model_results(file_path: Path) -> pd.DataFrame:
  """Load the regression model results summary."""
  # The model results file is created by run_regression_models.py.
  if not file_path.exists():
    raise FileNotFoundError(f"Model results file not found: {file_path}")

  # Read the CSV into a DataFrame so we can filter, sort, and select the best row.
  return pd.read_csv(file_path)


def validate_model_results_columns(results: pd.DataFrame) -> None:
  """Validate that the model results file has the columns needed for selection."""
  required_columns = {
    "model_name",
    "task",
    "split",
    "mae",
    "rmse",
    "model_parameters",
  }

  # Stop early if the results file is missing important columns.
  missing_columns = required_columns - set(results.columns)

  if missing_columns:
    raise ValueError(f"Model results file is missing columns: {sorted(missing_columns)}")


def filter_validation_regression_results(results: pd.DataFrame) -> pd.DataFrame:
  """Keep only validation regression rows that can be used for model selection."""
  validate_model_results_columns(results)

  # Use only regression rows because classification models will use different metrics later.
  regression_results = results[results["task"] == "regression"].copy()

  # Use only validation rows because validation is the model-selection split.
  validation_results = regression_results[regression_results["split"] == "validation"].copy()

  # Remove rows without MAE because MAE is the default selection criterion.
  validation_results = validation_results[validation_results["mae"].notna()].copy()

  return validation_results


def select_best_regression_model(
  results: pd.DataFrame,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> dict:
  """Select the best validation regression model using the lowest selected metric."""
  # Only allow regression error metrics where lower is better.
  if metric not in VALID_SELECTION_METRICS:
    raise ValueError(f"Selection metric must be one of: {VALID_SELECTION_METRICS}")

  # Keep only the rows that are allowed to participate in model selection.
  validation_results = filter_validation_regression_results(results)

  # If there are no valid validation rows, the pipeline cannot choose a model honestly.
  if validation_results.empty:
    raise ValueError("No validation regression results available for model selection.")

  # Convert the metric column to numeric in case it was read from CSV as text.
  validation_results[metric] = pd.to_numeric(validation_results[metric], errors="coerce")

  # Remove rows where the selected metric could not be converted to a number.
  validation_results = validation_results[validation_results[metric].notna()].copy()

  if validation_results.empty:
    raise ValueError(f"No usable {metric} values available for model selection.")

  # Lower MAE or RMSE is better, so the first sorted row is the selected model.
  best_model = validation_results.sort_values(metric, ascending=True).iloc[0]

  # Convert the selected row into a dictionary so it can be written or printed easily.
  return best_model.to_dict()


def add_selection_metadata(
  best_model: dict,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> dict:
  """Add clear selection metadata to the selected model row."""
  selected_model = best_model.copy()

  # Store the exact rule used so future readers know why this model was selected.
  selected_model["selection_metric"] = metric

  # Store the selection direction because lower regression error means better performance.
  selected_model["selection_rule"] = f"lowest_validation_{metric}"

  # Store a readable explanation for documentation and future inspection.
  selected_model["selection_reason"] = (
    f"Selected because it has the lowest validation {metric.upper()} "
    "among regression models."
  )

  return selected_model


def write_best_regression_model(best_model: dict, output_path: Path) -> Path:
  """Write the selected best regression model to a one-row CSV file."""
  # Create the reports folder if it does not exist yet.
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # A one-row CSV is easy to inspect and easy for future pipeline steps to consume.
  best_model_data = pd.DataFrame([best_model])

  # Save the selected model summary for future final evaluation or model saving steps.
  best_model_data.to_csv(output_path, index=False)

  return output_path


def print_best_model_summary(best_model: dict, output_path: Path) -> None:
  """Print a readable summary of the selected regression model."""
  print("Best regression model")
  print("=====================")
  print(f"Model: {best_model['model_name']}")
  print(f"Selection metric: {best_model['selection_metric']}")
  print(f"Selection rule: {best_model['selection_rule']}")
  print(f"Split used for selection: {best_model['split']}")
  print(f"MAE: {best_model['mae']:.4f}")
  print(f"RMSE: {best_model['rmse']:.4f}")
  print(f"Parameters: {best_model['model_parameters']}")
  print(f"Reason: {best_model['selection_reason']}")
  print(f"Selection file written to: {output_path}")


if __name__ == "__main__":
  model_results_path = Path("reports/model_results.csv")
  best_model_path = Path("reports/best_regression_model.csv")

  # Load the comparison table produced by the regression modeling workflow.
  model_results = load_model_results(model_results_path)

  # Select the model with the lowest validation MAE.
  best_regression_model = select_best_regression_model(
    results=model_results,
    metric=DEFAULT_SELECTION_METRIC,
  )

  # Add metadata so the output explains how and why the model was selected.
  best_regression_model = add_selection_metadata(
    best_model=best_regression_model,
    metric=DEFAULT_SELECTION_METRIC,
  )

  # Write the selected model to reports/best_regression_model.csv.
  written_path = write_best_regression_model(
    best_model=best_regression_model,
    output_path=best_model_path,
  )

  # Print the selection result in the terminal.
  print_best_model_summary(
    best_model=best_regression_model,
    output_path=written_path,
  )
