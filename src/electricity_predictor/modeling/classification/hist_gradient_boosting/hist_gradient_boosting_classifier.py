"""Train and evaluate HistGradientBoosting spike classifiers."""

from pathlib import Path

import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.utils.class_weight import compute_sample_weight

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_training_splits,
)
from electricity_predictor.modeling.classification.validation_evaluation import (
  add_decision_threshold_to_parameters,
  evaluate_classifier_on_validation,
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


CLASSIFICATION_FEATURE_COLUMNS = MODEL_FEATURE_COLUMNS

DEFAULT_LEARNING_RATE = 0.1
DEFAULT_MAX_ITER = 100
DEFAULT_MAX_LEAF_NODES = 31
DEFAULT_MIN_SAMPLES_LEAF = 20
DEFAULT_L2_REGULARIZATION = 0.0


def train_hist_gradient_boosting_classifier(
  train_data: pd.DataFrame,
  target_column: str,
  learning_rate: float = DEFAULT_LEARNING_RATE,
  max_iter: int = DEFAULT_MAX_ITER,
  max_leaf_nodes: int = DEFAULT_MAX_LEAF_NODES,
  min_samples_leaf: int = DEFAULT_MIN_SAMPLES_LEAF,
  l2_regularization: float = DEFAULT_L2_REGULARIZATION,
) -> HistGradientBoostingClassifier:
  """Train one balanced HistGradientBoosting spike classifier."""
  if target_column not in train_data.columns:
    raise ValueError(
      f"Missing classification target column: {target_column}"
    )

  features = train_data[CLASSIFICATION_FEATURE_COLUMNS]
  target = train_data[target_column]

  model = HistGradientBoostingClassifier(
    loss="log_loss",
    learning_rate=learning_rate,
    max_iter=max_iter,
    max_leaf_nodes=max_leaf_nodes,
    min_samples_leaf=min_samples_leaf,
    l2_regularization=l2_regularization,
    early_stopping=False,
    random_state=42,
  )

  # Balanced weights prevent the less frequent spike class from being ignored.
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


def evaluate_hist_gradient_boosting_classifier(
  model: HistGradientBoostingClassifier,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Evaluate HistGradientBoosting at its native prediction cutoff."""
  if target_column not in evaluation_data.columns:
    raise ValueError(
      f"Missing classification target column: {target_column}"
    )

  features = evaluation_data[CLASSIFICATION_FEATURE_COLUMNS]
  target = evaluation_data[target_column]
  prediction = model.predict(features)
  probability = model.predict_proba(features)[:, 1]

  return calculate_classification_metrics(
    target=target,
    prediction=prediction,
    probability=probability,
  )


def build_hist_gradient_boosting_result(
  scores: dict[str, float],
  row_count: int,
  horizon_hours: int,
  decision_threshold: float,
  split: str = "validation",
  learning_rate: float = DEFAULT_LEARNING_RATE,
  max_iter: int = DEFAULT_MAX_ITER,
  max_leaf_nodes: int = DEFAULT_MAX_LEAF_NODES,
  min_samples_leaf: int = DEFAULT_MIN_SAMPLES_LEAF,
  l2_regularization: float = DEFAULT_L2_REGULARIZATION,
) -> dict:
  """Build one validation-result row for the base model."""
  parameters = (
    f"learning_rate={learning_rate}; "
    f"max_iter={max_iter}; "
    f"max_leaf_nodes={max_leaf_nodes}; "
    f"min_samples_leaf={min_samples_leaf}; "
    f"l2_regularization={l2_regularization}; "
    "loss=log_loss; sample_weight=balanced; "
    "early_stopping=False; random_state=42"
  )

  return build_model_result_row(
    model_name="hist_gradient_boosting_classifier",
    task="classification",
    horizon_hours=horizon_hours,
    split=split,
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=add_decision_threshold_to_parameters(
      parameter_text=parameters,
      decision_threshold=decision_threshold,
    ),
    notes=(
      "HistGradientBoosting classifier trained on the chronological "
      f"train split and evaluated on the chronological {split} split."
    ),
  )


def run_hist_gradient_boosting_classifier(
  training_dataset_path: Path = TRAINING_DATASET_PATH,
  results_path: Path = CLASSIFICATION_VALIDATION_RESULTS_PATH,
) -> Path:
  """Train and evaluate the base model for all configured horizons."""
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

  prepared_train, prepared_validation, spike_threshold = (
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

    model = train_hist_gradient_boosting_classifier(
      train_data=prepared_train,
      target_column=target_column,
    )

    scores, decision_threshold = (
      evaluate_classifier_on_validation(
        model=model,
        validation_data=prepared_validation,
        target_column=target_column,
      )
    )

    result = build_hist_gradient_boosting_result(
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
    print(f"HistGradientBoosting Classifier: {horizon_hours}h")
    print("=" * 48)
    print(f"Spike threshold: {spike_threshold:.4f}")
    print(f"Decision threshold: {decision_threshold:.4f}")
    print(f"Accuracy: {scores['accuracy']:.4f}")
    print(f"Precision: {scores['precision']:.4f}")
    print(f"Recall: {scores['recall']:.4f}")
    print(f"F1: {scores['f1']:.4f}")
    print(f"PR-AUC: {scores['pr_auc']:.4f}")

  return results_path


if __name__ == "__main__":
  written_path = run_hist_gradient_boosting_classifier()

  print("")
  print(f"Results written to: {written_path}")
