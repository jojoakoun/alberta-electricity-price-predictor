"""Evaluate simple price-threshold spike baselines."""

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
  AESO_FORECAST_COLUMN,
  PREVIOUS_DAY_PRICE_COLUMN,
)


AESO_FORECAST_BASELINE_NAME = "aeso_forecast_spike_baseline"

PREVIOUS_DAY_BASELINE_NAME = "previous_day_spike_baseline"


def predict_spikes_from_price_column(
  data: pd.DataFrame,
  price_column: str,
  threshold: float,
) -> pd.Series:
  """Predict spikes when one available price signal exceeds the threshold."""
  if price_column not in data.columns:
    raise ValueError(
      f"Missing baseline price column: {price_column}"
    )

  return (
    data[price_column] > threshold
  ).astype(int)


def evaluate_rule_spike_baseline(
  data: pd.DataFrame,
  target_column: str,
  price_column: str,
  threshold: float,
) -> dict[str, float]:
  """Evaluate one deterministic price-threshold baseline."""
  if target_column not in data.columns:
    raise ValueError(
      f"Missing classification target column: {target_column}"
    )

  prediction = predict_spikes_from_price_column(
    data=data,
    price_column=price_column,
    threshold=threshold,
  )

  return calculate_classification_metrics(
    target=data[target_column],
    prediction=prediction,
  )


def build_rule_spike_baseline_result(
  model_name: str,
  price_column: str,
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  threshold: float,
  split: str = "validation",
) -> dict:
  """Build one shared result row for a deterministic spike baseline."""
  return build_model_result_row(
    model_name=model_name,
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"prediction_column={price_column}; "
      f"spike_threshold={threshold:.6f}"
    ),
    notes=(
      f"{model_name} evaluated on the chronological {split} split."
    ),
  )


def run_rule_spike_baseline(
  model_name: str,
  price_column: str,
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Evaluate one price-threshold baseline across all horizons."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  training_data = load_training_dataset(
    training_dataset_path
  )

  train_data, validation_data, _ = (
    split_time_series_data_from_config(
      data=training_data,
      modeling_config=modeling_config,
    )
  )

  _, prepared_validation, threshold = (
    prepare_classification_training_splits(
      train_data=train_data,
      validation_data=validation_data,
      horizons_hours=horizons_hours,
    )
  )

  for horizon_hours in horizons_hours:
    target_column = build_spike_target_column_name(
      horizon_hours
    )

    scores = evaluate_rule_spike_baseline(
      data=prepared_validation,
      target_column=target_column,
      price_column=price_column,
      threshold=threshold,
    )

    result = build_rule_spike_baseline_result(
      model_name=model_name,
      price_column=price_column,
      scores=scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
      threshold=threshold,
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print("")
    print(f"{model_name}: {horizon_hours}h")
    print("=" * 45)
    print(f"Prediction column: {price_column}")
    print(f"Spike threshold: {threshold:.4f}")
    print(f"Accuracy: {scores['accuracy']:.4f}")
    print(f"Precision: {scores['precision']:.4f}")
    print(f"Recall: {scores['recall']:.4f}")
    print(f"F1: {scores['f1']:.4f}")

  return results_path


def run_aeso_forecast_spike_baseline(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Evaluate the AESO forecast price as a spike predictor."""
  return run_rule_spike_baseline(
    model_name=AESO_FORECAST_BASELINE_NAME,
    price_column=AESO_FORECAST_COLUMN,
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )


def run_previous_day_spike_baseline(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Evaluate previous-day price persistence as a spike predictor."""
  return run_rule_spike_baseline(
    model_name=PREVIOUS_DAY_BASELINE_NAME,
    price_column=PREVIOUS_DAY_PRICE_COLUMN,
    training_dataset_path=training_dataset_path,
    results_path=results_path,
  )
