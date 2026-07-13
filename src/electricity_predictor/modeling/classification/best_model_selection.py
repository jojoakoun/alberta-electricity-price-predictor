from pathlib import Path

import pandas as pd


VALID_SELECTION_METRICS = ["f1", "recall", "precision", "accuracy"]
DEFAULT_SELECTION_METRIC = "f1"

MODEL_RESULTS_PATH = Path("reports/model_results.csv")
BEST_CLASSIFICATION_MODEL_PATH = Path("reports/best_classification_model.csv")


def load_model_results(file_path: Path = MODEL_RESULTS_PATH) -> pd.DataFrame:
  """Load the shared model results summary."""
  if not file_path.exists():
    raise FileNotFoundError(f"Model results file not found: {file_path}")

  return pd.read_csv(file_path)


def validate_model_results_columns(results: pd.DataFrame) -> None:
  """Validate the columns required for classification model selection."""
  required_columns = {
    "model_name",
    "task",
    "horizon_hours",
    "split",
    "accuracy",
    "precision",
    "recall",
    "f1",
    "model_parameters",
  }

  missing_columns = required_columns - set(results.columns)

  if missing_columns:
    raise ValueError(
      f"Model results file is missing columns: {sorted(missing_columns)}"
    )


def validate_selection_metric(metric: str) -> None:
  """Validate the requested classification selection metric."""
  if metric not in VALID_SELECTION_METRICS:
    raise ValueError(
      f"Selection metric must be one of: {VALID_SELECTION_METRICS}"
    )


def filter_validation_classification_results(
  results: pd.DataFrame,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> pd.DataFrame:
  """Keep usable classification results from the validation split."""
  validate_model_results_columns(results)
  validate_selection_metric(metric)

  filtered = results[
    (results["task"] == "classification")
    & (results["split"] == "validation")
    & results["horizon_hours"].notna()
  ].copy()

  filtered[metric] = pd.to_numeric(filtered[metric], errors="coerce")
  filtered = filtered[filtered[metric].notna()].copy()

  return filtered


def select_best_classification_models_by_horizon(
  results: pd.DataFrame,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> list[dict]:
  """Select the strongest validation classifier for each horizon."""
  validation_results = filter_validation_classification_results(
    results=results,
    metric=metric,
  )

  if validation_results.empty:
    raise ValueError(
      "No validation classification results available for model selection."
    )

  selected_models = []

  for _, horizon_results in validation_results.groupby("horizon_hours"):
    # F1 is primary. Recall, precision, and accuracy provide deterministic tie-breaks.
    sorted_results = horizon_results.sort_values(
      by=[metric, "recall", "precision", "accuracy"],
      ascending=[False, False, False, False],
    )

    selected_models.append(sorted_results.iloc[0].to_dict())

  return sorted(
    selected_models,
    key=lambda row: row["horizon_hours"],
  )


def add_selection_metadata(
  selected_model: dict,
  metric: str = DEFAULT_SELECTION_METRIC,
) -> dict:
  """Add the classification selection rule to one selected result."""
  result = selected_model.copy()
  horizon_hours = int(result["horizon_hours"])

  result["selection_metric"] = metric
  result["selection_rule"] = (
    f"highest_validation_{metric}_within_horizon"
  )
  result["selection_reason"] = (
    f"Selected because it has the highest validation {metric.upper()} "
    f"among classification models for the {horizon_hours}h horizon."
  )

  return result


def add_selection_metadata_to_models(
  selected_models: list[dict],
  metric: str = DEFAULT_SELECTION_METRIC,
) -> list[dict]:
  """Add selection metadata to all horizon winners."""
  return [
    add_selection_metadata(
      selected_model=selected_model,
      metric=metric,
    )
    for selected_model in selected_models
  ]


def write_best_classification_models(
  selected_models: list[dict],
  output_path: Path = BEST_CLASSIFICATION_MODEL_PATH,
) -> Path:
  """Write one selected classification model per horizon."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  pd.DataFrame(selected_models).to_csv(
    output_path,
    index=False,
  )

  return output_path


def print_best_classification_models_summary(
  selected_models: list[dict],
  output_path: Path,
) -> None:
  """Print the selected classifier for every forecast horizon."""
  print("Best classification models by horizon")
  print("=====================================")

  for model in selected_models:
    print("")
    print(f"Horizon: {int(model['horizon_hours'])}h")
    print(f"Model: {model['model_name']}")
    print(f"F1: {model['f1']:.4f}")
    print(f"Precision: {model['precision']:.4f}")
    print(f"Recall: {model['recall']:.4f}")
    print(f"Accuracy: {model['accuracy']:.4f}")
    print(f"Parameters: {model['model_parameters']}")

  print("")
  print(f"Selection file written to: {output_path}")


if __name__ == "__main__":
  model_results = load_model_results()

  best_models = select_best_classification_models_by_horizon(
    results=model_results,
    metric=DEFAULT_SELECTION_METRIC,
  )

  best_models = add_selection_metadata_to_models(
    selected_models=best_models,
    metric=DEFAULT_SELECTION_METRIC,
  )

  written_path = write_best_classification_models(
    selected_models=best_models,
  )

  print_best_classification_models_summary(
    selected_models=best_models,
    output_path=written_path,
  )
