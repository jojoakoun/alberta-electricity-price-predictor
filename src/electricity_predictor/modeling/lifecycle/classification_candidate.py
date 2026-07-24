from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.classification.decision_threshold import (
  apply_decision_threshold,
)
from electricity_predictor.modeling.classification.final_test_evaluation import (
  load_selected_classification_models,
  select_model_decision_threshold,
  train_selected_classification_model,
)
from electricity_predictor.modeling.classification.save_selected_models import (
  build_model_artifact_filename,
  build_model_metadata_row,
  build_naive_spike_baseline_artifact,
  save_model_artifact,
)
from electricity_predictor.modeling.classification.target_builder import (
  build_spike_target_column_name,
  prepare_classification_splits,
)
from electricity_predictor.modeling.lifecycle.candidate_run import (
  read_json_file,
  write_json_file,
)
from electricity_predictor.modeling.lifecycle.frozen_splits import (
  load_frozen_candidate_splits,
  resolve_latest_candidate_manifest_path,
)
from electricity_predictor.modeling.metrics import (
  calculate_classification_metrics,
)
from electricity_predictor.modeling.split import (
  DATETIME_COLUMN,
)


BEST_CLASSIFICATION_MODEL_PATH = Path(
  "reports/best_classification_model.csv"
)

CANDIDATE_METADATA_COLUMNS = [
  "model_version",
  "dataset_version",
  "split_version",
  "model_name",
  "horizon_hours",
  "target_column",
  "spike_threshold",
  "decision_threshold",
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
  "test_accuracy",
  "test_precision",
  "test_recall",
  "test_f1",
  "test_pr_auc",
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
  "spike_threshold",
  "decision_threshold",
  "accuracy",
  "precision",
  "recall",
  "f1",
  "pr_auc",
  "model_parameters",
]


def evaluate_naive_candidate(
  selected_model: dict,
  evaluation_data: pd.DataFrame,
  target_column: str,
  spike_threshold: float,
) -> tuple[
  dict[str, float | None],
  pd.Series,
  None,
  dict,
]:
  """Evaluate and build one naive classification artifact."""
  prediction = (
    evaluation_data[
      "actual_price_lag_1h"
    ]
    > spike_threshold
  ).astype(int)

  scores = calculate_classification_metrics(
    target=evaluation_data[
      target_column
    ],
    prediction=prediction,
  )

  artifact = (
    build_naive_spike_baseline_artifact(
      selected_model=selected_model,
      target_column=target_column,
      threshold=spike_threshold,
    )
  )

  return (
    scores,
    prediction,
    None,
    artifact,
  )


def evaluate_learned_candidate(
  selected_model: dict,
  train_data: pd.DataFrame,
  validation_data: pd.DataFrame,
  test_data: pd.DataFrame,
  target_column: str,
) -> tuple[
  dict[str, float | None],
  pd.Series,
  float,
  object,
]:
  """Select a validation cutoff and evaluate one learned candidate."""
  threshold_result = (
    select_model_decision_threshold(
      selected_model=selected_model,
      train_data=train_data,
      validation_data=validation_data,
      target_column=target_column,
    )
  )

  decision_threshold = float(
    threshold_result[
      "decision_threshold"
    ]
  )

  final_training_data = pd.concat(
    [
      train_data,
      validation_data,
    ],
    ignore_index=True,
  )

  model = train_selected_classification_model(
    selected_model=selected_model,
    train_data=final_training_data,
    target_column=target_column,
  )

  test_features = test_data[
    MODEL_FEATURE_COLUMNS
  ]

  probability = pd.Series(
    model.predict_proba(
      test_features
    )[:, 1],
    index=test_data.index,
  )

  prediction = pd.Series(
    apply_decision_threshold(
      probability=probability,
      threshold=decision_threshold,
    ),
    index=test_data.index,
  )

  scores = calculate_classification_metrics(
    target=test_data[target_column],
    prediction=prediction,
    probability=probability,
  )

  return (
    scores,
    prediction,
    decision_threshold,
    model,
  )


def build_candidate_metadata_row(
  candidate_manifest: dict,
  selected_model: dict,
  target_column: str,
  spike_threshold: float,
  decision_threshold: float | None,
  artifact_path: Path,
  training_data: pd.DataFrame,
  test_rows: int,
  scores: dict[str, float | None],
) -> dict:
  """Build versioned metadata for one classification artifact."""
  row = build_model_metadata_row(
    selected_model=selected_model,
    target_column=target_column,
    threshold=spike_threshold,
    decision_threshold=decision_threshold,
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
    "test_accuracy": scores.get(
      "accuracy"
    ),
    "test_precision": scores.get(
      "precision"
    ),
    "test_recall": scores.get(
      "recall"
    ),
    "test_f1": scores.get(
      "f1"
    ),
    "test_pr_auc": scores.get(
      "pr_auc"
    ),
  }


def build_candidate_report_row(
  candidate_manifest: dict,
  selected_model: dict,
  spike_threshold: float,
  decision_threshold: float | None,
  test_rows: int,
  scores: dict[str, float | None],
) -> dict:
  """Build one lifecycle classification result."""
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
    "task": "classification",
    "model_name": (
      selected_model[
        "model_name"
      ]
    ),
    "horizon_hours": int(
      selected_model[
        "horizon_hours"
      ]
    ),
    "split": "lifecycle_test",
    "evaluation_rows": test_rows,
    "spike_threshold": (
      spike_threshold
    ),
    "decision_threshold": (
      decision_threshold
    ),
    "accuracy": scores.get(
      "accuracy"
    ),
    "precision": scores.get(
      "precision"
    ),
    "recall": scores.get(
      "recall"
    ),
    "f1": scores.get(
      "f1"
    ),
    "pr_auc": scores.get(
      "pr_auc"
    ),
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
  spike_threshold: float,
) -> dict:
  """Record successful classification candidate training."""
  completed_at = datetime.now(
    UTC
  ).isoformat()

  classification_task = (
    candidate_manifest[
      "tasks"
    ]["classification"]
  )

  classification_task.update(
    {
      "status": "completed",
      "completed_at_utc": (
        completed_at
      ),
      "metadata_path": str(
        metadata_path
      ),
      "report_path": str(
        report_path
      ),
      "selection_source": str(
        BEST_CLASSIFICATION_MODEL_PATH
      ),
      "candidate_kind": (
        "retrained_selected_design"
      ),
      "spike_threshold": (
        spike_threshold
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
    if task_statuses == {
      "completed"
    }
    else "partially_trained"
  )

  write_json_file(
    content=candidate_manifest,
    file_path=(
      candidate_manifest_path
    ),
  )

  return candidate_manifest


def train_classification_candidate(
  candidate_manifest_path: Path,
  best_model_path: Path = (
    BEST_CLASSIFICATION_MODEL_PATH
  ),
) -> tuple[Path, Path, dict]:
  """Train selected classification designs in isolation."""
  candidate_manifest = read_json_file(
    candidate_manifest_path
  )

  classification_task = (
    candidate_manifest[
      "tasks"
    ]["classification"]
  )

  metadata_path = Path(
    classification_task[
      "metadata_path"
    ]
  )

  report_path = (
    Path(
      classification_task[
        "report_directory"
      ]
    )
    / "lifecycle_test_results.csv"
  )

  if (
    classification_task[
      "status"
    ]
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

  selected_models = (
    load_selected_classification_models(
      best_model_path
    )
  )

  horizons_hours = sorted(
    selected_models[
      "horizon_hours"
    ]
    .astype(int)
    .tolist()
  )

  (
    prepared_train,
    prepared_validation,
    prepared_test,
    spike_threshold,
  ) = prepare_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
    test_data=test_data,
    horizons_hours=horizons_hours,
  )

  final_training_data = pd.concat(
    [
      prepared_train,
      prepared_validation,
    ],
    ignore_index=True,
  )

  artifact_directory = Path(
    classification_task[
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
      build_spike_target_column_name(
        horizon_hours
      )
    )

    print("")
    print(
      "Classification candidate: "
      f"{horizon_hours}h"
    )
    print("=" * 38)

    print(
      "Model: "
      f"{selected_model['model_name']}"
    )

    if (
      selected_model[
        "model_name"
      ]
      == "naive_spike_baseline"
    ):
      (
        scores,
        _,
        decision_threshold,
        artifact,
      ) = evaluate_naive_candidate(
        selected_model=selected_model,
        evaluation_data=(
          prepared_test
        ),
        target_column=target_column,
        spike_threshold=(
          spike_threshold
        ),
      )
    else:
      (
        scores,
        _,
        decision_threshold,
        artifact,
      ) = evaluate_learned_candidate(
        selected_model=selected_model,
        train_data=prepared_train,
        validation_data=(
          prepared_validation
        ),
        test_data=prepared_test,
        target_column=target_column,
      )

    artifact_path = (
      artifact_directory
      / build_model_artifact_filename(
        model_name=(
          selected_model[
            "model_name"
          ]
        ),
        horizon_hours=(
          horizon_hours
        ),
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
        spike_threshold=(
          spike_threshold
        ),
        decision_threshold=(
          decision_threshold
        ),
        artifact_path=saved_path,
        training_data=(
          final_training_data
        ),
        test_rows=len(
          prepared_test
        ),
        scores=scores,
      )
    )

    report_rows.append(
      build_candidate_report_row(
        candidate_manifest=(
          candidate_manifest
        ),
        selected_model=selected_model,
        spike_threshold=(
          spike_threshold
        ),
        decision_threshold=(
          decision_threshold
        ),
        test_rows=len(
          prepared_test
        ),
        scores=scores,
      )
    )

    print(
      "Spike threshold: "
      f"{spike_threshold:.4f}"
    )

    if decision_threshold is not None:
      print(
        "Decision threshold: "
        f"{decision_threshold:.4f}"
      )

    print(
      f"Precision: "
      f"{scores['precision']:.4f}"
    )

    print(
      f"Recall: "
      f"{scores['recall']:.4f}"
    )

    print(
      f"F1: "
      f"{scores['f1']:.4f}"
    )

    print(
      f"PR-AUC: "
      f"{scores.get('pr_auc', 0.0):.4f}"
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
      spike_threshold=(
        spike_threshold
      ),
    )
  )

  return (
    metadata_path,
    report_path,
    updated_manifest,
  )


def main() -> None:
  """Train the latest isolated classification candidate."""
  candidate_manifest_path = (
    resolve_latest_candidate_manifest_path()
  )

  (
    metadata_path,
    report_path,
    candidate_manifest,
  ) = train_classification_candidate(
    candidate_manifest_path=(
      candidate_manifest_path
    )
  )

  print("")
  print(
    "Classification candidate complete"
  )
  print(
    "================================="
  )

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
