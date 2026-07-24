from datetime import UTC, datetime
import json
from pathlib import Path

import pytest

from electricity_predictor.modeling.lifecycle import (
  model_retraining_scheduler,
)


def make_configuration() -> dict:
  return {
    "model_lifecycle": {
      "retraining_interval_days": 90,
      "promotion_mode": "manual",
    }
  }


def test_schedule_is_due_without_previous_run():
  schedule = (
    model_retraining_scheduler.calculate_lifecycle_schedule(
      state=None,
      interval_days=90,
      now_utc=datetime(
        2026,
        7,
        20,
        tzinfo=UTC,
      ),
    )
  )

  assert schedule["due"] is True
  assert (
    schedule[
      "last_completed_at_utc"
    ]
    is None
  )


def test_schedule_waits_until_ninety_days():
  schedule = (
    model_retraining_scheduler.calculate_lifecycle_schedule(
      state={
        "last_completed_at_utc": (
          "2026-07-20T18:00:00+00:00"
        )
      },
      interval_days=90,
      now_utc=datetime(
        2026,
        8,
        20,
        tzinfo=UTC,
      ),
    )
  )

  assert schedule["due"] is False

  assert schedule[
    "next_due_at_utc"
  ].startswith(
    "2026-10-18"
  )


def test_build_state_from_existing_candidate(
  tmp_path: Path,
):
  candidate_directory = (
    tmp_path / "candidate"
  )

  comparison_directory = (
    candidate_directory
    / "reports"
    / "comparison"
  )

  comparison_directory.mkdir(
    parents=True
  )

  candidate_manifest_path = (
    candidate_directory
    / "candidate_manifest.json"
  )

  candidate_manifest_path.write_text(
    json.dumps(
      {
        "status": "evaluated",
        "model_version": (
          "candidate-test"
        ),
        "split_version": (
          "split-test"
        ),
        "promotion_mode": "manual",
        "candidate_directory": str(
          candidate_directory
        ),
      }
    ),
    encoding="utf-8",
  )

  (
    comparison_directory
    / "promotion_summary.json"
  ).write_text(
    json.dumps(
      {
        "evaluated_at_utc": (
          "2026-07-20T18:00:00+00:00"
        ),
        "regression_gate_pass": True,
        "classification_gate_pass": False,
      }
    ),
    encoding="utf-8",
  )

  state = model_retraining_scheduler.build_state_from_candidate(
    candidate_manifest_path
  )

  assert state is not None

  assert state[
    "last_completed_at_utc"
  ] == "2026-07-20T18:00:00+00:00"

  assert (
    state["model_version"]
    == "candidate-test"
  )


def test_runner_skips_before_interval(
  tmp_path: Path,
  monkeypatch,
):
  state_path = (
    tmp_path / "state.json"
  )

  model_retraining_scheduler.write_lifecycle_state(
    state={
      "last_completed_at_utc": (
        "2026-07-20T18:00:00+00:00"
      ),
      "model_version": "candidate-test",
    },
    state_path=state_path,
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "load_configuration",
    make_configuration,
  )

  def reject_preparation():
    raise AssertionError(
      "Training must not run before it is due."
    )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "prepare_lifecycle_training_data",
    reject_preparation,
  )

  result = model_retraining_scheduler.run_scheduled_model_retraining(
    now_utc=datetime(
      2026,
      8,
      20,
      tzinfo=UTC,
    ),
    state_path=state_path,
  )

  assert result[
    "status"
  ] == "skipped"


def test_runner_executes_steps_without_promotion(
  tmp_path,
  monkeypatch,
):
  from datetime import UTC, datetime

  from electricity_predictor.modeling.lifecycle import (
    model_retraining_scheduler as scheduler,
  )

  calls = []

  monkeypatch.setattr(
    scheduler,
    "load_configuration",
    lambda: {
      "model_lifecycle": {
        "retraining_interval_days": 30,
        "promotion_mode": "manual",
      },
    },
  )

  monkeypatch.setattr(
    scheduler,
    "resolve_lifecycle_state",
    lambda state_path: None,
  )

  monkeypatch.setattr(
    scheduler,
    "prepare_lifecycle_training_data",
    lambda: calls.append(
      "prepare_source_data"
    ),
  )

  monkeypatch.setattr(
    scheduler,
    "build_and_save_champion_challenger_datasets",
    lambda: calls.append(
      "build_comparison_dataset"
    ),
  )

  monkeypatch.setattr(
    scheduler,
    "materialize_lifecycle_manifest",
    lambda: calls.append(
      "materialize_manifest"
    ),
  )

  candidate_manifest_path = (
    tmp_path
    / "candidate_manifest.json"
  )

  candidate_manifest = {
    "candidate_directory":
      str(
        tmp_path
        / "candidate"
      ),
    "model_version":
      "candidate-v1",
    "split_version":
      "split-v1",
  }

  monkeypatch.setattr(
    scheduler,
    "prepare_candidate_run",
    lambda **kwargs: (
      candidate_manifest_path,
      tmp_path / "split_manifest.json",
      candidate_manifest,
    ),
  )

  monkeypatch.setattr(
    scheduler,
    "train_live_lifecycle_candidate",
    lambda candidate_manifest_path: (
      calls.append(
        "train_live_candidate"
      )
    ),
  )

  monkeypatch.setattr(
    scheduler,
    "compare_challenger_with_active_models",
    lambda candidate_manifest_path: (
      calls.append(
        "compare_candidate"
      )
    ),
  )

  evaluated_manifest = {
    "status":
      "evaluated",
    "model_version":
      "candidate-v1",
    "split_version":
      "split-v1",
  }

  monkeypatch.setattr(
    scheduler,
    "read_json_file",
    lambda path: evaluated_manifest,
  )

  promotion_summary_path = (
    tmp_path
    / "promotion_summary.json"
  )

  promotion_summary = {
    "evaluated_at_utc":
      "2026-07-24T15:00:00+00:00",
    "regression_gate_pass":
      True,
    "classification_gate_pass":
      True,
    "promotion_ready":
      True,
  }

  monkeypatch.setattr(
    scheduler,
    "load_promotion_summary",
    lambda manifest: (
      promotion_summary_path,
      promotion_summary,
    ),
  )

  result = (
    scheduler.run_scheduled_model_retraining(
      force=True,
      now_utc=datetime(
        2026,
        7,
        24,
        14,
        0,
        tzinfo=UTC,
      ),
      state_path=(
        tmp_path
        / "lifecycle_state.json"
      ),
    )
  )

  assert calls == [
    "prepare_source_data",
    "build_comparison_dataset",
    "materialize_manifest",
    "train_live_candidate",
    "compare_candidate",
  ]

  assert result[
    "status"
  ] == "completed"

  assert result[
    "model_version"
  ] == "candidate-v1"

  assert result[
    "promotion_ready"
  ] is True

  assert result[
    "automatic_promotion_performed"
  ] is False



def test_runner_rejects_automatic_promotion(
  monkeypatch,
):
  monkeypatch.setattr(
    model_retraining_scheduler,
    "load_configuration",
    lambda: {
      "model_lifecycle": {
        "retraining_interval_days": 90,
        "promotion_mode": "automatic",
      }
    },
  )

  with pytest.raises(
    ValueError,
    match="promotion_mode: manual",
  ):
    model_retraining_scheduler.run_scheduled_model_retraining(
      force=True
    )
