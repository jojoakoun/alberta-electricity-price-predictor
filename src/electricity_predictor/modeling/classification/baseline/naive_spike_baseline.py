from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_training_splits,
)
from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
)
from electricity_predictor.modeling.model_results import (
  CLASSIFICATION_VALIDATION_RESULTS_PATH,
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)
from electricity_predictor.contracts.columns import (
  BASELINE_PRICE_COLUMN,
)


CLASSIFICATION_BASELINE_NAME = "naive_spike_baseline"


def predict_spike_persistence(
  data: pd.DataFrame,
  threshold: float,
) -> pd.Series:
  """Predict a future spike when the previous-hour price exceeds the threshold."""
  if BASELINE_PRICE_COLUMN not in data.columns:
    raise ValueError(f"Missing prediction column: {BASELINE_PRICE_COLUMN}")

  return (data[BASELINE_PRICE_COLUMN] > threshold).astype(int)


def evaluate_classification_baseline(
  data: pd.DataFrame,
  target_column: str,
  threshold: float,
) -> dict[str, float]:
  """Evaluate the naive spike baseline against one horizon target."""
  if target_column not in data.columns:
    raise ValueError(f"Missing classification target column: {target_column}")

  prediction = predict_spike_persistence(
    data=data,
    threshold=threshold,
  )

  return calculate_classification_metrics(
    target=data[target_column],
    prediction=prediction,
  )


def build_classification_baseline_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  threshold: float,
  split: str = "validation",
) -> dict:
  """Build one model result row for the naive spike baseline."""
  return build_model_result_row(
    model_name=CLASSIFICATION_BASELINE_NAME,
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"prediction_column={BASELINE_PRICE_COLUMN}; "
      f"spike_threshold={threshold:.6f}"
    ),
    notes=(
      "Previous-hour spike persistence baseline evaluated on the "
      f"chronological {split} split."
    ),
  )


def run_classification_baseline(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Evaluate the naive spike baseline for all configured horizons."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  training_data = load_training_dataset(training_dataset_path)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  _, prepared_validation, threshold = prepare_classification_training_splits(
    train_data=train_data,
    validation_data=validation_data,
    horizons_hours=horizons_hours,
  )

  for horizon_hours in horizons_hours:
    target_column = build_spike_target_column_name(horizon_hours)

    scores = evaluate_classification_baseline(
      data=prepared_validation,
      target_column=target_column,
      threshold=threshold,
    )

    result = build_classification_baseline_result(
      scores=scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
      threshold=threshold,
      split="validation",
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print("")
    print(f"Classification baseline: {horizon_hours}h")
    print("=" * 35)
    print(f"Threshold: {threshold:.4f}")
    print(f"Accuracy: {scores['accuracy']:.4f}")
    print(f"Precision: {scores['precision']:.4f}")
    print(f"Recall: {scores['recall']:.4f}")
    print(f"F1: {scores['f1']:.4f}")

  return results_path


if __name__ == "__main__":
  written_path = run_classification_baseline()
  print("")
  print(f"Results written to: {written_path}")
