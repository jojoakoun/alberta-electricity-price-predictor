from pathlib import Path

import joblib
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier, DummyRegressor

from electricity_predictor.serving.inference import (
  parse_feature_columns,
  predict_horizon,
  prepare_feature_row,
)


FEATURE_COLUMNS = [
  "forecast_price",
  "actual_price_lag_1h",
]


def write_test_artifacts(tmp_path: Path) -> tuple[Path, Path]:
  """Create tiny reloadable artifacts and their metadata."""
  training_features = pd.DataFrame({
    "forecast_price": [20.0, 40.0, 60.0, 80.0],
    "actual_price_lag_1h": [18.0, 35.0, 55.0, 75.0],
  })

  regression_model = DummyRegressor(strategy="constant", constant=55.0)
  regression_model.fit(
    training_features,
    [30.0, 40.0, 50.0, 60.0],
  )

  classification_model = DummyClassifier(
    strategy="constant",
    constant=1,
  )
  classification_model.fit(
    training_features,
    [0, 1, 0, 1],
  )

  regression_artifact_path = tmp_path / "regression.joblib"
  classification_artifact_path = tmp_path / "classification.joblib"

  joblib.dump(regression_model, regression_artifact_path)
  joblib.dump(classification_model, classification_artifact_path)

  regression_metadata_path = tmp_path / "regression_metadata.csv"
  classification_metadata_path = tmp_path / "classification_metadata.csv"

  pd.DataFrame([
    {
      "model_name": "dummy_regression",
      "horizon_hours": 1,
      "artifact_path": regression_artifact_path,
      "feature_columns": "|".join(FEATURE_COLUMNS),
    }
  ]).to_csv(regression_metadata_path, index=False)

  pd.DataFrame([
    {
      "model_name": "dummy_classification",
      "horizon_hours": 1,
      "artifact_path": classification_artifact_path,
      "feature_columns": "|".join(FEATURE_COLUMNS),
      "spike_threshold": 170.77,
      "decision_threshold": 0.45,
    }
  ]).to_csv(classification_metadata_path, index=False)

  return regression_metadata_path, classification_metadata_path


def test_parse_feature_columns_preserves_order():
  columns = parse_feature_columns(
    "forecast_price|actual_price_lag_1h"
  )

  assert columns == FEATURE_COLUMNS


def test_prepare_feature_row_rejects_missing_features():
  with pytest.raises(ValueError, match="missing columns"):
    prepare_feature_row(
      features={"forecast_price": 50.0},
      feature_columns=FEATURE_COLUMNS,
    )


def test_predict_horizon_loads_artifacts_and_returns_prediction(
  tmp_path: Path,
):
  regression_metadata_path, classification_metadata_path = (
    write_test_artifacts(tmp_path)
  )

  result = predict_horizon(
    horizon_hours=1,
    features={
      "forecast_price": 50.0,
      "actual_price_lag_1h": 45.0,
    },
    regression_metadata_path=regression_metadata_path,
    classification_metadata_path=classification_metadata_path,
  )

  assert result["horizon_hours"] == 1
  assert result["predicted_price"] == pytest.approx(55.0)
  assert result["spike_probability"] == pytest.approx(1.0)
  assert result["decision_threshold"] == pytest.approx(0.45)
  assert result["is_spike"] is True
  assert result["spike_threshold"] == pytest.approx(170.77)


def test_predict_horizon_supports_regression_rule_baseline(
  tmp_path: Path,
):
  classification_training_features = pd.DataFrame({
    "forecast_price": [20.0, 40.0],
    "actual_price_lag_1h": [18.0, 35.0],
  })
  classifier = DummyClassifier(strategy="constant", constant=0)
  classifier.fit(
    classification_training_features,
    [0, 1],
  )

  regression_artifact_path = tmp_path / "baseline.joblib"
  classification_artifact_path = tmp_path / "classifier.joblib"

  joblib.dump(
    {
      "model_type": "rule_baseline",
      "prediction_column": "actual_price_lag_1h",
    },
    regression_artifact_path,
  )
  joblib.dump(classifier, classification_artifact_path)

  regression_metadata_path = tmp_path / "regression_metadata.csv"
  classification_metadata_path = tmp_path / "classification_metadata.csv"

  pd.DataFrame([
    {
      "model_name": "naive_baseline",
      "horizon_hours": 24,
      "artifact_path": regression_artifact_path,
      "feature_columns": "|".join(FEATURE_COLUMNS),
    }
  ]).to_csv(regression_metadata_path, index=False)

  pd.DataFrame([
    {
      "model_name": "dummy_classification",
      "horizon_hours": 24,
      "artifact_path": classification_artifact_path,
      "feature_columns": "|".join(FEATURE_COLUMNS),
      "spike_threshold": 170.77,
      "decision_threshold": 0.50,
    }
  ]).to_csv(classification_metadata_path, index=False)

  result = predict_horizon(
    horizon_hours=24,
    features={
      "forecast_price": 90.0,
      "actual_price_lag_1h": 72.5,
    },
    regression_metadata_path=regression_metadata_path,
    classification_metadata_path=classification_metadata_path,
  )

  assert result["predicted_price"] == pytest.approx(72.5)
  assert result["regression_model"] == "naive_baseline"


def test_predict_horizon_rejects_unknown_horizon(tmp_path: Path):
  regression_metadata_path, classification_metadata_path = (
    write_test_artifacts(tmp_path)
  )

  with pytest.raises(ValueError, match="No selected model"):
    predict_horizon(
      horizon_hours=6,
      features={
        "forecast_price": 50.0,
        "actual_price_lag_1h": 45.0,
      },
      regression_metadata_path=regression_metadata_path,
      classification_metadata_path=classification_metadata_path,
    )
