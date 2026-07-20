import pandas as pd

from electricity_predictor.modeling.lifecycle.comparison import (
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
