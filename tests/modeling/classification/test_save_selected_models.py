from pathlib import Path

import joblib

from electricity_predictor.modeling.classification.save_selected_models import (
  build_model_artifact_filename,
  build_naive_spike_baseline_artifact,
  save_model_artifact,
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
