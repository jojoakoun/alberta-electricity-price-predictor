import json
from pathlib import Path

import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  MODEL_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.lifecycle.candidate import (
  prepare_candidate_run,
)
from electricity_predictor.modeling.lifecycle.manifest import (
  calculate_dataset_sha256,
)
from electricity_predictor.modeling.lifecycle.regression_candidate import (
  load_frozen_candidate_splits,
  train_regression_candidate,
)


def build_training_dataset(
  dataset_path: Path,
) -> pd.DataFrame:
  timestamps = pd.date_range(
    start="2026-01-01 00:00:00",
    periods=96,
    freq="h",
  )

  rows = []

  for index, timestamp in enumerate(
    timestamps
  ):
    actual_price = 30.0 + index

    row = {
      "datetime_universal_time":
        timestamp,
      "actual_price":
        actual_price,
      "actual_price_target_1h":
        actual_price + 1,
      "actual_price_target_3h":
        actual_price + 3,
    }

    for feature_index, column in enumerate(
      MODEL_FEATURE_COLUMNS
    ):
      row[column] = (
        float(index + feature_index + 1)
      )

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
    "split_version": "expanding-test-001",
    "strategy": "expanding",
    "dataset": {
      "path": str(dataset_path),
      "sha256": dataset_hash,
      "version": (
        f"sha256-{dataset_hash[:12]}"
      ),
      "row_count": 96,
      "start_utc": (
        "2026-01-01T00:00:00"
      ),
      "end_utc": (
        "2026-01-04T23:00:00"
      ),
    },
    "plan": {
      "train_start_utc": (
        "2026-01-01T00:00:00"
      ),
      "validation_start_utc": (
        "2026-01-03T00:00:00"
      ),
      "test_start_utc": (
        "2026-01-04T00:00:00"
      ),
      "test_end_utc": (
        "2026-01-04T23:00:00"
      ),
      "purge_hours": 0,
    },
    "splits": {
      "train": {
        "row_count": 48,
        "start_utc": (
          "2026-01-01T00:00:00"
        ),
        "end_utc": (
          "2026-01-02T23:00:00"
        ),
      },
      "validation": {
        "row_count": 24,
        "start_utc": (
          "2026-01-03T00:00:00"
        ),
        "end_utc": (
          "2026-01-03T23:00:00"
        ),
      },
      "test": {
        "row_count": 24,
        "start_utc": (
          "2026-01-04T00:00:00"
        ),
        "end_utc": (
          "2026-01-04T23:00:00"
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

  return (
    dataset_path,
    candidate_manifest_path,
    candidate_manifest,
  )


def test_train_regression_candidate_isolated(
  tmp_path: Path,
):
  (
    _,
    candidate_manifest_path,
    candidate_manifest,
  ) = prepare_test_candidate(
    tmp_path
  )

  best_model_path = (
    tmp_path / "best_models.csv"
  )

  pd.DataFrame(
    [
      {
        "model_name":
          "linear_regression",
        "horizon_hours": 1,
        "model_parameters":
          "fit_intercept=True",
        "selection_metric": "mae",
        "selection_rule":
          "lowest_validation_mae_within_horizon",
      },
      {
        "model_name":
          "naive_baseline",
        "horizon_hours": 3,
        "model_parameters":
          "prediction_column=actual_price_lag_1h",
        "selection_metric": "mae",
        "selection_rule":
          "lowest_validation_mae_within_horizon",
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
  ) = train_regression_candidate(
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

  assert len(metadata) == 2
  assert len(report) == 2

  assert (
    metadata["model_version"]
    .eq(
      candidate_manifest[
        "model_version"
      ]
    )
    .all()
  )

  assert (
    metadata["artifact_path"]
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
    ]["regression"]["status"]
    == "completed"
  )

  assert (
    updated_manifest["status"]
    == "partially_trained"
  )


def test_candidate_rejects_changed_dataset(
  tmp_path: Path,
):
  (
    dataset_path,
    candidate_manifest_path,
    _,
  ) = prepare_test_candidate(
    tmp_path
  )

  dataset_path.write_text(
    dataset_path.read_text(
      encoding="utf-8"
    )
    + "\n",
    encoding="utf-8",
  )

  candidate_manifest = json.loads(
    candidate_manifest_path.read_text(
      encoding="utf-8"
    )
  )

  with pytest.raises(
    ValueError,
    match="hash no longer matches",
  ):
    load_frozen_candidate_splits(
      candidate_manifest
    )
