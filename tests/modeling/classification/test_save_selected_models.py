from pathlib import Path

import joblib
import pytest

from electricity_predictor.modeling.classification.save_selected_models import (
  build_model_artifact_filename,
  load_final_decision_thresholds,
  build_naive_spike_baseline_artifact,
  save_model_artifact,
  save_selected_classification_models,
)


def test_build_model_artifact_filename():
  filename = build_model_artifact_filename(
    model_name="logistic_regression",
    horizon_hours=3,
  )

  assert filename == (
    "selected_classification_model_"
    "3h_logistic_regression.joblib"
  )


def test_build_naive_spike_baseline_artifact():
  artifact = build_naive_spike_baseline_artifact(
    selected_model={
      "model_name": "naive_spike_baseline",
      "horizon_hours": 6,
      "model_parameters": (
        "prediction_column=actual_price_lag_1h"
      ),
    },
    target_column="is_spike_target_6h",
    threshold=165.1475,
  )

  assert artifact["model_type"] == "rule_baseline"
  assert artifact["horizon_hours"] == 6
  assert artifact["spike_threshold"] == 165.1475


def test_save_model_artifact(
  tmp_path: Path,
):
  output_path = tmp_path / "artifact.joblib"
  artifact = {"model_name": "test"}

  saved_path = save_model_artifact(
    model=artifact,
    output_path=output_path,
  )

  assert saved_path == output_path
  assert joblib.load(output_path) == artifact


def test_save_selected_classification_models_round_trip(
  tmp_path: Path,
) -> None:
  """Save and reload one learned classifier and one rule baseline."""
  import pandas as pd

  timestamps = [
    *pd.date_range(
      "2023-12-01 00:00:00",
      periods=40,
      freq="h",
    ),
    *pd.date_range(
      "2024-06-01 00:00:00",
      periods=20,
      freq="h",
    ),
    *pd.date_range(
      "2025-06-01 00:00:00",
      periods=20,
      freq="h",
    ),
  ]

  rows = []

  for index, timestamp in enumerate(timestamps):
    # Alternate target prices so learned classifiers receive both classes.
    future_price = 300.0 if index % 4 == 0 else 40.0

    rows.append({
      "datetime_universal_time": timestamp,
      "actual_price": 30.0 + (index % 10),
      "forecast_price": 31.0 + (index % 10),
      "hour": timestamp.hour,
      "day_of_week": timestamp.dayofweek,
      "month": timestamp.month,
      "is_weekend": int(timestamp.dayofweek >= 5),
      "actual_price_lag_1h": 29.0 + (index % 10),
      "actual_price_lag_24h": 28.0 + (index % 10),
      "forecast_price_lag_1h": 30.0 + (index % 10),
      "actual_price_rolling_24h_mean": 32.0 + (index % 10),
      "actual_price_rolling_24h_max": 45.0 + (index % 10),
      "actual_price_rolling_7d_mean": 31.0 + (index % 10),
      "actual_price_target_1h": future_price,
      "actual_price_target_3h": future_price,
      "actual_price_target_6h": future_price,
      "actual_price_target_12h": future_price,
      "actual_price_target_24h": future_price,
    })

  training_path = tmp_path / "training_dataset.csv"
  pd.DataFrame(rows).to_csv(
    training_path,
    index=False,
  )

  selected_models = pd.DataFrame([
    {
      "model_name": "logistic_regression",
      "horizon_hours": 1,
      "model_parameters": "C=1.0; decision_threshold=0.45",
      "selection_metric": "f1",
      "selection_rule": "highest_validation_f1_within_horizon",
    },
    {
      "model_name": "naive_spike_baseline",
      "horizon_hours": 3,
      "model_parameters": (
        "prediction_column=actual_price_lag_1h"
      ),
      "selection_metric": "f1",
      "selection_rule": "highest_validation_f1_within_horizon",
    },
  ])

  best_model_path = tmp_path / "best_classification_model.csv"
  selected_models.to_csv(
    best_model_path,
    index=False,
  )

  output_dir = tmp_path / "models"
  metadata_path = output_dir / "metadata.csv"

  final_results_path = tmp_path / "final_classification_results.csv"
  pd.DataFrame([
    {
      "model_name": "logistic_regression",
      "horizon_hours": 1,
      "model_parameters": "C=1.0",
    },
    {
      "model_name": "naive_spike_baseline",
      "horizon_hours": 3,
      "model_parameters": "decision_threshold=0.50",
    },
  ]).to_csv(final_results_path, index=False)

  written_path = save_selected_classification_models(
    best_model_path=best_model_path,
    training_dataset_path=training_path,
    output_dir=output_dir,
    metadata_path=metadata_path,
    final_results_path=final_results_path,
  )

  metadata = pd.read_csv(written_path)

  assert len(metadata) == 2
  assert metadata["artifact_path"].notna().all()
  assert metadata["spike_threshold"].notna().all()
  assert metadata["decision_threshold"].iloc[0] == 0.45
  assert pd.isna(metadata["decision_threshold"].iloc[1])
  assert metadata["training_rows"].tolist() == [60, 60]

  learned_artifact = joblib.load(
    metadata.loc[
      metadata["model_name"] == "logistic_regression",
      "artifact_path",
    ].iloc[0]
  )
  assert hasattr(learned_artifact, "predict")
  assert hasattr(learned_artifact, "predict_proba")

  baseline_artifact = joblib.load(
    metadata.loc[
      metadata["model_name"] == "naive_spike_baseline",
      "artifact_path",
    ].iloc[0]
  )
  assert baseline_artifact["model_type"] == "rule_baseline"
  assert baseline_artifact["target_column"] == "is_spike_target_3h"
  assert baseline_artifact["spike_threshold"] == pytest.approx(
    metadata["spike_threshold"].iloc[0]
  )


def test_build_rule_spike_baseline_artifact_supports_new_baselines():
  from electricity_predictor.modeling.classification.save_selected_models import (
    build_rule_spike_baseline_artifact,
  )

  cases = [
    (
      "aeso_forecast_spike_baseline",
      "forecast_price",
    ),
    (
      "previous_day_spike_baseline",
      "actual_price_lag_24h",
    ),
  ]

  for model_name, expected_column in cases:
    artifact = build_rule_spike_baseline_artifact(
      selected_model={
        "model_name": model_name,
        "horizon_hours": 6,
        "model_parameters": (
          f"prediction_column={expected_column}"
        ),
      },
      target_column="is_spike_target_6h",
      threshold=170.77,
    )

    assert artifact["model_name"] == model_name
    assert artifact["model_type"] == "rule_baseline"
    assert artifact["prediction_column"] == expected_column
    assert artifact["spike_threshold"] == 170.77
