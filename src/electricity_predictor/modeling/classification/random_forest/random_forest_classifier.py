from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_training_splits,
)
from electricity_predictor.modeling.classification.validation_evaluation import (
  add_decision_threshold_to_parameters,
  evaluate_classifier_on_validation,
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


def train_random_forest_classifier(
  train_data: pd.DataFrame,
  target_column: str,
  n_estimators: int = 100,
  max_depth: int | None = None,
  min_samples_leaf: int = 1,
) -> RandomForestClassifier:
  """Train a Random Forest classifier for one spike target."""
  if target_column not in train_data.columns:
    raise ValueError(f"Missing classification target column: {target_column}")

  features = train_data[CLASSIFICATION_FEATURE_COLUMNS]
  target = train_data[target_column]

  model = RandomForestClassifier(
    n_estimators=n_estimators,
    max_depth=max_depth,
    min_samples_leaf=min_samples_leaf,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1,
  )

  model.fit(features, target)

  return model


def evaluate_random_forest_classifier(
  model: RandomForestClassifier,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Evaluate Random Forest against one classification target."""
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


def build_random_forest_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  split: str = "validation",
  n_estimators: int = 100,
  max_depth: int | None = None,
  min_samples_leaf: int = 1,
  decision_threshold: float = 0.5,
) -> dict:
  """Build one shared result row for Random Forest classification."""
  return build_model_result_row(
    model_name="random_forest_classifier",
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=add_decision_threshold_to_parameters(
      parameter_text=(
        f"n_estimators={n_estimators}; "
        f"max_depth={max_depth}; "
        f"min_samples_leaf={min_samples_leaf}; "
        "class_weight=balanced; random_state=42; n_jobs=-1"
      ),
      decision_threshold=decision_threshold,
    ),
    notes=(
      "Random Forest classifier trained on the chronological train split "
      f"and evaluated on the chronological {split} split."
    ),
  )


def run_random_forest_classifier(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Train and evaluate Random Forest for all configured horizons."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  training_data = load_training_dataset(training_dataset_path)

  train_data, validation_data, _ = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  prepared_train, prepared_validation, threshold = prepare_classification_training_splits(
    train_data=train_data,
    validation_data=validation_data,
    horizons_hours=horizons_hours,
  )

  for horizon_hours in horizons_hours:
    target_column = build_spike_target_column_name(horizon_hours)

    model = train_random_forest_classifier(
      train_data=prepared_train,
      target_column=target_column,
    )

    scores, decision_threshold = evaluate_classifier_on_validation(
      model=model,
      validation_data=prepared_validation,
      target_column=target_column,
    )

    result = build_random_forest_result(
      scores=scores,
      row_count=len(prepared_validation),
      horizon_hours=horizon_hours,
      decision_threshold=decision_threshold,
    )

    append_model_result(
      result=result,
      output_path=results_path,
    )

    print("")
    print(f"Random Forest Classifier: {horizon_hours}h")
    print("=" * 38)
    print(f"Spike threshold: {threshold:.4f}")
    print(f"Accuracy: {scores['accuracy']:.4f}")
    print(f"Precision: {scores['precision']:.4f}")
    print(f"Recall: {scores['recall']:.4f}")
    print(f"F1: {scores['f1']:.4f}")
    print(f"Decision threshold: {decision_threshold:.4f}")

  return results_path


if __name__ == "__main__":
  written_path = run_random_forest_classifier()

  print("")
  print(f"Results written to: {written_path}")
