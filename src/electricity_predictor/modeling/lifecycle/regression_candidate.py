from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_engineering import (
  build_target_column_name,
)
from electricity_predictor.modeling.lifecycle.candidate import (
  read_json_file,
  write_json_file,
)
from electricity_predictor.modeling.lifecycle.frozen_splits import (
  load_frozen_candidate_splits,
  resolve_latest_candidate_manifest_path,
)
from electricity_predictor.modeling.regression.baseline.naive_baseline import (
  evaluate_naive_baseline,
)
from electricity_predictor.modeling.regression.final_test_evaluation import (
  load_selected_regression_models,
  train_selected_regression_model,
  evaluate_trained_selected_regression_model,
)
from electricity_predictor.modeling.regression.save_selected_models import (
  build_model_artifact_filename,
  build_model_metadata_row,
  build_naive_baseline_artifact,
  save_model_artifact,
)
from electricity_predictor.modeling.split import (
  DATETIME_COLUMN,
)


BEST_REGRESSION_MODEL_PATH = Path(
  "reports/best_regression_model.csv"
)

CANDIDATE_METADATA_COLUMNS = [
  "model_version",
  "dataset_version",
  "split_version",
  "model_name",
  "horizon_hours",
  "target_column",
  "artifact_path",
  "training_rows",
  "feature_columns",
  "sklearn_version",
  "training_start_utc",
  "training_end_utc",
  "selection_metric",
  "selection_rule",
  "model_parameters",
  "test_rows",
  "test_mae",
  "test_rmse",
]

CANDIDATE_REPORT_COLUMNS = [
  "model_version",
  "dataset_version",
  "split_version",
  "task",
  "model_name",
  "horizon_hours",
  "split",
  "evaluation_rows",
  "mae",
  "rmse",
  "model_parameters",
]


def build_candidate_metadata_row(
  candidate_manifest: dict,
  selected_model: dict,
  target_column: str,
  artifact_path: Path,
  training_data: pd.DataFrame,
  test_rows: int,
  scores: dict[str, float],
) -> dict:
  """Build versioned metadata for one candidate artifact."""
  row = build_model_metadata_row(
    selected_model=selected_model,
    target_column=target_column,
    artifact_path=artifact_path,
    training_rows=len(training_data),
    training_start_utc=str(
      training_data[
        DATETIME_COLUMN
      ].min()
    ),
    training_end_utc=str(
      training_data[
        DATETIME_COLUMN
      ].max()
    ),
  )

  return {
    "model_version": (
      candidate_manifest[
        "model_version"
      ]
    ),
    "dataset_version": (
      candidate_manifest[
        "dataset_version"
      ]
    ),
    "split_version": (
      candidate_manifest[
        "split_version"
      ]
    ),
    **row,
    "test_rows": test_rows,
    "test_mae": scores["mae"],
    "test_rmse": scores["rmse"],
  }


def build_candidate_report_row(
  candidate_manifest: dict,
  selected_model: dict,
  test_rows: int,
  scores: dict[str, float],
) -> dict:
  """Build one lifecycle test result."""
  return {
    "model_version": (
      candidate_manifest[
        "model_version"
      ]
    ),
    "dataset_version": (
      candidate_manifest[
        "dataset_version"
      ]
    ),
    "split_version": (
      candidate_manifest[
        "split_version"
      ]
    ),
    "task": "regression",
    "model_name": (
      selected_model["model_name"]
    ),
    "horizon_hours": int(
      selected_model["horizon_hours"]
    ),
    "split": "lifecycle_test",
    "evaluation_rows": test_rows,
    "mae": scores["mae"],
    "rmse": scores["rmse"],
    "model_parameters": (
      selected_model.get(
        "model_parameters",
        "",
      )
    ),
  }


def update_candidate_status(
  candidate_manifest: dict,
  candidate_manifest_path: Path,
  metadata_path: Path,
  report_path: Path,
) -> dict:
  """Record successful regression candidate training."""
  completed_at = datetime.now(
    UTC
  ).isoformat()

  regression_task = (
    candidate_manifest[
      "tasks"
    ]["regression"]
  )

  regression_task.update(
    {
      "status": "completed",
      "completed_at_utc": completed_at,
      "metadata_path": str(
        metadata_path
      ),
      "report_path": str(
        report_path
      ),
      "selection_source": str(
        BEST_REGRESSION_MODEL_PATH
      ),
      "candidate_kind": (
        "retrained_selected_design"
      ),
    }
  )

  task_statuses = {
    task["status"]
    for task in candidate_manifest[
      "tasks"
    ].values()
  }

  candidate_manifest["status"] = (
    "trained"
    if task_statuses == {"completed"}
    else "partially_trained"
  )

  write_json_file(
    content=candidate_manifest,
    file_path=candidate_manifest_path,
  )

  return candidate_manifest


def train_regression_candidate(
  candidate_manifest_path: Path,
  best_model_path: Path = (
    BEST_REGRESSION_MODEL_PATH
  ),
) -> tuple[Path, Path, dict]:
  """Train selected regression designs in isolation."""
  candidate_manifest = read_json_file(
    candidate_manifest_path
  )

  regression_task = (
    candidate_manifest[
      "tasks"
    ]["regression"]
  )

  metadata_path = Path(
    regression_task[
      "metadata_path"
    ]
  )

  report_path = (
    Path(
      regression_task[
        "report_directory"
      ]
    )
    / "lifecycle_test_results.csv"
  )

  if (
    regression_task["status"]
    == "completed"
    and metadata_path.exists()
    and report_path.exists()
  ):
    return (
      metadata_path,
      report_path,
      candidate_manifest,
    )

  (
    train_data,
    validation_data,
    test_data,
    _,
  ) = load_frozen_candidate_splits(
    candidate_manifest
  )

  final_training_data = pd.concat(
    [
      train_data,
      validation_data,
    ],
    ignore_index=True,
  )

  selected_models = (
    load_selected_regression_models(
      best_model_path
    )
  )

  artifact_directory = Path(
    regression_task[
      "artifact_directory"
    ]
  )

  metadata_rows = []
  report_rows = []

  for selected_model in (
    selected_models.to_dict(
      orient="records"
    )
  ):
    horizon_hours = int(
      selected_model[
        "horizon_hours"
      ]
    )

    target_column = (
      build_target_column_name(
        horizon_hours
      )
    )

    print("")
    print(
      "Regression candidate: "
      f"{horizon_hours}h"
    )
    print("=" * 34)

    print(
      "Model: "
      f"{selected_model['model_name']}"
    )

    if (
      selected_model["model_name"]
      == "naive_baseline"
    ):
      scores = evaluate_naive_baseline(
        data=test_data,
        target_column=target_column,
      )

      artifact = (
        build_naive_baseline_artifact(
          selected_model=selected_model,
          target_column=target_column,
        )
      )
    else:
      artifact = (
        train_selected_regression_model(
          selected_model=selected_model,
          train_data=(
            final_training_data
          ),
          target_column=target_column,
        )
      )

      scores = (
        evaluate_trained_selected_regression_model(
          selected_model=selected_model,
          model=artifact,
          evaluation_data=test_data,
          target_column=target_column,
        )
      )

    artifact_path = (
      artifact_directory
      / build_model_artifact_filename(
        model_name=(
          selected_model[
            "model_name"
          ]
        ),
        horizon_hours=horizon_hours,
      )
    )

    saved_path = save_model_artifact(
      model=artifact,
      output_path=artifact_path,
    )

    metadata_rows.append(
      build_candidate_metadata_row(
        candidate_manifest=(
          candidate_manifest
        ),
        selected_model=selected_model,
        target_column=target_column,
        artifact_path=saved_path,
        training_data=(
          final_training_data
        ),
        test_rows=len(test_data),
        scores=scores,
      )
    )

    report_rows.append(
      build_candidate_report_row(
        candidate_manifest=(
          candidate_manifest
        ),
        selected_model=selected_model,
        test_rows=len(test_data),
        scores=scores,
      )
    )

    print(
      f"MAE: {scores['mae']:.4f}"
    )
    print(
      f"RMSE: {scores['rmse']:.4f}"
    )

  metadata_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  report_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  pd.DataFrame(
    metadata_rows,
    columns=(
      CANDIDATE_METADATA_COLUMNS
    ),
  ).to_csv(
    metadata_path,
    index=False,
  )

  pd.DataFrame(
    report_rows,
    columns=(
      CANDIDATE_REPORT_COLUMNS
    ),
  ).to_csv(
    report_path,
    index=False,
  )

  updated_manifest = (
    update_candidate_status(
      candidate_manifest=(
        candidate_manifest
      ),
      candidate_manifest_path=(
        candidate_manifest_path
      ),
      metadata_path=metadata_path,
      report_path=report_path,
    )
  )

  return (
    metadata_path,
    report_path,
    updated_manifest,
  )


def main() -> None:
  """Train the latest isolated regression candidate."""
  candidate_manifest_path = (
    resolve_latest_candidate_manifest_path()
  )

  (
    metadata_path,
    report_path,
    candidate_manifest,
  ) = train_regression_candidate(
    candidate_manifest_path=(
      candidate_manifest_path
    )
  )

  print("")
  print("Regression candidate complete")
  print("=============================")

  print(
    "Model version: "
    f"{candidate_manifest['model_version']}"
  )

  print(
    "Candidate status: "
    f"{candidate_manifest['status']}"
  )

  print(
    f"Metadata: {metadata_path}"
  )

  print(
    f"Report: {report_path}"
  )


if __name__ == "__main__":
  main()
