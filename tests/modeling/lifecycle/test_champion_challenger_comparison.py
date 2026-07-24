import pandas as pd

from electricity_predictor.modeling.lifecycle.champion_challenger_comparison import (
  build_classification_comparison,
  build_promotion_summary,
  build_regression_comparison,
)


def test_regression_candidate_must_not_degrade_either_metric():
  champion = pd.DataFrame(
    [
      {
        "horizon_hours": 1,
        "model_name": "champion",
        "mae": 30.0,
        "rmse": 80.0,
      },
      {
        "horizon_hours": 3,
        "model_name": "champion",
        "mae": 40.0,
        "rmse": 90.0,
      },
    ]
  )

  candidate = pd.DataFrame(
    [
      {
        "horizon_hours": 1,
        "model_name": "candidate",
        "mae": 25.0,
        "rmse": 75.0,
      },
      {
        "horizon_hours": 3,
        "model_name": "candidate",
        "mae": 39.0,
        "rmse": 95.0,
      },
    ]
  )

  comparison = build_regression_comparison(
    champion_results=champion,
    candidate_results=candidate,
  )

  assert bool(
    comparison.iloc[0][
      "promotion_gate_pass"
    ]
  )

  assert not bool(
    comparison.iloc[1][
      "promotion_gate_pass"
    ]
  )


def test_automatic_spike_threshold_change_does_not_block_promotion():
  champion = pd.DataFrame(
    [
      {
        "horizon_hours": 1,
        "model_name": "champion",
        "reference_spike_threshold": 157.885,
        "operational_spike_threshold": 170.77,
        "decision_threshold": 0.45,
        "precision": 0.30,
        "recall": 0.20,
        "f1": 0.24,
        "pr_auc": 0.30,
      },
    ]
  )

  candidate = pd.DataFrame(
    [
      {
        "horizon_hours": 1,
        "model_name": "candidate",
        "reference_spike_threshold": 157.885,
        "operational_spike_threshold": 157.885,
        "decision_threshold": 0.55,
        "precision": 0.60,
        "recall": 0.30,
        "f1": 0.40,
        "pr_auc": 0.50,
      },
    ]
  )

  comparison = build_classification_comparison(
    champion_results=champion,
    candidate_results=candidate,
  )

  assert bool(
    comparison.iloc[0][
      "metric_gate_pass"
    ]
  )

  assert bool(
    comparison.iloc[0][
      "promotion_gate_pass"
    ]
  )


def test_classification_metric_degradation_blocks_promotion():
  champion = pd.DataFrame(
    [
      {
        "horizon_hours": 1,
        "model_name": "champion",
        "reference_spike_threshold": 157.885,
        "operational_spike_threshold": 170.77,
        "decision_threshold": 0.45,
        "precision": 0.40,
        "recall": 0.40,
        "f1": 0.40,
        "pr_auc": 0.40,
      },
    ]
  )

  candidate = pd.DataFrame(
    [
      {
        "horizon_hours": 1,
        "model_name": "candidate",
        "reference_spike_threshold": 157.885,
        "operational_spike_threshold": 157.885,
        "decision_threshold": 0.55,
        "precision": 0.60,
        "recall": 0.30,
        "f1": 0.40,
        "pr_auc": 0.50,
      },
    ]
  )

  comparison = build_classification_comparison(
    champion_results=champion,
    candidate_results=candidate,
  )

  assert not bool(
    comparison.iloc[0][
      "metric_gate_pass"
    ]
  )

  assert not bool(
    comparison.iloc[0][
      "promotion_gate_pass"
    ]
  )


def test_promotion_summary_records_automatic_threshold_update():
  regression = pd.DataFrame(
    [
      {
        "promotion_gate_pass": True,
      },
    ]
  )

  classification = pd.DataFrame(
    [
      {
        "metric_gate_pass": True,
        "promotion_gate_pass": True,
      },
    ]
  )

  summary = build_promotion_summary(
    regression_comparison=regression,
    classification_comparison=classification,
    champion_spike_threshold=170.77,
    candidate_spike_threshold=157.885,
  )

  assert summary[
    "regression_gate_pass"
  ]

  assert summary[
    "classification_metric_gate_pass"
  ]

  assert summary[
    "classification_gate_pass"
  ]

  assert summary[
    "spike_threshold_changed"
  ]

  assert (
    summary[
      "spike_threshold_update_mode"
    ]
    == "automatic_train_derived"
  )

  assert summary[
    "promotion_ready"
  ]

def test_prepare_first_activation_review(
  tmp_path,
):
  import json

  import pandas as pd

  from electricity_predictor.modeling.lifecycle.candidate_run import (
    write_json_file,
  )
  from electricity_predictor.modeling.lifecycle.champion_challenger_comparison import (
    prepare_first_activation_review,
  )

  candidate_directory = (
    tmp_path
    / "candidate-v1"
  )

  tasks = {}

  for task_name in (
    "regression",
    "classification",
  ):
    task_directory = (
      candidate_directory
      / task_name
    )

    task_directory.mkdir(
      parents=True,
      exist_ok=True,
    )

    metadata_path = (
      task_directory
      / f"{task_name}_metadata.csv"
    )

    metadata_rows = []

    for horizon in (
      1,
      3,
      6,
      12,
      24,
    ):
      artifact_path = (
        task_directory
        / f"{task_name}_{horizon}h.joblib"
      )

      artifact_path.write_bytes(
        b"test-model"
      )

      metadata_rows.append({
        "horizon_hours":
          horizon,
        "artifact_path":
          str(
            artifact_path
          ),
        "artifact_sha256":
          "test-sha256",
        "feature_columns":
          "feature_a|feature_b",
        "contract":
          "conservative_hybrid",
      })

    pd.DataFrame(
      metadata_rows
    ).to_csv(
      metadata_path,
      index=False,
    )

    tasks[
      task_name
    ] = {
      "status":
        "completed",
      "metadata_path":
        str(
          metadata_path
        ),
    }

  candidate_manifest = {
    "status":
      "trained",
    "model_version":
      "candidate-v1",
    "candidate_directory":
      str(
        candidate_directory
      ),
    "tasks":
      tasks,
    "current_champion": {
      "status":
        "no_active_models",
    },
  }

  candidate_manifest_path = (
    candidate_directory
    / "candidate_manifest.json"
  )

  write_json_file(
    content=candidate_manifest,
    file_path=candidate_manifest_path,
  )

  summary_path, summary = (
    prepare_first_activation_review(
      candidate_manifest_path=(
        candidate_manifest_path
      )
    )
  )

  assert summary_path.is_file()

  assert summary[
    "review_type"
  ] == "first_activation"

  assert summary[
    "comparison_required"
  ] is False

  assert summary[
    "promotion_ready"
  ] is True

  assert summary[
    "manual_activation_required"
  ] is True

  updated_manifest = json.loads(
    candidate_manifest_path.read_text(
      encoding="utf-8"
    )
  )

  assert updated_manifest[
    "status"
  ] == "evaluated"

  assert updated_manifest[
    "comparison"
  ][
    "status"
  ] == "not_required"

  assert updated_manifest[
    "comparison"
  ][
    "reason"
  ] == "no_active_models"

def test_resolve_champion_model_versions_uses_registry_versions():
  from electricity_predictor.modeling.lifecycle.champion_challenger_comparison import (
    resolve_champion_model_versions,
  )

  candidate_manifest = {
    "current_champion": {
      "status":
        "active_models_available",
      "regression_model_version":
        "regression-active-v7",
      "classification_model_version":
        "classification-active-v4",
    },
  }

  versions = resolve_champion_model_versions(
    candidate_manifest
  )

  assert versions == (
    "regression-active-v7",
    "classification-active-v4",
  )


def test_resolve_champion_model_versions_preserves_old_manifest_compatibility():
  from electricity_predictor.modeling.lifecycle.champion_challenger_comparison import (
    resolve_champion_model_versions,
  )

  versions = resolve_champion_model_versions({
    "current_champion": {
      "status":
        "active_models_available",
    },
  })

  assert versions == (
    "legacy-unversioned",
    "legacy-unversioned",
  )
