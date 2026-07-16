from pathlib import Path

import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.features.feature_engineering import build_target_column_name
from electricity_predictor.modeling.model_results import build_model_result_row, write_model_results
from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  evaluate_naive_baseline,
)
from electricity_predictor.modeling.regression.elastic_net.elastic_net_regression import (
  ELASTIC_NET_ALPHA,
  ELASTIC_NET_L1_RATIO,
  ELASTIC_NET_MAX_ITER,
  evaluate_elastic_net_regression_model,
  train_elastic_net_regression_model,
)
from electricity_predictor.modeling.regression.lasso.lasso_regression import (
  LASSO_ALPHA,
  LASSO_MAX_ITER,
  evaluate_lasso_regression_model,
  train_lasso_regression_model,
)
from electricity_predictor.modeling.regression.linear.linear_regression import (
  evaluate_linear_regression_model,
  train_linear_regression_model,
)
from electricity_predictor.modeling.regression.random_forest.random_forest import (
  RANDOM_FOREST_MAX_DEPTH,
  RANDOM_FOREST_MIN_SAMPLES_LEAF,
  RANDOM_FOREST_N_ESTIMATORS,
  RANDOM_FOREST_RANDOM_STATE,
  evaluate_random_forest_model,
  train_random_forest_model,
)
from electricity_predictor.modeling.regression.ridge.ridge_regression import (
  RIDGE_ALPHA,
  evaluate_ridge_regression_model,
  train_ridge_regression_model,
)
from electricity_predictor.modeling.split import (
  TRAINING_DATASET_PATH,
  load_training_dataset,
  split_time_series_data_from_config,
)


BEST_MODEL_PATH = Path("reports/best_regression_model.csv")
FINAL_TEST_RESULTS_PATH = Path("reports/final_regression_test_results.csv")


def parse_model_parameters(parameter_text: str) -> dict[str, str]:
  """Parse the saved model parameter string into a dictionary."""
  if not isinstance(parameter_text, str) or not parameter_text.strip():
    return {}

  parameters = {}

  for part in parameter_text.split(";"):
    if "=" not in part:
      continue

    key, value = part.split("=", 1)
    parameters[key.strip()] = value.strip()

  return parameters


# Tuned models must be retrained with their selected parameters.
# Falling back to defaults would silently evaluate a different model
# than the one chosen during validation selection.
TUNED_REQUIRED_PARAMETERS = {
  "ridge_regression_tuned": ["best_alpha"],
  "lasso_regression_tuned": ["best_alpha"],
  "elastic_net_regression_tuned": ["alpha", "l1_ratio"],
  "random_forest_regressor_tuned": ["n_estimators", "max_depth", "min_samples_leaf"],
}


def validate_tuned_model_parameters(model_name: str, parameters: dict[str, str]) -> None:
  """Reject tuned models whose selected parameters are missing."""
  required_names = TUNED_REQUIRED_PARAMETERS.get(model_name, [])

  missing_names = [name for name in required_names if name not in parameters]

  if missing_names:
    raise ValueError(
      f"Tuned model {model_name} is missing required parameters: {missing_names}. "
      "Refusing to retrain with default hyperparameters."
    )


def get_parameter_value(
  parameters: dict[str, str],
  names: list[str],
  default: str | None = None,
) -> str | None:
  """Get the first available parameter value from several possible names."""
  for name in names:
    if name in parameters:
      return parameters[name]

  return default


def get_float_parameter(
  parameters: dict[str, str],
  names: list[str],
  default: float,
) -> float:
  """Read a float parameter from saved model metadata."""
  value = get_parameter_value(parameters, names)

  if value is None:
    return default

  return float(value)


def get_int_parameter(
  parameters: dict[str, str],
  names: list[str],
  default: int,
) -> int:
  """Read an integer parameter from saved model metadata."""
  value = get_parameter_value(parameters, names)

  if value is None:
    return default

  return int(value)


def get_optional_int_parameter(
  parameters: dict[str, str],
  names: list[str],
  default: int | None,
) -> int | None:
  """Read an integer parameter that may also be saved as None."""
  value = get_parameter_value(parameters, names)

  if value is None:
    return default

  if value == "None":
    return None

  return int(value)


def load_selected_regression_models(file_path: Path = BEST_MODEL_PATH) -> pd.DataFrame:
  """Load the validation-selected regression models."""
  if not file_path.exists():
    raise FileNotFoundError(f"Best regression model file not found: {file_path}")

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
    raise ValueError(f"Best model file is missing columns: {sorted(missing_columns)}")

  return selected_models.sort_values("horizon_hours").reset_index(drop=True)


def train_selected_regression_model(
  selected_model: dict,
  train_data: pd.DataFrame,
  target_column: str,
):
  """Train the selected regression model for one horizon."""
  model_name = selected_model["model_name"]
  parameters = parse_model_parameters(selected_model.get("model_parameters", ""))
  validate_tuned_model_parameters(model_name, parameters)

  if model_name == "linear_regression":
    return train_linear_regression_model(
      train_data=train_data,
      target_column=target_column,
    )

  if model_name in ["ridge_regression", "ridge_regression_tuned"]:
    alpha = get_float_parameter(parameters, ["best_alpha", "alpha"], RIDGE_ALPHA)

    return train_ridge_regression_model(
      train_data=train_data,
      alpha=alpha,
      target_column=target_column,
    )

  if model_name in ["lasso_regression", "lasso_regression_tuned"]:
    alpha = get_float_parameter(parameters, ["best_alpha", "alpha"], LASSO_ALPHA)
    max_iter = get_int_parameter(parameters, ["max_iter"], LASSO_MAX_ITER)

    return train_lasso_regression_model(
      train_data=train_data,
      alpha=alpha,
      max_iter=max_iter,
      target_column=target_column,
    )

  if model_name in ["elastic_net_regression", "elastic_net_regression_tuned"]:
    alpha = get_float_parameter(parameters, ["alpha"], ELASTIC_NET_ALPHA)
    l1_ratio = get_float_parameter(parameters, ["l1_ratio"], ELASTIC_NET_L1_RATIO)
    max_iter = get_int_parameter(parameters, ["max_iter"], ELASTIC_NET_MAX_ITER)

    return train_elastic_net_regression_model(
      train_data=train_data,
      alpha=alpha,
      l1_ratio=l1_ratio,
      max_iter=max_iter,
      target_column=target_column,
    )

  if model_name in ["random_forest_regressor", "random_forest_regressor_tuned"]:
    n_estimators = get_int_parameter(parameters, ["n_estimators"], RANDOM_FOREST_N_ESTIMATORS)
    max_depth = get_optional_int_parameter(parameters, ["max_depth"], RANDOM_FOREST_MAX_DEPTH)
    min_samples_leaf = get_int_parameter(
      parameters,
      ["min_samples_leaf"],
      RANDOM_FOREST_MIN_SAMPLES_LEAF,
    )
    random_state = get_int_parameter(parameters, ["random_state"], RANDOM_FOREST_RANDOM_STATE)

    return train_random_forest_model(
      train_data=train_data,
      n_estimators=n_estimators,
      max_depth=max_depth,
      min_samples_leaf=min_samples_leaf,
      random_state=random_state,
      target_column=target_column,
    )

  raise ValueError(f"Unsupported selected regression model: {model_name}")


def evaluate_trained_selected_regression_model(
  selected_model: dict,
  model,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Evaluate a trained selected model on the protected test split."""
  model_name = selected_model["model_name"]

  if model_name == "linear_regression":
    return evaluate_linear_regression_model(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  if model_name in ["ridge_regression", "ridge_regression_tuned"]:
    return evaluate_ridge_regression_model(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  if model_name in ["lasso_regression", "lasso_regression_tuned"]:
    return evaluate_lasso_regression_model(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  if model_name in ["elastic_net_regression", "elastic_net_regression_tuned"]:
    return evaluate_elastic_net_regression_model(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  if model_name in ["random_forest_regressor", "random_forest_regressor_tuned"]:
    return evaluate_random_forest_model(
      model=model,
      evaluation_data=evaluation_data,
      target_column=target_column,
    )

  raise ValueError(f"Unsupported selected regression model: {model_name}")


def evaluate_selected_regression_model(
  selected_model: dict,
  train_data: pd.DataFrame,
  evaluation_data: pd.DataFrame,
  target_column: str,
) -> dict[str, float]:
  """Evaluate one selected model against the protected test split."""
  model_name = selected_model["model_name"]

  if model_name == "naive_baseline":
    return evaluate_naive_baseline(
      data=evaluation_data,
      target_column=target_column,
    )

  model = train_selected_regression_model(
    selected_model=selected_model,
    train_data=train_data,
    target_column=target_column,
  )

  return evaluate_trained_selected_regression_model(
    selected_model=selected_model,
    model=model,
    evaluation_data=evaluation_data,
    target_column=target_column,
  )


def build_final_test_result(
  selected_model: dict,
  scores: dict[str, float],
  row_count: int,
) -> dict:
  """Build one final protected test result row."""
  horizon_hours = int(selected_model["horizon_hours"])

  return build_model_result_row(
    model_name=selected_model["model_name"],
    task="regression",
    horizon_hours=horizon_hours,
    split="test",
    evaluation_rows=row_count,
    metrics=scores,
    model_parameters=selected_model.get("model_parameters", ""),
    notes=(
      "Final protected test evaluation after validation selection "
      f"for the {horizon_hours}h horizon."
    ),
  )


def run_final_regression_test_evaluation() -> Path:
  """Evaluate validation-selected regression models on the protected test split."""
  configuration = load_configuration()
  modeling_config = configuration["modeling"]

  selected_models = load_selected_regression_models(BEST_MODEL_PATH)
  training_data = load_training_dataset(TRAINING_DATASET_PATH)

  train_data, validation_data, test_data = split_time_series_data_from_config(
    data=training_data,
    modeling_config=modeling_config,
)

  # After model selection, train on train + validation before the one-time test evaluation.
  final_training_data = pd.concat([train_data, validation_data], ignore_index=True)

  final_results = []

  for selected_model in selected_models.to_dict(orient="records"):
    horizon_hours = int(selected_model["horizon_hours"])
    target_column = build_target_column_name(horizon_hours)

    print("")
    print(f"Final test evaluation: {horizon_hours}h")
    print("=" * 34)
    print(f"Selected model: {selected_model['model_name']}")
    print(f"Target column: {target_column}")

    scores = evaluate_selected_regression_model(
      selected_model=selected_model,
      train_data=final_training_data,
      evaluation_data=test_data,
      target_column=target_column,
    )

    final_results.append(
      build_final_test_result(
        selected_model=selected_model,
        scores=scores,
        row_count=len(test_data),
      )
    )

  return write_model_results(
    results=final_results,
    output_path=FINAL_TEST_RESULTS_PATH,
  )


def print_final_test_summary(results_path: Path) -> None:
  """Print the final protected test results."""
  results = pd.read_csv(results_path)

  print("")
  print("Final protected regression test results")
  print("=======================================")

  for _, result in results.iterrows():
    print(
      f"{int(result['horizon_hours'])}h | "
      f"{result['model_name']} | "
      f"MAE: {result['mae']:.4f} | "
      f"RMSE: {result['rmse']:.4f}"
    )

  print("")
  print(f"Final test results written to: {results_path}")


if __name__ == "__main__":
  written_path = run_final_regression_test_evaluation()
  print_final_test_summary(written_path)
