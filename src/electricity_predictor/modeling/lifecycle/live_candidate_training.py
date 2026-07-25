"""Train live models inside one isolated lifecycle candidate."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
  SELECTED_LIVE_FEATURE_CONTRACT,
)
from electricity_predictor.modeling.lifecycle.candidate_run import (
  read_json_file,
  write_json_file,
)
from electricity_predictor.modeling.lifecycle.frozen_splits import (
  load_frozen_candidate_splits,
)
from electricity_predictor.modeling.live_contract.live_model_datasets import (
  DATETIME_COLUMN,
)
from electricity_predictor.modeling.live_contract.train_live_candidate_models import (
  CLASSIFICATION_RESULTS_PATH,
  REGRESSION_RESULTS_PATH,
  load_selected_results,
  train_classification_candidates,
  train_regression_candidates,
  write_manifest,
)


REGRESSION_RESULT_COLUMNS = {
  "contract",
  "horizon_hours",
  "validation_mae",
  "validation_rmse",
  "learning_rate",
  "max_iter",
  "max_leaf_nodes",
  "min_samples_leaf",
  "l2_regularization",
}

CLASSIFICATION_RESULT_COLUMNS = {
  "contract",
  "horizon_hours",
  "model_family",
  "model_name",
  "model_parameters",
  "spike_threshold",
  "decision_threshold",
  "validation_f1",
  "validation_pr_auc",
}


def build_final_candidate_training_data(
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
) -> pd.DataFrame:
  """Combine frozen train and validation rows without using test rows."""
  final_training_data = pd.concat(
    [
      train_data,
      validation_data,
    ],
    ignore_index=True,
  )

  return (
    final_training_data
    .sort_values(
      DATETIME_COLUMN
    )
    .reset_index(drop=True)
  )


def validate_final_training_data(
  training_data: pd.DataFrame,
) -> None:
  """Require every selected live feature and future price target."""
  target_columns = [
    f"actual_price_target_{horizon}h"
    for horizon in (
      SUPPORTED_FORECAST_HORIZONS_HOURS
    )
  ]

  required_columns = {
    DATETIME_COLUMN,
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *target_columns,
  }

  missing_columns = (
    required_columns
    - set(training_data.columns)
  )

  if missing_columns:
    raise ValueError(
      "Lifecycle training data is missing columns: "
      f"{sorted(missing_columns)}"
    )

  complete_columns = [
    *SELECTED_LIVE_FEATURE_COLUMNS,
    *target_columns,
  ]

  if training_data[
    complete_columns
  ].isna().any().any():
    raise ValueError(
      "Lifecycle training features and targets "
      "must not contain missing values."
    )


def validate_metadata_rows(
  task_name: str,
  metadata_rows: list[dict],
) -> None:
  """Require all five live models and their saved artifact files."""
  expected_horizons = list(
    SUPPORTED_FORECAST_HORIZONS_HOURS
  )

  observed_horizons = sorted(
    int(
      row["horizon_hours"]
    )
    for row in metadata_rows
  )

  if observed_horizons != expected_horizons:
    raise ValueError(
      f"{task_name} metadata horizons are "
      f"{observed_horizons}; expected "
      f"{expected_horizons}."
    )

  expected_feature_columns = "|".join(
    SELECTED_LIVE_FEATURE_COLUMNS
  )

  for row in metadata_rows:
    if row.get(
      "contract"
    ) != SELECTED_LIVE_FEATURE_CONTRACT:
      raise ValueError(
        f"{task_name} metadata does not use "
        "the selected live feature contract."
      )

    if row.get(
      "feature_columns"
    ) != expected_feature_columns:
      raise ValueError(
        f"{task_name} metadata does not use "
        "the selected live feature columns."
      )

    artifact_path = Path(
      row["artifact_path"]
    )

    if not artifact_path.is_file():
      raise FileNotFoundError(
        f"{task_name} artifact was not created: "
        f"{artifact_path}"
      )


def resolve_completed_candidate_outputs(
  candidate_manifest: dict,
) -> tuple[
  Path,
  Path,
  Path,
] | None:
  """Return existing outputs when candidate training already completed."""
  if candidate_manifest.get(
    "status"
  ) != "trained":
    return None

  tasks = candidate_manifest.get(
    "tasks",
    {},
  )

  if any(
    tasks.get(
      task_name,
      {},
    ).get(
      "status"
    ) != "completed"
    for task_name in (
      "regression",
      "classification",
    )
  ):
    raise ValueError(
      "A trained candidate must have two completed tasks."
    )

  live_training = candidate_manifest.get(
    "live_training",
    {},
  )

  regression_metadata_path = Path(
    tasks[
      "regression"
    ][
      "metadata_path"
    ]
  )

  classification_metadata_path = Path(
    tasks[
      "classification"
    ][
      "metadata_path"
    ]
  )

  bundle_manifest_value = (
    live_training.get(
      "bundle_manifest_path"
    )
  )

  if not bundle_manifest_value:
    raise ValueError(
      "A trained candidate is missing its "
      "live bundle manifest path."
    )

  bundle_manifest_path = Path(
    bundle_manifest_value
  )

  required_paths = (
    regression_metadata_path,
    classification_metadata_path,
    bundle_manifest_path,
  )

  missing_paths = [
    path
    for path in required_paths
    if not path.is_file()
  ]

  if missing_paths:
    raise FileNotFoundError(
      "A trained candidate is missing output files: "
      f"{[str(path) for path in missing_paths]}"
    )

  return required_paths


def validate_candidate_ready_for_training(
  candidate_manifest: dict,
) -> None:
  """Require one newly prepared candidate with two pending tasks."""
  if candidate_manifest.get(
    "status"
  ) != "prepared":
    raise ValueError(
      "Live lifecycle training requires a prepared candidate."
    )

  tasks = candidate_manifest.get(
    "tasks",
    {},
  )

  expected_task_names = {
    "regression",
    "classification",
  }

  if set(
    tasks
  ) != expected_task_names:
    raise ValueError(
      "Candidate manifest must contain regression "
      "and classification tasks."
    )

  for task_name in sorted(
    expected_task_names
  ):
    task = tasks[
      task_name
    ]

    if task.get(
      "status"
    ) != "pending":
      raise ValueError(
        f"Candidate task {task_name} must be pending."
      )

    for required_key in (
      "artifact_directory",
      "metadata_path",
    ):
      if not task.get(
        required_key
      ):
        raise ValueError(
          f"Candidate task {task_name} is missing "
          f"{required_key}."
        )


def mark_candidate_training_completed(
  candidate_manifest: dict,
  candidate_manifest_path: Path,
  regression_results_path: Path,
  classification_results_path: Path,
  regression_metadata: list[dict],
  classification_metadata: list[dict],
  bundle_manifest_path: Path,
  training_data: pd.DataFrame,
) -> dict:
  """Record successful live training after every output is available."""
  completed_at = datetime.now(
    UTC
  ).isoformat()

  task_updates = {
    "regression": {
      "selection_source":
        str(
          regression_results_path
        ),
      "artifact_count":
        len(
          regression_metadata
        ),
    },
    "classification": {
      "selection_source":
        str(
          classification_results_path
        ),
      "artifact_count":
        len(
          classification_metadata
        ),
      "spike_threshold":
        float(
          classification_metadata[
            0
          ][
            "spike_threshold"
          ]
        ),
    },
  }

  for task_name, task_values in (
    task_updates.items()
  ):
    candidate_manifest[
      "tasks"
    ][
      task_name
    ].update({
      "status":
        "completed",
      "completed_at_utc":
        completed_at,
      "candidate_kind":
        "live_selected_contract",
      **task_values,
    })

  candidate_manifest[
    "status"
  ] = "trained"

  candidate_manifest[
    "trained_at_utc"
  ] = completed_at

  candidate_manifest[
    "live_training"
  ] = {
    "status":
      "completed",
    "selected_live_contract":
      SELECTED_LIVE_FEATURE_CONTRACT,
    "feature_count":
      len(
        SELECTED_LIVE_FEATURE_COLUMNS
      ),
    "feature_columns":
      SELECTED_LIVE_FEATURE_COLUMNS,
    "training_rows":
      len(
        training_data
      ),
    "training_start_utc":
      training_data[
        DATETIME_COLUMN
      ].min().isoformat(),
    "training_end_utc":
      training_data[
        DATETIME_COLUMN
      ].max().isoformat(),
    "bundle_manifest_path":
      str(
        bundle_manifest_path
      ),
    "protected_test_used":
      False,
    "active_registry_modified":
      False,
  }

  write_json_file(
    content=candidate_manifest,
    file_path=candidate_manifest_path,
  )

  return candidate_manifest


def train_live_lifecycle_candidate(
  candidate_manifest_path: Path,
  regression_results_path: Path = (
    REGRESSION_RESULTS_PATH
  ),
  classification_results_path: Path = (
    CLASSIFICATION_RESULTS_PATH
  ),
) -> tuple[
  Path,
  Path,
  Path,
  dict,
]:
  """Train all live models inside one lifecycle candidate directory."""
  candidate_manifest = read_json_file(
    candidate_manifest_path
  )

  completed_outputs = (
    resolve_completed_candidate_outputs(
      candidate_manifest
    )
  )

  if completed_outputs is not None:
    (
      regression_metadata_path,
      classification_metadata_path,
      bundle_manifest_path,
    ) = completed_outputs

    return (
      regression_metadata_path,
      classification_metadata_path,
      bundle_manifest_path,
      candidate_manifest,
    )

  validate_candidate_ready_for_training(
    candidate_manifest
  )

  regression_results = (
    load_selected_results(
      path=regression_results_path,
      task_name="Regression",
      required_columns=(
        REGRESSION_RESULT_COLUMNS
      ),
    )
  )

  classification_results = (
    load_selected_results(
      path=classification_results_path,
      task_name="Classification",
      required_columns=(
        CLASSIFICATION_RESULT_COLUMNS
      ),
    )
  )

  if (
    classification_results[
      "spike_threshold"
    ].nunique()
    != 1
  ):
    raise ValueError(
      "Classification results must use one "
      "shared spike threshold."
    )

  (
    train_data,
    validation_data,
    _protected_test_data,
    _split_manifest,
  ) = load_frozen_candidate_splits(
    candidate_manifest
  )

  training_data = (
    build_final_candidate_training_data(
      train_data=train_data,
      validation_data=validation_data,
    )
  )

  validate_final_training_data(
    training_data
  )

  regression_task = (
    candidate_manifest[
      "tasks"
    ][
      "regression"
    ]
  )

  classification_task = (
    candidate_manifest[
      "tasks"
    ][
      "classification"
    ]
  )

  regression_artifact_directory = Path(
    regression_task[
      "artifact_directory"
    ]
  )

  classification_artifact_directory = Path(
    classification_task[
      "artifact_directory"
    ]
  )

  regression_metadata_path = Path(
    regression_task[
      "metadata_path"
    ]
  )

  classification_metadata_path = Path(
    classification_task[
      "metadata_path"
    ]
  )

  bundle_manifest_path = (
    Path(
      candidate_manifest[
        "candidate_directory"
      ]
    )
    / "live_bundle_manifest.json"
  )

  for directory in (
    regression_artifact_directory,
    classification_artifact_directory,
    regression_metadata_path.parent,
    classification_metadata_path.parent,
    bundle_manifest_path.parent,
  ):
    directory.mkdir(
      parents=True,
      exist_ok=True,
    )

  regression_metadata = (
    train_regression_candidates(
      training_data=training_data,
      results=regression_results,
      artifact_directory=(
        regression_artifact_directory
      ),
    )
  )

  classification_metadata = (
    train_classification_candidates(
      training_data=training_data,
      results=classification_results,
      artifact_directory=(
        classification_artifact_directory
      ),
    )
  )

  validate_metadata_rows(
    task_name="Regression",
    metadata_rows=regression_metadata,
  )

  validate_metadata_rows(
    task_name="Classification",
    metadata_rows=classification_metadata,
  )

  pd.DataFrame(
    regression_metadata
  ).to_csv(
    regression_metadata_path,
    index=False,
  )

  pd.DataFrame(
    classification_metadata
  ).to_csv(
    classification_metadata_path,
    index=False,
  )

  write_manifest(
    regression_metadata=regression_metadata,
    classification_metadata=classification_metadata,
    manifest_path=bundle_manifest_path,
  )

  updated_manifest = (
    mark_candidate_training_completed(
      candidate_manifest=(
        candidate_manifest
      ),
      candidate_manifest_path=(
        candidate_manifest_path
      ),
      regression_results_path=(
        regression_results_path
      ),
      classification_results_path=(
        classification_results_path
      ),
      regression_metadata=(
        regression_metadata
      ),
      classification_metadata=(
        classification_metadata
      ),
      bundle_manifest_path=(
        bundle_manifest_path
      ),
      training_data=training_data,
    )
  )

  return (
    regression_metadata_path,
    classification_metadata_path,
    bundle_manifest_path,
    updated_manifest,
  )
