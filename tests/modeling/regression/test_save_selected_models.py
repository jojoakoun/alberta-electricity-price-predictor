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
  assert result["feature_columns"].split("|")[0] == "forecast_price"
  assert result["sklearn_version"]
  assert result["training_start_utc"] == ""


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

def test_save_selected_regression_models_round_trip(tmp_path: Path) -> None:
  """End-to-end: fake selection file + tiny dataset -> reloadable artifacts."""
  import pandas as pd

  from electricity_predictor.modeling.regression.save_selected_models import (
    save_selected_regression_models,
  )

  # Small continuous hourly dataset with every required modeling column.
  rows = []
  for hour in range(40):
    rows.append(
      {
        "datetime_universal_time": (
          pd.Timestamp("2023-12-01 00:00:00") + pd.Timedelta(hours=hour)
          if hour < 20
          else pd.Timestamp("2024-06-01 00:00:00") + pd.Timedelta(hours=hour - 20)
          if hour < 30
          else pd.Timestamp("2025-06-01 00:00:00") + pd.Timedelta(hours=hour - 30)
        ),
        "actual_price": 30.0 + hour,
        "forecast_price": 29.0 + hour,
        "hour": hour % 24,
        "day_of_week": hour % 7,
        "month": 1,
        "is_weekend": 1 if hour % 7 in [5, 6] else 0,
        "actual_price_lag_1h": 29.0 + hour,
        "actual_price_lag_24h": 25.0 + hour,
        "forecast_price_lag_1h": 28.0 + hour,
        "actual_price_rolling_24h_mean": 27.0 + hour,
        "actual_price_rolling_24h_max": 35.0 + hour,
        "actual_price_rolling_7d_mean": 26.0 + hour,
        "actual_price_target_1h": 31.0 + hour,
        "actual_price_target_3h": 33.0 + hour,
      }
    )
  training_path = tmp_path / "training_dataset.csv"
  pd.DataFrame(rows).to_csv(training_path, index=False)

  # One learned winner and one baseline winner, like the real selection file.
  best_models = pd.DataFrame(
    [
      {
        "model_name": "linear_regression",
        "horizon_hours": 1,
        "model_parameters": "fit_intercept=True",
        "selection_metric": "mae",
        "selection_rule": "lowest_validation_mae_within_horizon",
      },
      {
        "model_name": "naive_baseline",
        "horizon_hours": 3,
        "model_parameters": "prediction_column=actual_price_lag_1h",
        "selection_metric": "mae",
        "selection_rule": "lowest_validation_mae_within_horizon",
      },
    ]
  )
  best_model_path = tmp_path / "best_regression_model.csv"
  best_models.to_csv(best_model_path, index=False)

  output_dir = tmp_path / "models"
  metadata_path = output_dir / "metadata.csv"

  written_path = save_selected_regression_models(
    best_model_path=best_model_path,
    training_dataset_path=training_path,
    output_dir=output_dir,
    metadata_path=metadata_path,
  )

  metadata = pd.read_csv(written_path)
  assert len(metadata) == 2

  # Fixed-date synthetic data -> 20 train + 10 validation = 30 final training rows, test excluded.
  assert metadata["training_rows"].tolist() == [30, 30]
  assert metadata["sklearn_version"].notna().all()
  assert metadata.loc[0, "feature_columns"].split("|")[0] == "forecast_price"
  assert metadata["training_start_utc"].notna().all()

  # The learned artifact must reload as a working estimator.
  learned = joblib.load(metadata.loc[0, "artifact_path"])
  assert hasattr(learned, "predict")

  # The baseline artifact must reload as a rule description, not an estimator.
  baseline = joblib.load(metadata.loc[1, "artifact_path"])
  assert isinstance(baseline, dict)
  assert baseline["model_type"] == "rule_baseline"
  assert baseline["prediction_column"] == "actual_price_lag_1h"
  assert baseline["target_column"] == "actual_price_target_3h"
