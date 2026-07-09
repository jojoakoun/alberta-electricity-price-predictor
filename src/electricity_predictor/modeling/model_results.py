from pathlib import Path

import pandas as pd


MODEL_RESULT_COLUMNS = [
  "model_name",
  "task",
  "horizon_hours",
  "split",
  "evaluation_rows",
  "model_parameters",
  "mae",
  "rmse",
  "accuracy",
  "precision",
  "recall",
  "f1",
  "notes",
]


def build_model_result_row(
  model_name: str,
  task: str,
  split: str,
  evaluation_rows: int,
  metrics: dict[str, float],
  horizon_hours: int | None = None,
  model_parameters: str = "",
  notes: str = "",
) -> dict:
  """Build one model evaluation row for the results summary."""
  result = {
    "model_name": model_name,
    "task": task,
    "horizon_hours": horizon_hours,
    "split": split,
    "evaluation_rows": evaluation_rows,
    "model_parameters": model_parameters,
    "mae": None,
    "rmse": None,
    "accuracy": None,
    "precision": None,
    "recall": None,
    "f1": None,
    "notes": notes,
  }

  # Only fill the metrics that apply to the current model type.
  for metric_name, metric_value in metrics.items():
    if metric_name in result:
      result[metric_name] = metric_value

  return result


def append_model_result(result: dict, output_path: Path) -> Path:
  """Append one model evaluation result to the shared summary file."""
  # Create the reports folder if this is the first model result.
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # Force a stable column order so the CSV remains easy to inspect.
  result_data = pd.DataFrame([result], columns=MODEL_RESULT_COLUMNS)

  if output_path.exists():
    existing_data = pd.read_csv(output_path)

    # Keep previous model results, then add the newest evaluation row.
    result_data = pd.concat([existing_data, result_data], ignore_index=True)

  result_data.to_csv(output_path, index=False)

  return output_path


def write_model_results(results: list[dict], output_path: Path) -> Path:
  """Write a fresh model evaluation summary file."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  # Rebuild the summary from the provided results so repeated runs stay clean.
  results_data = pd.DataFrame(results, columns=MODEL_RESULT_COLUMNS)
  results_data.to_csv(output_path, index=False)

  return output_path
