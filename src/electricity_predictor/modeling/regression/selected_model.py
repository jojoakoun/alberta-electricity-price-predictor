"""Build and use validation-selected regression models."""

from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  NAIVE_BASELINE_PREDICTION_COLUMN,
)
from electricity_predictor.modeling.regression.elastic_net.elastic_net_regression import (
  ELASTIC_NET_ALPHA,
  ELASTIC_NET_L1_RATIO,
  ELASTIC_NET_MAX_ITER,
  train_elastic_net_regression_model,
)
from electricity_predictor.modeling.regression.lasso.lasso_regression import (
  LASSO_ALPHA,
  LASSO_MAX_ITER,
  train_lasso_regression_model,
)
from electricity_predictor.modeling.regression.linear.linear_regression import (
  train_linear_regression_model,
)
from electricity_predictor.modeling.regression.random_forest.random_forest import (
  RANDOM_FOREST_MAX_DEPTH,
  RANDOM_FOREST_MIN_SAMPLES_LEAF,
  RANDOM_FOREST_N_ESTIMATORS,
  RANDOM_FOREST_RANDOM_STATE,
  train_random_forest_model,
)
from electricity_predictor.modeling.regression.ridge.ridge_regression import (
  RIDGE_ALPHA,
  train_ridge_regression_model,
)


BEST_MODEL_PATH = Path("reports/best_regression_model.csv")


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


# Tuned models must be rebuilt with the parameters selected on validation.
# Falling back to defaults would silently construct a different model.
TUNED_REQUIRED_PARAMETERS = {
  "ridge_regression_tuned": ["best_alpha"],
  "lasso_regression_tuned": ["best_alpha"],
  "elastic_net_regression_tuned": ["alpha", "l1_ratio"],
  "random_forest_regressor_tuned": [
    "n_estimators",
    "max_depth",
    "min_samples_leaf",
  ],
}


def validate_tuned_model_parameters(
  model_name: str,
  parameters: dict[str, str],
) -> None:
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


def load_selected_regression_models(
  file_path: Path = BEST_MODEL_PATH,
) -> pd.DataFrame:
  """Load and validate the validation-selected regression rows."""
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
  """Fit the selected estimator with its recorded validation parameters."""
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
    n_estimators = get_int_parameter(
      parameters,
      ["n_estimators"],
      RANDOM_FOREST_N_ESTIMATORS,
    )
    max_depth = get_optional_int_parameter(
      parameters,
      ["max_depth"],
      RANDOM_FOREST_MAX_DEPTH,
    )
    min_samples_leaf = get_int_parameter(
      parameters,
      ["min_samples_leaf"],
      RANDOM_FOREST_MIN_SAMPLES_LEAF,
    )
    random_state = get_int_parameter(
      parameters,
      ["random_state"],
      RANDOM_FOREST_RANDOM_STATE,
    )
    return train_random_forest_model(
      train_data=train_data,
      n_estimators=n_estimators,
      max_depth=max_depth,
      min_samples_leaf=min_samples_leaf,
      random_state=random_state,
      target_column=target_column,
    )

  raise ValueError(f"Unsupported selected regression model: {model_name}")


def predict_selected_regression_model(
  selected_model: dict,
  model,
  data: pd.DataFrame,
) -> pd.Series:
  """Return index-aligned predictions for a selected model or baseline."""
  if selected_model["model_name"] == "naive_baseline":
    return data[NAIVE_BASELINE_PREDICTION_COLUMN]

  predictions = model.predict(data[MODEL_FEATURE_COLUMNS])
  return pd.Series(predictions, index=data.index)
