"""Compare current-hour feature contracts on chronological validation data."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import (
  GradientBoostingClassifier,
  HistGradientBoostingClassifier,
  HistGradientBoostingRegressor,
)
from sklearn.utils.class_weight import (
  compute_sample_weight,
)

from electricity_predictor.config import (
  load_configuration,
)
from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.live_feature_contract import (
  LIVE_FEATURE_CONTRACTS,
  add_live_feature_candidates,
)
from electricity_predictor.modeling.classification.decision_threshold import (
  evaluate_at_best_f1_threshold,
)
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.contracts.columns import (
  DATETIME_COLUMN,
)


HISTORICAL_DATASET_PATH = Path(
  "data/interim/current_historical_prices_clean.csv"
)

REGRESSION_METADATA_PATH = Path(
  "models/regression/"
  "selected_regression_model_metadata.csv"
)

CLASSIFICATION_METADATA_PATH = Path(
  "models/classification/"
  "selected_classification_model_metadata.csv"
)



def parse_parameter_text(
  parameter_text: object,
) -> dict[str, str]:
  """Parse semicolon-separated metadata parameters."""
  if not isinstance(parameter_text, str):
    return {}

  parameters = {}

  for part in parameter_text.split(";"):
    if "=" not in part:
      continue

    name, value = part.split(
      "=",
      1,
    )

    parameters[
      name.strip()
    ] = value.strip()

  return parameters


def parse_bool(
  value: str,
) -> bool:
  """Parse one explicit metadata boolean."""
  normalized = value.strip().lower()

  if normalized == "true":
    return True

  if normalized == "false":
    return False

  raise ValueError(
    f"Invalid boolean metadata value: {value}"
  )


def load_historical_prices(
  path: Path = HISTORICAL_DATASET_PATH,
) -> pd.DataFrame:
  """Load continuous hourly history for candidate feature construction."""
  if not path.exists():
    raise FileNotFoundError(
      f"Historical dataset not found: {path}"
    )

  data = pd.read_csv(path)

  required_columns = {
    DATETIME_COLUMN,
    "datetime_local_time",
    "actual_price",
    "forecast_price",
  }

  missing_columns = (
    required_columns - set(data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Historical dataset is missing columns: "
      f"{sorted(missing_columns)}"
    )

  data[DATETIME_COLUMN] = pd.to_datetime(
    data[DATETIME_COLUMN],
    utc=True,
    errors="raise",
  )

  data["datetime_local_time"] = pd.to_datetime(
    data["datetime_local_time"],
    errors="raise",
  )

  data["actual_price"] = pd.to_numeric(
    data["actual_price"],
    errors="coerce",
  )

  data["forecast_price"] = pd.to_numeric(
    data["forecast_price"],
    errors="coerce",
  )

  return (
    data
    .sort_values(DATETIME_COLUMN)
    .reset_index(drop=True)
  )


def add_horizon_targets(
  data: pd.DataFrame,
) -> pd.DataFrame:
  """Attach future actual-price targets without changing source-hour features."""
  result = data.copy()

  for horizon in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    result[
      f"actual_price_target_{horizon}h"
    ] = result["actual_price"].shift(
      -horizon
    )

  return result


def normalize_utc_timestamp(
  value: object,
  field_name: str,
) -> pd.Timestamp:
  """Return one configuration boundary as a timezone-aware UTC timestamp."""
  timestamp = pd.Timestamp(value)

  if pd.isna(timestamp):
    raise ValueError(
      f"{field_name} must be a valid timestamp."
    )

  if timestamp.tzinfo is None:
    return timestamp.tz_localize("UTC")

  return timestamp.tz_convert("UTC")


def build_validation_only_splits(
  data: pd.DataFrame,
  modeling_config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
  """Create train and validation splits without materializing protected test rows."""
  required_keys = {
    "train_start_utc",
    "validation_start_utc",
    "test_start_utc",
    "purge_hours",
  }

  missing_keys = (
    required_keys - set(modeling_config)
  )

  if missing_keys:
    raise ValueError(
      "Modeling configuration is missing keys: "
      f"{sorted(missing_keys)}"
    )

  train_start = normalize_utc_timestamp(
    modeling_config[
      "train_start_utc"
    ],
    "train_start_utc",
  )

  validation_start = normalize_utc_timestamp(
    modeling_config[
      "validation_start_utc"
    ],
    "validation_start_utc",
  )

  test_start = normalize_utc_timestamp(
    modeling_config[
      "test_start_utc"
    ],
    "test_start_utc",
  )

  purge = pd.Timedelta(
    hours=int(
      modeling_config[
        "purge_hours"
      ]
    )
  )

  train_end = (
    validation_start - purge
  )

  validation_end = (
    test_start - purge
  )

  timestamps = pd.to_datetime(
    data[DATETIME_COLUMN],
    utc=True,
    errors="raise",
  )

  train_data = data.loc[
    (timestamps >= train_start)
    & (timestamps < train_end)
  ].copy()

  validation_data = data.loc[
    (timestamps >= validation_start)
    & (timestamps < validation_end)
  ].copy()

  if (
    train_data.empty
    or validation_data.empty
  ):
    raise ValueError(
      "Validation-only split produced an empty period."
    )

  if (
    pd.to_datetime(
      validation_data[DATETIME_COLUMN],
      utc=True,
    )
    >= test_start
  ).any():
    raise RuntimeError(
      "Protected test rows entered validation comparison."
    )

  return (
    train_data.reset_index(drop=True),
    validation_data.reset_index(drop=True),
  )


def build_horizon_comparison_data(
  feature_data: pd.DataFrame,
  horizon: int,
  modeling_config: dict,
) -> tuple[
  pd.DataFrame,
  pd.DataFrame,
]:
  """Build identical train and validation rows for both live contracts."""
  target_column = (
    f"actual_price_target_{horizon}h"
  )

  conservative_columns = (
    LIVE_FEATURE_CONTRACTS[
      "conservative_hybrid"
    ]
  )

  required_columns = [
    DATETIME_COLUMN,
    "actual_price",
    target_column,
    *conservative_columns,
  ]

  comparison_data = (
    feature_data
    .dropna(
      subset=required_columns,
    )
    .copy()
  )

  return build_validation_only_splits(
    data=comparison_data,
    modeling_config=modeling_config,
  )


def build_regression_model(
  metadata_row: dict,
) -> HistGradientBoostingRegressor:
  """Recreate the selected regression estimator without using old features."""
  model_name = metadata_row[
    "model_name"
  ]

  if model_name != (
    "hist_gradient_boosting_regressor_tuned"
  ):
    raise ValueError(
      "Live comparison currently expects the selected "
      "HistGradientBoosting regressor."
    )

  parameters = parse_parameter_text(
    metadata_row[
      "model_parameters"
    ]
  )

  return HistGradientBoostingRegressor(
    loss=parameters["loss"],
    learning_rate=float(
      parameters["learning_rate"]
    ),
    max_iter=int(
      parameters["max_iter"]
    ),
    max_leaf_nodes=int(
      parameters["max_leaf_nodes"]
    ),
    min_samples_leaf=int(
      parameters["min_samples_leaf"]
    ),
    l2_regularization=float(
      parameters["l2_regularization"]
    ),
    early_stopping=parse_bool(
      parameters["early_stopping"]
    ),
    random_state=int(
      parameters["random_state"]
    ),
  )


def build_classification_model(
  metadata_row: dict,
):
  """Recreate one selected classifier without using old feature globals."""
  model_name = metadata_row[
    "model_name"
  ]

  parameters = parse_parameter_text(
    metadata_row[
      "model_parameters"
    ]
  )

  if model_name in {
    "hist_gradient_boosting_classifier",
    "hist_gradient_boosting_classifier_tuned",
  }:
    return HistGradientBoostingClassifier(
      loss="log_loss",
      learning_rate=float(
        parameters["learning_rate"]
      ),
      max_iter=int(
        parameters["max_iter"]
      ),
      max_leaf_nodes=int(
        parameters["max_leaf_nodes"]
      ),
      min_samples_leaf=int(
        parameters["min_samples_leaf"]
      ),
      l2_regularization=float(
        parameters["l2_regularization"]
      ),
      early_stopping=False,
      random_state=42,
    )

  if model_name == (
    "gradient_boosting_classifier_tuned"
  ):
    return GradientBoostingClassifier(
      n_estimators=int(
        parameters["n_estimators"]
      ),
      learning_rate=float(
        parameters["learning_rate"]
      ),
      max_depth=int(
        parameters["max_depth"]
      ),
      random_state=42,
    )

  raise ValueError(
    f"Unsupported selected classifier: {model_name}"
  )


def evaluate_regression_contract(
  contract_name: str,
  feature_columns: list[str],
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  metadata_row: dict,
  horizon: int,
) -> dict:
  """Evaluate one feature contract with the frozen selected estimator settings."""
  target_column = (
    f"actual_price_target_{horizon}h"
  )

  model = build_regression_model(
    metadata_row
  )

  model.fit(
    train_data[feature_columns],
    train_data[target_column],
  )

  predictions = model.predict(
    validation_data[
      feature_columns
    ]
  )

  return {
    "task": "regression",
    "contract": contract_name,
    "horizon_hours": horizon,
    "train_rows": len(train_data),
    "validation_rows": len(
      validation_data
    ),
    "mae": mean_absolute_error_value(
      validation_data[target_column],
      predictions,
    ),
    "rmse": root_mean_squared_error_value(
      validation_data[target_column],
      predictions,
    ),
    "f1": np.nan,
    "pr_auc": np.nan,
    "decision_threshold": np.nan,
  }


def evaluate_classification_contract(
  contract_name: str,
  feature_columns: list[str],
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  metadata_row: dict,
  horizon: int,
) -> dict:
  """Evaluate one live contract with train-derived spike labels."""
  price_target_column = (
    f"actual_price_target_{horizon}h"
  )

  spike_threshold = float(
    metadata_row[
      "spike_threshold"
    ]
  )

  spike_target_column = (
    f"is_spike_target_{horizon}h"
  )

  train_labeled = train_data.copy()
  validation_labeled = (
    validation_data.copy()
  )

  train_labeled[
    spike_target_column
  ] = (
    train_labeled[
      price_target_column
    ]
    > spike_threshold
  ).astype(int)

  validation_labeled[
    spike_target_column
  ] = (
    validation_labeled[
      price_target_column
    ]
    > spike_threshold
  ).astype(int)

  model = build_classification_model(
    metadata_row
  )

  sample_weight = compute_sample_weight(
    class_weight="balanced",
    y=train_labeled[
      spike_target_column
    ],
  )

  model.fit(
    train_labeled[feature_columns],
    train_labeled[
      spike_target_column
    ],
    sample_weight=sample_weight,
  )

  probability = model.predict_proba(
    validation_labeled[
      feature_columns
    ]
  )[:, 1]

  scores, decision_threshold = (
    evaluate_at_best_f1_threshold(
      target=validation_labeled[
        spike_target_column
      ],
      probability=probability,
    )
  )

  return {
    "task": "classification",
    "contract": contract_name,
    "horizon_hours": horizon,
    "train_rows": len(
      train_labeled
    ),
    "validation_rows": len(
      validation_labeled
    ),
    "mae": np.nan,
    "rmse": np.nan,
    "f1": scores["f1"],
    "pr_auc": scores["pr_auc"],
    "decision_threshold":
      decision_threshold,
  }


def validate_metadata_horizons(
  metadata: pd.DataFrame,
  name: str,
) -> None:
  """Require one metadata row for each supported horizon."""
  horizons = sorted(
    pd.to_numeric(
      metadata["horizon_hours"],
      errors="raise",
    )
    .astype(int)
    .tolist()
  )

  expected = list(
    SUPPORTED_FORECAST_HORIZONS_HOURS
  )

  if horizons != expected:
    raise ValueError(
      f"{name} metadata horizons are {horizons}; "
      f"expected {expected}."
    )


def compare_live_contracts() -> pd.DataFrame:
  """Run the isolated train/validation comparison for both prediction tasks."""
  configuration = load_configuration()
  modeling_config = configuration[
    "modeling"
  ]

  historical_data = (
    load_historical_prices()
  )

  feature_data = add_live_feature_candidates(
    historical_data
  )

  feature_data = add_horizon_targets(
    feature_data
  )

  regression_metadata = pd.read_csv(
    REGRESSION_METADATA_PATH
  )

  classification_metadata = pd.read_csv(
    CLASSIFICATION_METADATA_PATH
  )

  validate_metadata_horizons(
    regression_metadata,
    "Regression",
  )

  validate_metadata_horizons(
    classification_metadata,
    "Classification",
  )

  results = []

  for horizon in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    train_data, validation_data = (
      build_horizon_comparison_data(
        feature_data=feature_data,
        horizon=horizon,
        modeling_config=modeling_config,
      )
    )

    regression_row = (
      regression_metadata.loc[
        regression_metadata[
          "horizon_hours"
        ] == horizon
      ]
      .iloc[0]
      .to_dict()
    )

    classification_row = (
      classification_metadata.loc[
        classification_metadata[
          "horizon_hours"
        ] == horizon
      ]
      .iloc[0]
      .to_dict()
    )

    for (
      contract_name,
      feature_columns,
    ) in LIVE_FEATURE_CONTRACTS.items():
      results.append(
        evaluate_regression_contract(
          contract_name=contract_name,
          feature_columns=feature_columns,
          train_data=train_data,
          validation_data=validation_data,
          metadata_row=regression_row,
          horizon=horizon,
        )
      )

      results.append(
        evaluate_classification_contract(
          contract_name=contract_name,
          feature_columns=feature_columns,
          train_data=train_data,
          validation_data=validation_data,
          metadata_row=classification_row,
          horizon=horizon,
        )
      )

  return pd.DataFrame(results)


def print_comparison_summary(
  results: pd.DataFrame,
) -> None:
  """Print task-specific comparison tables and deterministic horizon winners."""
  regression = results.loc[
    results["task"] == "regression"
  ].copy()

  classification = results.loc[
    results["task"]
    == "classification"
  ].copy()

  print("")
  print("REGRESSION VALIDATION")
  print("=====================")

  print(
    regression[
      [
        "contract",
        "horizon_hours",
        "train_rows",
        "validation_rows",
        "mae",
        "rmse",
      ]
    ]
    .sort_values(
      [
        "horizon_hours",
        "contract",
      ]
    )
    .to_string(
      index=False,
      float_format=lambda value:
        f"{value:.6f}",
    )
  )

  print("")
  print("REGRESSION WINNERS BY MAE")
  print("=========================")

  regression_winners = (
    regression
    .sort_values(
      [
        "horizon_hours",
        "mae",
        "rmse",
        "contract",
      ]
    )
    .groupby(
      "horizon_hours",
      as_index=False,
    )
    .first()
  )

  print(
    regression_winners[
      [
        "horizon_hours",
        "contract",
        "mae",
        "rmse",
      ]
    ].to_string(
      index=False,
      float_format=lambda value:
        f"{value:.6f}",
    )
  )

  print("")
  print("CLASSIFICATION VALIDATION")
  print("=========================")

  print(
    classification[
      [
        "contract",
        "horizon_hours",
        "train_rows",
        "validation_rows",
        "f1",
        "pr_auc",
        "decision_threshold",
      ]
    ]
    .sort_values(
      [
        "horizon_hours",
        "contract",
      ]
    )
    .to_string(
      index=False,
      float_format=lambda value:
        f"{value:.6f}",
    )
  )

  print("")
  print("CLASSIFICATION WINNERS BY F1")
  print("============================")

  classification_winners = (
    classification
    .sort_values(
      [
        "horizon_hours",
        "f1",
        "pr_auc",
        "contract",
      ],
      ascending=[
        True,
        False,
        False,
        True,
      ],
    )
    .groupby(
      "horizon_hours",
      as_index=False,
    )
    .first()
  )

  print(
    classification_winners[
      [
        "horizon_hours",
        "contract",
        "f1",
        "pr_auc",
        "decision_threshold",
      ]
    ].to_string(
      index=False,
      float_format=lambda value:
        f"{value:.6f}",
    )
  )

  regression_counts = (
    regression_winners[
      "contract"
    ]
    .value_counts()
    .to_dict()
  )

  classification_counts = (
    classification_winners[
      "contract"
    ]
    .value_counts()
    .to_dict()
  )

  print("")
  print("WIN COUNTS")
  print("==========")

  for contract_name in sorted(
    LIVE_FEATURE_CONTRACTS
  ):
    print(
      f"{contract_name}: "
      f"regression_mae_wins="
      f"{regression_counts.get(contract_name, 0)} "
      f"classification_f1_wins="
      f"{classification_counts.get(contract_name, 0)}"
    )

  print("")
  print("protected_test_used=False")
  print("test_split_materialized=False")
  print("models_saved=False")
  print("active_registry_modified=False")


def main() -> None:
  """Run and optionally write the validation-only contract comparison."""
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "--output",
    type=Path,
    required=True,
  )

  arguments = parser.parse_args()

  results = compare_live_contracts()

  arguments.output.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  results.to_csv(
    arguments.output,
    index=False,
  )

  print_comparison_summary(
    results
  )

  print("")
  print(
    f"comparison_results_path="
    f"{arguments.output}"
  )


if __name__ == "__main__":
  main()
