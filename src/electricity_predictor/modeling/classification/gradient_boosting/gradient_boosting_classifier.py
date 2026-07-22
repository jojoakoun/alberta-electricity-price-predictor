from pathlib import Path

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_splits,
)
from electricity_predictor.modeling.metrics import calculate_classification_metrics
from electricity_predictor.modeling.model_results import (
  CLASSIFICATION_VALIDATION_RESULTS_PATH,
  append_model_result,
  build_model_result_row,
)
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


CLASSIFICATION_FEATURE_COLUMNS = MODEL_FEATURE_COLUMNS


def train_gradient_boosting_classifier(
  train_data: pd.DataFrame,
  target_column: str,
  n_estimators: int = 100,
  learning_rate: float = 0.1,
  max_depth: int = 3,
) -> GradientBoostingClassifier:
  """Train a Gradient Boosting classifier for one spike target."""
  if target_column not in train_data.columns:
    raise ValueError(f"Missing classification target column: {target_column}")

  features = train_data[CLASSIFICATION_FEATURE_COLUMNS]
  target = train_data[target_column]

  model = GradientBoostingClassifier(
    n_estimators=n_estimators,
    learning_rate=learning_rate,
    max_depth=max_depth,
    random_state=42,
  )

  # GradientBoostingClassifier has no class_weight parameter.
  # Balanced sample weights prevent the rare spike class from being ignored.
  sample_weight = compute_sample_weight(
    class_weight="balanced",
    y=target,
  )

  model.fit(
    features,
    target,
    sample_weight=sample_weight,
  )

  return model


def evaluate_gradient_boosting_classifier(
  model: GradientBoostingClassifier,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Evaluate Gradient Boosting against one classification target."""
  if target_column not in evaluation_data.columns:
    raise ValueError(f"Missing classification target column: {target_column}")

  features = evaluation_data[CLASSIFICATION_FEATURE_COLUMNS]
  target = evaluation_data[target_column]
  prediction = model.predict(features)
  probability = model.predict_proba(features)[:, 1]

  return calculate_classification_metrics(
    target=target,
    prediction=prediction,
    probability=probability,
  )


def build_gradient_boosting_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  split: str = "validation",
  n_estimators: int = 100,
  learning_rate: float = 0.1,
  max_depth: int = 3,
) -> dict:
  """Build one shared result row for Gradient Boosting classification."""
  return build_model_result_row(
    model_name="gradient_boosting_classifier",
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=(
      f"n_estimators={n_estimators}; "
      f"learning_rate={learning_rate}; "
      f"max_depth={max_depth}; "
      "sample_weight=balanced; random_state=42"
    ),
    notes=(
      "Gradient Boosting classifier trained on the chronological train split "
      f"and evaluated on the chronological {split} split."
    ),
  )


def run_gradient_boosting_classifier(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Train and evaluate Gradient Boosting for all configured horizons."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  training_data = load_training_dataset(training_dataset_path)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  prepared_train, prepared_validation, _, threshold = prepare_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=horizons_hours,
  )

  for horizon_hours in horizons_hours:
    target_column = build_spike_target_column_name(horizon_hours)

    model = train_gradient_boosting_classifier(
      train_data=prepared_train,
      target_column=target_column,
    )

    scores = evaluate_gradient_boosting_classifier(
      model=model,
      evaluation_data=prepared_validation,
      target_column=target_column,
    )

    result = build_gradient_boosting_result(
      scores=scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print("")
    print(f"Gradient Boosting Classifier: {horizon_hours}h")
    print("=" * 42)
    print(f"Spike threshold: {threshold:.4f}")
    print(f"Accuracy: {scores['accuracy']:.4f}")
    print(f"Precision: {scores['precision']:.4f}")
    print(f"Recall: {scores['recall']:.4f}")
    print(f"F1: {scores['f1']:.4f}")

  return results_path


if __name__ == "__main__":
  written_path = run_gradient_boosting_classifier()

  print("")
  print(f"Results written to: {written_path}")
