"""Tune and evaluate live-contract regression models on validation only."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.ensemble import (
  HistGradientBoostingRegressor,
)
from sklearn.model_selection import (
  TimeSeriesSplit,
)

from electricity_predictor.config import (
  load_configuration,
)
from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)
from electricity_predictor.modeling.live_contract.validation_comparison import (
  build_validation_only_splits,
)
from electricity_predictor.modeling.metrics import (
  mean_absolute_error_value,
  root_mean_squared_error_value,
)
from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting import (
  HIST_GRADIENT_BOOSTING_EARLY_STOPPING,
  HIST_GRADIENT_BOOSTING_LOSS,
  HIST_GRADIENT_BOOSTING_RANDOM_STATE,
)
from electricity_predictor.modeling.regression.hist_gradient_boosting.hist_gradient_boosting_tuning import (
  HIST_GRADIENT_BOOSTING_CONFIGS,
)
from electricity_predictor.modeling.split import (
  get_time_series_cv_gap_hours,
)


LIVE_TRAINING_DATASET_PATH = Path(
  "data/processed/live_training_dataset.csv"
)

DATETIME_COLUMN = "datetime_universal_time"
CV_SPLITS = 3


def load_live_training_dataset(
  path: Path = LIVE_TRAINING_DATASET_PATH,
) -> pd.DataFrame:
  """Load the selected-contract dataset in chronological order."""
  if not path.exists():
    raise FileNotFoundError(
      f"Live training dataset not found: {path}"
    )

  data = pd.read_csv(path)

  required_columns = {
    DATETIME_COLUMN,
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *[
      f"actual_price_target_{horizon}h"
      for horizon in SUPPORTED_FORECAST_HORIZONS_HOURS
    ],
  }

  missing_columns = (
    required_columns - set(data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Live training dataset is missing columns: "
      f"{sorted(missing_columns)}"
    )

  data[DATETIME_COLUMN] = pd.to_datetime(
    data[DATETIME_COLUMN],
    utc=True,
    errors="raise",
  )

  return (
    data
    .sort_values(DATETIME_COLUMN)
    .reset_index(drop=True)
  )


def build_regression_model(
  config: dict,
) -> HistGradientBoostingRegressor:
  """Build one candidate using the established regression search space."""
  return HistGradientBoostingRegressor(
    loss=HIST_GRADIENT_BOOSTING_LOSS,
    learning_rate=float(
      config["learning_rate"]
    ),
    max_iter=int(
      config["max_iter"]
    ),
    max_leaf_nodes=int(
      config["max_leaf_nodes"]
    ),
    min_samples_leaf=int(
      config["min_samples_leaf"]
    ),
    l2_regularization=float(
      config["l2_regularization"]
    ),
    early_stopping=(
      HIST_GRADIENT_BOOSTING_EARLY_STOPPING
    ),
    random_state=(
      HIST_GRADIENT_BOOSTING_RANDOM_STATE
    ),
  )


def evaluate_configuration_with_cv(
  train_data: pd.DataFrame,
  target_column: str,
  config: dict,
  gap_hours: int,
  n_splits: int = CV_SPLITS,
) -> dict:
  """Evaluate one configuration with leakage-safe chronological CV."""
  splitter = TimeSeriesSplit(
    n_splits=n_splits,
    gap=gap_hours,
  )

  fold_mae = []
  fold_rmse = []

  for (
    fold_number,
    (
      fold_train_index,
      fold_validation_index,
    ),
  ) in enumerate(
    splitter.split(train_data),
    start=1,
  ):
    fold_train = train_data.iloc[
      fold_train_index
    ]

    fold_validation = train_data.iloc[
      fold_validation_index
    ]

    model = build_regression_model(
      config
    )

    model.fit(
      fold_train[
        SELECTED_LIVE_FEATURE_COLUMNS
      ],
      fold_train[target_column],
    )

    predictions = model.predict(
      fold_validation[
        SELECTED_LIVE_FEATURE_COLUMNS
      ]
    )

    fold_mae.append(
      mean_absolute_error_value(
        fold_validation[target_column],
        predictions,
      )
    )

    fold_rmse.append(
      root_mean_squared_error_value(
        fold_validation[target_column],
        predictions,
      )
    )

    print(
      f"    fold={fold_number} "
      f"mae={fold_mae[-1]:.6f} "
      f"rmse={fold_rmse[-1]:.6f}"
    )

  return {
    "cv_mae": (
      sum(fold_mae) / len(fold_mae)
    ),
    "cv_rmse": (
      sum(fold_rmse) / len(fold_rmse)
    ),
  }


def select_best_configuration(
  results: list[dict],
) -> dict:
  """Select lowest CV MAE, then RMSE, with deterministic tie-breaking."""
  if not results:
    raise ValueError(
      "Regression tuning produced no results."
    )

  return sorted(
    results,
    key=lambda result: (
      result["cv_mae"],
      result["cv_rmse"],
      result["learning_rate"],
      result["max_iter"],
      result["max_leaf_nodes"],
      result["min_samples_leaf"],
      result["l2_regularization"],
    ),
  )[0]


def tune_horizon(
  train_data: pd.DataFrame,
  target_column: str,
  gap_hours: int,
) -> dict:
  """Tune one horizon using only chronological training rows."""
  tuning_results = []

  for config_number, config in enumerate(
    HIST_GRADIENT_BOOSTING_CONFIGS,
    start=1,
  ):
    print(
      f"  configuration={config_number} "
      f"learning_rate={config['learning_rate']} "
      f"max_iter={config['max_iter']} "
      f"max_leaf_nodes={config['max_leaf_nodes']} "
      f"min_samples_leaf={config['min_samples_leaf']} "
      f"l2_regularization={config['l2_regularization']}"
    )

    cv_scores = evaluate_configuration_with_cv(
      train_data=train_data,
      target_column=target_column,
      config=config,
      gap_hours=gap_hours,
    )

    tuning_results.append({
      **config,
      **cv_scores,
    })

  return select_best_configuration(
    tuning_results
  )


def evaluate_horizon(
  horizon_hours: int,
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  gap_hours: int,
) -> dict:
  """Tune on train and evaluate the selected configuration on validation."""
  target_column = (
    f"actual_price_target_{horizon_hours}h"
  )

  print("")
  print(
    f"HORIZON {horizon_hours}H"
  )
  print("=" * 40)

  best_result = tune_horizon(
    train_data=train_data,
    target_column=target_column,
    gap_hours=gap_hours,
  )

  selected_config = {
    key: best_result[key]
    for key in [
      "learning_rate",
      "max_iter",
      "max_leaf_nodes",
      "min_samples_leaf",
      "l2_regularization",
    ]
  }

  model = build_regression_model(
    selected_config
  )

  model.fit(
    train_data[
      SELECTED_LIVE_FEATURE_COLUMNS
    ],
    train_data[target_column],
  )

  validation_predictions = model.predict(
    validation_data[
      SELECTED_LIVE_FEATURE_COLUMNS
    ]
  )

  validation_mae = (
    mean_absolute_error_value(
      validation_data[target_column],
      validation_predictions,
    )
  )

  validation_rmse = (
    root_mean_squared_error_value(
      validation_data[target_column],
      validation_predictions,
    )
  )

  print(
    f"selected_cv_mae="
    f"{best_result['cv_mae']:.6f}"
  )

  print(
    f"selected_cv_rmse="
    f"{best_result['cv_rmse']:.6f}"
  )

  print(
    f"validation_mae="
    f"{validation_mae:.6f}"
  )

  print(
    f"validation_rmse="
    f"{validation_rmse:.6f}"
  )

  return {
    "contract":
      SELECTED_LIVE_FEATURE_CONTRACT,
    "model_name":
      "hist_gradient_boosting_regressor_tuned",
    "horizon_hours":
      horizon_hours,
    "target_column":
      target_column,
    "feature_count":
      len(SELECTED_LIVE_FEATURE_COLUMNS),
    "train_rows":
      len(train_data),
    "validation_rows":
      len(validation_data),
    "cv_splits":
      CV_SPLITS,
    "cv_gap_hours":
      gap_hours,
    "learning_rate":
      selected_config["learning_rate"],
    "max_iter":
      selected_config["max_iter"],
    "max_leaf_nodes":
      selected_config["max_leaf_nodes"],
    "min_samples_leaf":
      selected_config["min_samples_leaf"],
    "l2_regularization":
      selected_config["l2_regularization"],
    "cv_mae":
      best_result["cv_mae"],
    "cv_rmse":
      best_result["cv_rmse"],
    "validation_mae":
      validation_mae,
    "validation_rmse":
      validation_rmse,
  }


def run_live_regression_validation() -> pd.DataFrame:
  """Run validation-only regression tuning for all supported horizons."""
  configuration = load_configuration()
  modeling_config = configuration[
    "modeling"
  ]

  dataset = load_live_training_dataset()

  train_data, validation_data = (
    build_validation_only_splits(
      data=dataset,
      modeling_config=modeling_config,
    )
  )

  gap_hours = (
    get_time_series_cv_gap_hours(
      modeling_config
    )
  )

  results = []

  for horizon_hours in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    results.append(
      evaluate_horizon(
        horizon_hours=horizon_hours,
        train_data=train_data,
        validation_data=validation_data,
        gap_hours=gap_hours,
      )
    )

  return pd.DataFrame(results)


def print_summary(
  results: pd.DataFrame,
) -> None:
  """Print the validation results in horizon order."""
  print("")
  print("LIVE REGRESSION VALIDATION SUMMARY")
  print("==================================")

  columns = [
    "horizon_hours",
    "train_rows",
    "validation_rows",
    "cv_mae",
    "cv_rmse",
    "validation_mae",
    "validation_rmse",
    "learning_rate",
    "max_iter",
    "max_leaf_nodes",
    "min_samples_leaf",
    "l2_regularization",
  ]

  print(
    results[columns]
    .sort_values(
      "horizon_hours"
    )
    .to_string(
      index=False,
      float_format=lambda value:
        f"{value:.6f}",
    )
  )

  print("")
  print(
    "selected_live_contract="
    f"{SELECTED_LIVE_FEATURE_CONTRACT}"
  )

  print(
    "selected_live_feature_count="
    f"{len(SELECTED_LIVE_FEATURE_COLUMNS)}"
  )

  print("protected_test_used=False")
  print("models_saved=False")
  print("active_registry_modified=False")


def main() -> None:
  """Run validation and write its isolated result table."""
  parser = argparse.ArgumentParser()

  parser.add_argument(
    "--output",
    required=True,
    type=Path,
  )

  arguments = parser.parse_args()

  results = run_live_regression_validation()

  arguments.output.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  results.to_csv(
    arguments.output,
    index=False,
  )

  print_summary(
    results
  )

  print("")
  print(
    f"validation_results_path="
    f"{arguments.output}"
  )


if __name__ == "__main__":
  main()
