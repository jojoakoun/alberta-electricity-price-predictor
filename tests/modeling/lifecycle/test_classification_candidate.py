import json
from pathlib import Path

import pandas as pd

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.lifecycle.candidate_run import (
  prepare_candidate_run,
  write_json_file,
)
from electricity_predictor.modeling.lifecycle.classification_candidate import (
  train_classification_candidate,
)
from electricity_predictor.modeling.lifecycle.manifest import (
  calculate_dataset_sha256,
)


def build_training_dataset(
  dataset_path: Path,
) -> pd.DataFrame:
  timestamps = pd.date_range(
    start="2026-01-01 00:00:00",
    periods=240,
    freq="h",
  )

  rows = []

  for index, timestamp in enumerate(
    timestamps
  ):
    is_spike = (
      index % 10 == 0
    )

    target_is_spike = (
      (index + 1) % 10 == 0
    )

    actual_price = (
      200.0
      if is_spike
      else 20.0 + (index % 5)
    )

    target_price = (
      200.0
      if target_is_spike
      else 20.0 + ((index + 1) % 5)
    )

    row = {
      "datetime_universal_time":
        timestamp,
      "actual_price":
        actual_price,
      "actual_price_target_1h":
        target_price,
    }

    for feature_index, column in enumerate(
      MODEL_FEATURE_COLUMNS
    ):
      row[column] = float(
        (
          index
          + feature_index
        )
        % 24
      )

    row[
      MODEL_FEATURE_COLUMNS[0]
    ] = float(
      target_is_spike
    )

    if (
      "actual_price_lag_1h"
      in MODEL_FEATURE_COLUMNS
    ):
      row[
        "actual_price_lag_1h"
      ] = actual_price

    rows.append(row)

  data = pd.DataFrame(rows)

  data.to_csv(
    dataset_path,
    index=False,
  )

  return data


def build_split_manifest(
  dataset_path: Path,
  dataset_hash: str,
) -> dict:
  return {
    "schema_version": 1,
    "split_version": (
      "expanding-classification-test"
    ),
    "strategy": "expanding",
    "dataset": {
      "path": str(
        dataset_path
      ),
      "sha256": dataset_hash,
      "version": (
        f"sha256-{dataset_hash[:12]}"
      ),
      "row_count": 240,
      "start_utc": (
        "2026-01-01T00:00:00"
      ),
      "end_utc": (
        "2026-01-10T23:00:00"
      ),
    },
    "plan": {
      "train_start_utc": (
        "2026-01-01T00:00:00"
      ),
      "validation_start_utc": (
        "2026-01-06T00:00:00"
      ),
      "test_start_utc": (
        "2026-01-08T12:00:00"
      ),
      "test_end_utc": (
        "2026-01-10T23:00:00"
      ),
      "purge_hours": 0,
    },
    "splits": {
      "train": {
        "row_count": 120,
        "start_utc": (
          "2026-01-01T00:00:00"
        ),
        "end_utc": (
          "2026-01-05T23:00:00"
        ),
      },
      "validation": {
        "row_count": 60,
        "start_utc": (
          "2026-01-06T00:00:00"
        ),
        "end_utc": (
          "2026-01-08T11:00:00"
        ),
      },
      "test": {
        "row_count": 60,
        "start_utc": (
          "2026-01-08T12:00:00"
        ),
        "end_utc": (
          "2026-01-10T23:00:00"
        ),
      },
    },
  }


def prepare_test_candidate(
  tmp_path: Path,
):
  dataset_path = (
    tmp_path / "training_dataset.csv"
  )

  build_training_dataset(
    dataset_path
  )

  dataset_hash = (
    calculate_dataset_sha256(
      dataset_path
    )
  )

  split_manifest_path = (
    tmp_path / "latest_split.json"
  )

  split_manifest_path.write_text(
    json.dumps(
      build_split_manifest(
        dataset_path=dataset_path,
        dataset_hash=dataset_hash,
      )
    ),
    encoding="utf-8",
  )

  (
    candidate_manifest_path,
    _,
    candidate_manifest,
  ) = prepare_candidate_run(
    split_manifest_path=(
      split_manifest_path
    ),
    candidate_root=(
      tmp_path / "candidates"
    ),
    promotion_mode="manual",
  )

  candidate_manifest[
    "tasks"
  ]["regression"]["status"] = (
    "completed"
  )

  candidate_manifest[
    "status"
  ] = "partially_trained"

  write_json_file(
    content=candidate_manifest,
    file_path=(
      candidate_manifest_path
    ),
  )

  return (
    candidate_manifest_path,
    candidate_manifest,
  )


def test_train_classification_candidate_isolated(
  tmp_path: Path,
):
  (
    candidate_manifest_path,
    candidate_manifest,
  ) = prepare_test_candidate(
    tmp_path
  )

  best_model_path = (
    tmp_path
    / "best_classification_models.csv"
  )

  pd.DataFrame(
    [
      {
        "model_name":
          "logistic_regression",
        "horizon_hours": 1,
        "model_parameters": (
          "C=1.0; "
          "class_weight=balanced; "
          "max_iter=1000"
        ),
        "selection_metric": "f1",
        "selection_rule": (
          "highest_validation_f1_"
          "within_horizon"
        ),
      },
    ]
  ).to_csv(
    best_model_path,
    index=False,
  )

  (
    metadata_path,
    report_path,
    updated_manifest,
  ) = train_classification_candidate(
    candidate_manifest_path=(
      candidate_manifest_path
    ),
    best_model_path=best_model_path,
  )

  metadata = pd.read_csv(
    metadata_path
  )

  report = pd.read_csv(
    report_path
  )

  assert len(metadata) == 1
  assert len(report) == 1

  assert (
    metadata.iloc[0][
      "model_version"
    ]
    == candidate_manifest[
      "model_version"
    ]
  )

  assert (
    metadata.iloc[0][
      "decision_threshold"
    ]
    >= 0
  )

  assert (
    metadata[
      "artifact_path"
    ]
    .str.contains(
      str(
        candidate_manifest[
          "candidate_directory"
        ]
      ),
      regex=False,
    )
    .all()
  )

  assert (
    updated_manifest[
      "tasks"
    ]["classification"][
      "status"
    ]
    == "completed"
  )

  assert (
    updated_manifest[
      "status"
    ]
    == "trained"
  )
