from pathlib import Path

import joblib
from sklearn.linear_model import LinearRegression

from electricity_predictor.modeling.regression.save_selected_models import (
  build_model_artifact_filename,
  build_model_metadata_row,
  build_naive_baseline_artifact,
  save_model_artifact,
)


def test_build_model_artifact_filename_includes_horizon_and_model_name() -> None:
  filename = build_model_artifact_filename(
    model_name="lasso_regression_tuned",
    horizon_hours=24,
  )

  assert filename == "selected_regression_model_24h_lasso_regression_tuned.joblib"


def test_save_model_artifact_creates_joblib_file(tmp_path: Path) -> None:
  model = LinearRegression()
  output_path = tmp_path / "model.joblib"

  saved_path = save_model_artifact(model=model, output_path=output_path)

  assert saved_path == output_path
  assert output_path.exists()
  assert isinstance(joblib.load(output_path), LinearRegression)


def test_build_model_metadata_row_returns_saved_model_summary() -> None:
  selected_model = {
    "model_name": "random_forest_regressor_tuned",
    "horizon_hours": 1,
    "selection_metric": "mae",
    "selection_rule": "lowest_validation_mae_within_horizon",
    "model_parameters": "n_estimators=200; max_depth=20",
  }

  result = build_model_metadata_row(
    selected_model=selected_model,
    target_column="actual_price_target_1h",
    artifact_path=Path("models/regression/model.joblib"),
    training_rows=17083,
  )

  assert result["model_name"] == "random_forest_regressor_tuned"
  assert result["horizon_hours"] == 1
  assert result["target_column"] == "actual_price_target_1h"
  assert result["artifact_path"] == "models/regression/model.joblib"
  assert result["training_rows"] == 17083
  assert result["selection_metric"] == "mae"
  assert result["selection_rule"] == "lowest_validation_mae_within_horizon"
  assert result["model_parameters"] == "n_estimators=200; max_depth=20"


def test_build_naive_baseline_artifact_returns_rule_summary() -> None:
  selected_model = {
    "model_name": "naive_baseline",
    "horizon_hours": 3,
    "model_parameters": "prediction_column=actual_price_lag_1h",
  }

  artifact = build_naive_baseline_artifact(
    selected_model=selected_model,
    target_column="actual_price_target_3h",
  )

  assert artifact == {
    "model_name": "naive_baseline",
    "model_type": "rule_baseline",
    "horizon_hours": 3,
    "target_column": "actual_price_target_3h",
    "prediction_column": "actual_price_lag_1h",
    "model_parameters": "prediction_column=actual_price_lag_1h",
  }
