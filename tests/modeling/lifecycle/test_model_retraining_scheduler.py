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
  tmp_path: Path,
  monkeypatch,
):
  calls = []

  state_path = (
    tmp_path / "state.json"
  )

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

  candidate_manifest = {
    "status": "pending",
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

  candidate_manifest_path.write_text(
    json.dumps(
      candidate_manifest
    ),
    encoding="utf-8",
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "load_configuration",
    make_configuration,
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "discover_latest_candidate_state",
    lambda: None,
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "prepare_lifecycle_training_data",
    lambda: calls.append(
      "prepare_data"
    ),
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "materialize_lifecycle_manifest",
    lambda: calls.append(
      "manifest"
    ),
  )

  def prepare_candidate(**_):
    calls.append(
      "candidate"
    )

    return (
      candidate_manifest_path,
      candidate_directory,
      candidate_manifest,
    )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "prepare_candidate_run",
    prepare_candidate,
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "train_regression_candidate",
    lambda **_: calls.append(
      "regression"
    ),
  )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "train_classification_candidate",
    lambda **_: calls.append(
      "classification"
    ),
  )

  def compare_candidate(**_):
    calls.append(
      "comparison"
    )

    evaluated_manifest = {
      **candidate_manifest,
      "status": "evaluated",
      "evaluated_at_utc": (
        "2026-07-20T18:00:00+00:00"
      ),
    }

    candidate_manifest_path.write_text(
      json.dumps(
        evaluated_manifest
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
          "promotion_ready": False,
        }
      ),
      encoding="utf-8",
    )

  monkeypatch.setattr(
    model_retraining_scheduler,
    "compare_challenger_with_active_models",
    compare_candidate,
  )

  result = model_retraining_scheduler.run_scheduled_model_retraining(
    force=True,
    now_utc=datetime(
      2026,
      7,
      20,
      18,
      tzinfo=UTC,
    ),
    state_path=state_path,
  )

  assert calls == [
    "prepare_data",
    "manifest",
    "candidate",
    "regression",
    "classification",
    "comparison",
  ]

  assert result[
    "status"
  ] == "completed"

  assert result[
    "automatic_promotion_performed"
  ] is False

  saved_state = json.loads(
    state_path.read_text(
      encoding="utf-8"
    )
  )

  assert saved_state[
    "promotion_mode"
  ] == "manual"


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
