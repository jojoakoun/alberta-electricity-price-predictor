from pathlib import Path

import pandas as pd
from sklearn.metrics import confusion_matrix

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.block_bootstrap import (
  calculate_f1_block_bootstrap_interval,
)
from electricity_predictor.modeling.classification.baseline.naive_spike_baseline import (
  evaluate_classification_baseline,
)
from electricity_predictor.modeling.classification.decision_threshold import (
  apply_decision_threshold,
  select_f1_decision_threshold,
)
from electricity_predictor.modeling.classification.gradient_boosting.gradient_boosting_classifier import (
  evaluate_gradient_boosting_classifier,
  train_gradient_boosting_classifier,
)
from electricity_predictor.modeling.classification.logistic.logistic_regression import (
  evaluate_logistic_regression_model,
  train_logistic_regression_model,
)
from electricity_predictor.modeling.classification.random_forest.random_forest_classifier import (
  evaluate_random_forest_classifier,
  train_random_forest_classifier,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_splits,
)
from electricity_predictor.modeling.metrics import calculate_classification_metrics
from electricity_predictor.modeling.model_results import (
  build_model_result_row,
  write_model_results,
)
from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


BEST_MODEL_PATH = Path("reports/best_classification_model.csv")
FINAL_TEST_RESULTS_PATH = Path(
  "reports/final_classification_test_results.csv"
)
FINAL_CONFUSION_MATRICES_PATH = Path(
  "reports/final_classification_confusion_matrices.csv"
)
FINAL_CONFIDENCE_INTERVALS_PATH = Path(
  "reports/final_classification_confidence_intervals.csv"
)


TUNED_REQUIRED_PARAMETERS = {
  "logistic_regression_tuned": ["best_C"],
  "random_forest_classifier_tuned": [
    "n_estimators",
    "max_depth",
    "min_samples_leaf",
  ],
  "gradient_boosting_classifier_tuned": [
    "n_estimators",
    "learning_rate",
    "max_depth",
  ],
}


def parse_model_parameters(parameter_text: str) -> dict[str, str]:
  """Parse the saved semicolon-separated model parameters."""
  if not isinstance(parameter_text, str) or not parameter_text.strip():
    return {}

  parameters = {}

  for part in parameter_text.split(";"):
    if "=" not in part:
      continue

    key, value = part.split("=", 1)
    parameters[key.strip()] = value.strip()

  return parameters


def validate_tuned_model_parameters(
  model_name: str,
  parameters: dict[str, str],
) -> None:
  """Reject tuned models that are missing selected hyperparameters."""
  required_parameters = TUNED_REQUIRED_PARAMETERS.get(
    model_name,
    [],
  )

  missing_parameters = [
    parameter
    for parameter in required_parameters
    if parameter not in parameters
  ]

  if missing_parameters:
    raise ValueError(
      f"Tuned model {model_name} is missing required parameters: "
      f"{missing_parameters}."
    )


def get_float_parameter(
  parameters: dict[str, str],
  names: list[str],
  default: float,
) -> float:
  """Read the first available float parameter."""
  for name in names:
    if name in parameters:
      return float(parameters[name])

  return default


def get_int_parameter(
  parameters: dict[str, str],
  names: list[str],
  default: int,
) -> int:
  """Read the first available integer parameter."""
  for name in names:
    if name in parameters:
      return int(parameters[name])

  return default


def get_optional_int_parameter(
  parameters: dict[str, str],
  names: list[str],
  default: int | None,
) -> int | None:
  """Read an integer parameter that may be stored as None."""
  for name in names:
    if name not in parameters:
      continue

    if parameters[name] == "None":
      return None

    return int(parameters[name])

  return default


def load_selected_classification_models(
  file_path: Path = BEST_MODEL_PATH,
) -> pd.DataFrame:
  """Load validation-selected classification models."""
  if not file_path.exists():
    raise FileNotFoundError(
      f"Best classification model file not found: {file_path}"
    )

  selected_models = pd.read_csv(file_path)

  required_columns = {
    "model_name",
    "horizon_hours",
    "model_parameters",
    "selection_metric",
    "selection_rule",
  }

  missing_columns = required_columns - set(selected_models.columns)

  if missing_columns:
    raise ValueError(
      f"Best classification model file is missing columns: "
      f"{sorted(missing_columns)}"
    )

  return selected_models.sort_values(
    "horizon_hours"
  ).reset_index(drop=True)


def train_selected_classification_model(
  selected_model: dict,
  train_data: pd.DataFrame,
  target_column: str,
):
  """Train one selected learned classification model."""
  model_name = selected_model["model_name"]
  parameters = parse_model_parameters(
    selected_model.get("model_parameters", "")
  )

  validate_tuned_model_parameters(
    model_name=model_name,
    parameters=parameters,
  )

  if model_name in [
    "logistic_regression",
    "logistic_regression_tuned",
  ]:
    c_value = get_float_parameter(
      parameters,
      ["best_C", "C"],
      1.0,
    )

    return train_logistic_regression_model(
      train_data=train_data,
      target_column=target_column,
      c_value=c_value,
    )

  if model_name in [
    "random_forest_classifier",
    "random_forest_classifier_tuned",
  ]:
    return train_random_forest_classifier(
      train_data=train_data,
      target_column=target_column,
      n_estimators=get_int_parameter(
        parameters,
        ["n_estimators"],
        100,
      ),
      max_depth=get_optional_int_parameter(
        parameters,
        ["max_depth"],
        None,
      ),
      min_samples_leaf=get_int_parameter(
        parameters,
        ["min_samples_leaf"],
        1,
      ),
    )

  if model_name in [
    "gradient_boosting_classifier",
    "gradient_boosting_classifier_tuned",
  ]:
    return train_gradient_boosting_classifier(
      train_data=train_data,
      target_column=target_column,
      n_estimators=get_int_parameter(
        parameters,
        ["n_estimators"],
        100,
      ),
      learning_rate=get_float_parameter(
        parameters,
        ["learning_rate"],
        0.1,
      ),
      max_depth=get_int_parameter(
        parameters,
        ["max_depth"],
        3,
      ),
    )

  raise ValueError(
    f"Unsupported selected classification model: {model_name}"
  )


def evaluate_trained_classification_model(
  selected_model: dict,
  model,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Evaluate one trained selected classification model."""
  model_name = selected_model["model_name"]

  if model_name in [
    "logistic_regression",
    "logistic_regression_tuned",
  ]:
    return evaluate_logistic_regression_model(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  if model_name in [
    "random_forest_classifier",
    "random_forest_classifier_tuned",
  ]:
    return evaluate_random_forest_classifier(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  if model_name in [
    "gradient_boosting_classifier",
    "gradient_boosting_classifier_tuned",
  ]:
    return evaluate_gradient_boosting_classifier(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  raise ValueError(
    f"Unsupported selected classification model: {model_name}"
  )


def select_model_decision_threshold(
  selected_model: dict,
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Select a probability cutoff using validation data only."""
  model = train_selected_classification_model(
    selected_model=selected_model,
    train_data=train_data,
    target_column=target_column,
  )

  validation_features = validation_data[MODEL_FEATURE_COLUMNS]
  validation_probability = model.predict_proba(
    validation_features
  )[:, 1]

  return select_f1_decision_threshold(
    target=validation_data[target_column],
    probability=validation_probability,
  )


def evaluate_selected_classification_model(
  selected_model: dict,
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  evaluation_data: pd.DataFrame,
  target_column: str,
  threshold: float,
) -> tuple[dict[str, float | None], pd.Series, float | None]:
  """Select a validation cutoff and evaluate once on protected test data."""
  target = evaluation_data[target_column]

  if selected_model["model_name"] == "naive_spike_baseline":
    prediction = (
      evaluation_data["actual_price_lag_1h"] > threshold
    ).astype(int)

    scores = calculate_classification_metrics(
      target=target,
      prediction=prediction,
    )

    return scores, prediction, None

  threshold_result = select_model_decision_threshold(
    selected_model=selected_model,
    train_data=train_data,
    validation_data=validation_data,
    target_column=target_column,
  )
  decision_threshold = threshold_result["decision_threshold"]

  final_training_data = pd.concat(
    [train_data, validation_data],
    ignore_index=True,
  )

  model = train_selected_classification_model(
    selected_model=selected_model,
    train_data=final_training_data,
    target_column=target_column,
  )

  features = evaluation_data[MODEL_FEATURE_COLUMNS]
  probability = pd.Series(
    model.predict_proba(features)[:, 1],
    index=evaluation_data.index,
  )
  prediction = pd.Series(
    apply_decision_threshold(
      probability=probability,
      threshold=decision_threshold,
    ),
    index=evaluation_data.index,
  )

  scores = calculate_classification_metrics(
    target=target,
    prediction=prediction,
    probability=probability,
  )

  return scores, prediction, decision_threshold


def build_confusion_matrix_row(
  selected_model: dict,
  target: pd.Series,
  prediction: pd.Series,
) -> dict:
  """Build one auditable binary confusion-matrix row."""
  true_negative, false_positive, false_negative, true_positive = (
    confusion_matrix(
      target,
      prediction,
      labels=[0, 1],
    ).ravel()
  )

  return {
    "model_name": selected_model["model_name"],
    "horizon_hours": int(selected_model["horizon_hours"]),
    "split": "test",
    "true_negative": int(true_negative),
    "false_positive": int(false_positive),
    "false_negative": int(false_negative),
    "true_positive": int(true_positive),
  }


def write_confusion_matrices(
  rows: list[dict],
  output_path: Path = FINAL_CONFUSION_MATRICES_PATH,
) -> Path:
  """Persist final confusion matrices for every forecast horizon."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  columns = [
    "model_name",
    "horizon_hours",
    "split",
    "true_negative",
    "false_positive",
    "false_negative",
    "true_positive",
  ]

  pd.DataFrame(rows, columns=columns).to_csv(
    output_path,
    index=False,
  )

  return output_path


def build_f1_confidence_interval_row(
  selected_model: dict,
  target: pd.Series,
  prediction: pd.Series,
) -> dict:
  """Build one block-bootstrap F1 confidence-interval row."""
  interval = calculate_f1_block_bootstrap_interval(
    target=target,
    prediction=prediction,
  )

  return {
    "model_name": selected_model["model_name"],
    "horizon_hours": int(selected_model["horizon_hours"]),
    "split": "test",
    "metric": interval["metric"],
    "estimate": interval["estimate"],
    "confidence_level": interval["confidence_level"],
    "ci_lower": interval["ci_lower"],
    "ci_upper": interval["ci_upper"],
    "block_size": interval["block_size"],
    "iterations": interval["iterations"],
  }


def write_confidence_intervals(
  rows: list[dict],
  output_path: Path = FINAL_CONFIDENCE_INTERVALS_PATH,
) -> Path:
  """Persist block-bootstrap confidence intervals by horizon."""
  output_path.parent.mkdir(parents=True, exist_ok=True)

  columns = [
    "model_name",
    "horizon_hours",
    "split",
    "metric",
    "estimate",
    "confidence_level",
    "ci_lower",
    "ci_upper",
    "block_size",
    "iterations",
  ]

  pd.DataFrame(rows, columns=columns).to_csv(
    output_path,
    index=False,
  )

  return output_path


def build_final_classification_test_result(
  selected_model: dict,
  scores: dict[str, float],
  row_count: int,
) -> dict:
  """Build one protected classification test result."""
  horizon_hours = int(selected_model["horizon_hours"])

  return build_model_result_row(
    model_name=selected_model["model_name"],
    task="classification",
    horizon_hours=horizon_hours,
    split="test",
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=selected_model.get(
      "model_parameters",
      "",
    ),
    notes=(
      "Final protected classification test evaluation after "
      f"validation selection for the {horizon_hours}h horizon."
    ),
  )


def run_final_classification_test_evaluation() -> Path:
  """Evaluate selected classifiers on the protected test split."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]
  horizons_hours = modeling_config["horizons_hours"]

  selected_models = load_selected_classification_models()
  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  (
    prepared_train,
    prepared_validation,
    prepared_test,
    threshold,
  ) = prepare_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=horizons_hours,
  )

  # Validation selects the probability cutoff before final retraining.
  final_results = []
  confusion_matrix_rows = []
  confidence_interval_rows = []

  for selected_model in selected_models.to_dict(orient="records"):
    horizon_hours = int(selected_model["horizon_hours"])
    target_column = build_spike_target_column_name(horizon_hours)

    print("")
    print(f"Final classification test: {horizon_hours}h")
    print("=" * 36)
    print(f"Selected model: {selected_model['model_name']}")
    print(f"Target column: {target_column}")
    print(f"Frozen spike threshold: {threshold:.4f}")

    scores, prediction, decision_threshold = (
      evaluate_selected_classification_model(
        selected_model=selected_model,
        train_data=prepared_train,
        validation_data=prepared_validation,
        evaluation_data=prepared_test,
        target_column=target_column,
        threshold=threshold,
      )
    )

    if decision_threshold is not None:
      selected_model["model_parameters"] = (
        f"{selected_model.get('model_parameters', '')}; "
        f"decision_threshold={decision_threshold:.4f}"
      ).strip("; ")

    confusion_matrix_rows.append(
      build_confusion_matrix_row(
        selected_model=selected_model,
        target=prepared_test[target_column],
        prediction=prediction,
      )
    )

    confidence_interval_rows.append(
      build_f1_confidence_interval_row(
        selected_model=selected_model,
        target=prepared_test[target_column],
        prediction=prediction,
      )
    )

    final_results.append(
      build_final_classification_test_result(
        selected_model=selected_model,
        scores=scores,
        row_count=len(prepared_test),
      )
    )

  results_path = write_model_results(
    results=final_results,
    output_path=FINAL_TEST_RESULTS_PATH,
  )

  write_confusion_matrices(
    rows=confusion_matrix_rows,
  )

  write_confidence_intervals(
    rows=confidence_interval_rows,
  )

  return results_path


def print_final_classification_test_summary(
  results_path: Path,
) -> None:
  """Print final protected classification results."""
  results = pd.read_csv(results_path)

  print("")
  print("Final protected classification test results")
  print("===========================================")

  for _, result in results.iterrows():
    print(
      f"{int(result['horizon_hours'])}h | "
      f"{result['model_name']} | "
      f"F1: {result['f1']:.4f} | "
      f"Precision: {result['precision']:.4f} | "
      f"Recall: {result['recall']:.4f} | "
      f"Accuracy: {result['accuracy']:.4f}"
    )

  print("")
  print(f"Final test results written to: {results_path}")


if __name__ == "__main__":
  written_path = run_final_classification_test_evaluation()

  print_final_classification_test_summary(
    results_path=written_path,
  )
