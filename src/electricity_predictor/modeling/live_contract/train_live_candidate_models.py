"""Train and save an isolated candidate bundle for current-hour inference."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
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
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)
from electricity_predictor.modeling.live_contract.regression_validation import (
  load_live_training_dataset,
)
from electricity_predictor.modeling.live_contract.validation_comparison import (
  build_validation_only_splits,
)
from electricity_predictor.contracts.columns import (
  DATETIME_COLUMN,
)


REGRESSION_RESULTS_PATH = Path(
  "reports/live_regression_validation_results.csv"
)

CLASSIFICATION_RESULTS_PATH = Path(
  "reports/live_classification_validation_results.csv"
)

CANDIDATE_ROOT = Path(
  "models/live_candidate"
)

REGRESSION_DIRECTORY = (
  CANDIDATE_ROOT / "regression"
)

CLASSIFICATION_DIRECTORY = (
  CANDIDATE_ROOT / "classification"
)

REGRESSION_METADATA_PATH = (
  CANDIDATE_ROOT
  / "regression_metadata.csv"
)

CLASSIFICATION_METADATA_PATH = (
  CANDIDATE_ROOT
  / "classification_metadata.csv"
)

MANIFEST_PATH = (
  CANDIDATE_ROOT
  / "manifest.json"
)



def load_selected_results(
  path: Path,
  task_name: str,
  required_columns: set[str],
) -> pd.DataFrame:
  """Load one five-horizon validation result table."""
  if not path.exists():
    raise FileNotFoundError(
      f"{task_name} validation results not found: {path}"
    )

  results = pd.read_csv(path)

  missing_columns = (
    required_columns - set(results.columns)
  )

  if missing_columns:
    raise ValueError(
      f"{task_name} results are missing columns: "
      f"{sorted(missing_columns)}"
    )

  horizons = sorted(
    pd.to_numeric(
      results["horizon_hours"],
      errors="raise",
    )
    .astype(int)
    .tolist()
  )

  expected_horizons = list(
    SUPPORTED_FORECAST_HORIZONS_HOURS
  )

  if horizons != expected_horizons:
    raise ValueError(
      f"{task_name} horizons are {horizons}; "
      f"expected {expected_horizons}."
    )

  if set(results["contract"]) != {
    SELECTED_LIVE_FEATURE_CONTRACT
  }:
    raise ValueError(
      f"{task_name} results do not use the selected live contract."
    )

  return (
    results
    .sort_values("horizon_hours")
    .reset_index(drop=True)
  )


def load_final_candidate_training_data() -> pd.DataFrame:
  """Combine train and validation without loading protected test rows."""
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

  final_training_data = pd.concat(
    [
      train_data,
      validation_data,
    ],
    ignore_index=True,
  )

  return (
    final_training_data
    .sort_values(DATETIME_COLUMN)
    .reset_index(drop=True)
  )


def build_regression_model(
  result: dict,
) -> HistGradientBoostingRegressor:
  """Build the validation-selected regressor for one horizon."""
  return HistGradientBoostingRegressor(
    loss="absolute_error",
    learning_rate=float(
      result["learning_rate"]
    ),
    max_iter=int(
      result["max_iter"]
    ),
    max_leaf_nodes=int(
      result["max_leaf_nodes"]
    ),
    min_samples_leaf=int(
      result["min_samples_leaf"]
    ),
    l2_regularization=float(
      result["l2_regularization"]
    ),
    early_stopping=False,
    random_state=42,
  )


def parse_classification_parameters(
  parameter_text: str,
) -> dict:
  """Parse the selected classifier configuration stored during validation."""
  try:
    parameters = json.loads(
      parameter_text
    )
  except json.JSONDecodeError as error:
    raise ValueError(
      "Classification model parameters must contain valid JSON."
    ) from error

  if not isinstance(parameters, dict):
    raise ValueError(
      "Classification model parameters must be a JSON object."
    )

  return parameters


def build_classification_model(
  result: dict,
):
  """Build the validation-selected classifier for one horizon."""
  parameters = (
    parse_classification_parameters(
      result["model_parameters"]
    )
  )

  model_family = parameters[
    "model_family"
  ]

  if model_family == "gradient_boosting":
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

  if model_family == (
    "hist_gradient_boosting"
  ):
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

  raise ValueError(
    f"Unsupported classification model family: {model_family}"
  )


def calculate_sha256(
  path: Path,
) -> str:
  """Return the SHA-256 digest for one saved artifact."""
  return hashlib.sha256(
    path.read_bytes()
  ).hexdigest()


def describe_training_period(
  training_data: pd.DataFrame,
) -> tuple[str, str]:
  """Return normalized training-period boundaries."""
  timestamps = pd.to_datetime(
    training_data[DATETIME_COLUMN],
    utc=True,
    errors="raise",
  )

  return (
    timestamps.min().isoformat(),
    timestamps.max().isoformat(),
  )


def train_regression_candidates(
  training_data: pd.DataFrame,
  results: pd.DataFrame,
  artifact_directory: Path = (
    REGRESSION_DIRECTORY
  ),
) -> list[dict]:
  """Fit and save all five regression candidate artifacts."""
  metadata_rows = []

  training_start, training_end = (
    describe_training_period(
      training_data
    )
  )

  for _, result_row in results.iterrows():
    result = result_row.to_dict()

    horizon = int(
      result["horizon_hours"]
    )

    target_column = (
      f"actual_price_target_{horizon}h"
    )

    model = build_regression_model(
      result
    )

    model.fit(
      training_data[
        SELECTED_LIVE_FEATURE_COLUMNS
      ],
      training_data[target_column],
    )

    artifact_path = (
      artifact_directory
      / f"live_regression_model_{horizon}h.joblib"
    )

    joblib.dump(
      model,
      artifact_path,
    )

    metadata_rows.append({
      "task":
        "regression",
      "contract":
        SELECTED_LIVE_FEATURE_CONTRACT,
      "model_name":
        "hist_gradient_boosting_regressor_tuned",
      "horizon_hours":
        horizon,
      "target_column":
        target_column,
      "artifact_path":
        str(artifact_path),
      "artifact_sha256":
        calculate_sha256(
          artifact_path
        ),
      "training_rows":
        len(training_data),
      "training_start_utc":
        training_start,
      "training_end_utc":
        training_end,
      "feature_count":
        len(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "feature_columns":
        "|".join(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "sklearn_version":
        sklearn.__version__,
      "validation_mae":
        float(
          result["validation_mae"]
        ),
      "validation_rmse":
        float(
          result["validation_rmse"]
        ),
      "learning_rate":
        float(
          result["learning_rate"]
        ),
      "max_iter":
        int(
          result["max_iter"]
        ),
      "max_leaf_nodes":
        int(
          result["max_leaf_nodes"]
        ),
      "min_samples_leaf":
        int(
          result["min_samples_leaf"]
        ),
      "l2_regularization":
        float(
          result["l2_regularization"]
        ),
    })

  return metadata_rows


def train_classification_candidates(
  training_data: pd.DataFrame,
  results: pd.DataFrame,
  artifact_directory: Path = (
    CLASSIFICATION_DIRECTORY
  ),
) -> list[dict]:
  """Fit and save all five classification candidate artifacts."""
  metadata_rows = []

  training_start, training_end = (
    describe_training_period(
      training_data
    )
  )

  for _, result_row in results.iterrows():
    result = result_row.to_dict()

    horizon = int(
      result["horizon_hours"]
    )

    price_target_column = (
      f"actual_price_target_{horizon}h"
    )

    target_column = (
      f"is_spike_target_{horizon}h"
    )

    spike_threshold = float(
      result["spike_threshold"]
    )

    labeled_training_data = (
      training_data.copy()
    )

    labeled_training_data[
      target_column
    ] = (
      labeled_training_data[
        price_target_column
      ]
      > spike_threshold
    ).astype(int)

    if (
      labeled_training_data[
        target_column
      ].nunique()
      != 2
    ):
      raise ValueError(
        f"Classification target {target_column} "
        "must contain both classes."
      )

    model = build_classification_model(
      result
    )

    sample_weight = (
      compute_sample_weight(
        class_weight="balanced",
        y=labeled_training_data[
          target_column
        ],
      )
    )

    model.fit(
      labeled_training_data[
        SELECTED_LIVE_FEATURE_COLUMNS
      ],
      labeled_training_data[
        target_column
      ],
      sample_weight=sample_weight,
    )

    artifact_path = (
      artifact_directory
      / f"live_classification_model_{horizon}h.joblib"
    )

    joblib.dump(
      model,
      artifact_path,
    )

    parameters = (
      parse_classification_parameters(
        result["model_parameters"]
      )
    )

    metadata_rows.append({
      "task":
        "classification",
      "contract":
        SELECTED_LIVE_FEATURE_CONTRACT,
      "model_name":
        result["model_name"],
      "model_family":
        result["model_family"],
      "horizon_hours":
        horizon,
      "target_column":
        target_column,
      "spike_threshold":
        spike_threshold,
      "decision_threshold":
        float(
          result["decision_threshold"]
        ),
      "artifact_path":
        str(artifact_path),
      "artifact_sha256":
        calculate_sha256(
          artifact_path
        ),
      "training_rows":
        len(labeled_training_data),
      "training_start_utc":
        training_start,
      "training_end_utc":
        training_end,
      "feature_count":
        len(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "feature_columns":
        "|".join(
          SELECTED_LIVE_FEATURE_COLUMNS
        ),
      "sklearn_version":
        sklearn.__version__,
      "validation_f1":
        float(
          result["validation_f1"]
        ),
      "validation_pr_auc":
        float(
          result["validation_pr_auc"]
        ),
      "model_parameters":
        json.dumps(
          parameters,
          sort_keys=True,
        ),
    })

  return metadata_rows


def write_manifest(
  regression_metadata: list[dict],
  classification_metadata: list[dict],
  manifest_path: Path = MANIFEST_PATH,
) -> dict:
  """Write one bundle manifest for later worker activation."""
  artifacts = [
    {
      "task":
        row["task"],
      "horizon_hours":
        row["horizon_hours"],
      "artifact_path":
        row["artifact_path"],
      "artifact_sha256":
        row["artifact_sha256"],
    }
    for row in [
      *regression_metadata,
      *classification_metadata,
    ]
  ]

  manifest = {
    "bundle_status":
      "candidate",
    "generated_at_utc":
      datetime.now(
        timezone.utc
      ).isoformat(),
    "selected_live_contract":
      SELECTED_LIVE_FEATURE_CONTRACT,
    "feature_count":
      len(
        SELECTED_LIVE_FEATURE_COLUMNS
      ),
    "feature_columns":
      SELECTED_LIVE_FEATURE_COLUMNS,
    "horizons_hours":
      list(
        SUPPORTED_FORECAST_HORIZONS_HOURS
      ),
    "protected_test_used":
      False,
    "active_registry_modified":
      False,
    "artifact_count":
      len(artifacts),
    "artifacts":
      artifacts,
  }

  manifest_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  manifest_path.write_text(
    json.dumps(
      manifest,
      indent=2,
      sort_keys=True,
    ),
    encoding="utf-8",
  )

  return manifest


def train_live_candidate_model_bundle() -> dict:
  """Build a clean isolated ten-model candidate bundle."""
  regression_results = (
    load_selected_results(
      path=REGRESSION_RESULTS_PATH,
      task_name="Regression",
      required_columns={
        "contract",
        "horizon_hours",
        "validation_mae",
        "validation_rmse",
        "learning_rate",
        "max_iter",
        "max_leaf_nodes",
        "min_samples_leaf",
        "l2_regularization",
      },
    )
  )

  classification_results = (
    load_selected_results(
      path=CLASSIFICATION_RESULTS_PATH,
      task_name="Classification",
      required_columns={
        "contract",
        "horizon_hours",
        "model_family",
        "model_name",
        "model_parameters",
        "spike_threshold",
        "decision_threshold",
        "validation_f1",
        "validation_pr_auc",
      },
    )
  )

  training_data = (
    load_final_candidate_training_data()
  )

  if CANDIDATE_ROOT.exists():
    shutil.rmtree(
      CANDIDATE_ROOT
    )

  REGRESSION_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
  )

  CLASSIFICATION_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
  )

  regression_metadata = (
    train_regression_candidates(
      training_data=training_data,
      results=regression_results,
    )
  )

  classification_metadata = (
    train_classification_candidates(
      training_data=training_data,
      results=classification_results,
    )
  )

  pd.DataFrame(
    regression_metadata
  ).to_csv(
    REGRESSION_METADATA_PATH,
    index=False,
  )

  pd.DataFrame(
    classification_metadata
  ).to_csv(
    CLASSIFICATION_METADATA_PATH,
    index=False,
  )

  manifest = write_manifest(
    regression_metadata=regression_metadata,
    classification_metadata=classification_metadata,
  )

  return {
    "training_rows":
      len(training_data),
    "training_start_utc":
      training_data[
        DATETIME_COLUMN
      ].min(),
    "training_end_utc":
      training_data[
        DATETIME_COLUMN
      ].max(),
    "regression_models":
      len(regression_metadata),
    "classification_models":
      len(classification_metadata),
    "manifest":
      manifest,
  }


def main() -> None:
  """Train and report the isolated candidate model bundle."""
  summary = train_live_candidate_model_bundle()

  print(
    "selected_live_contract="
    f"{SELECTED_LIVE_FEATURE_CONTRACT}"
  )

  print(
    "selected_live_feature_count="
    f"{len(SELECTED_LIVE_FEATURE_COLUMNS)}"
  )

  print(
    "candidate_training_rows="
    f"{summary['training_rows']}"
  )

  print(
    "candidate_training_start_utc="
    f"{summary['training_start_utc']}"
  )

  print(
    "candidate_training_end_utc="
    f"{summary['training_end_utc']}"
  )

  print(
    "regression_candidate_models="
    f"{summary['regression_models']}"
  )

  print(
    "classification_candidate_models="
    f"{summary['classification_models']}"
  )

  print(
    "candidate_artifact_count="
    f"{summary['manifest']['artifact_count']}"
  )

  print(
    f"candidate_manifest={MANIFEST_PATH}"
  )

  print("protected_test_used=False")
  print("active_registry_modified=False")


if __name__ == "__main__":
  main()
