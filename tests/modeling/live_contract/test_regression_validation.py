"""Tests for validation-only live regression tuning."""

import pandas as pd
import pytest

from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.live_contract.regression_validation import (
  build_regression_model,
  select_best_configuration,
)


def test_regression_model_accepts_selected_live_feature_count():
  """The estimator must accept all selected live-contract features."""
  model = build_regression_model({
    "learning_rate": 0.05,
    "max_iter": 20,
    "max_leaf_nodes": 15,
    "min_samples_leaf": 10,
    "l2_regularization": 0.0,
  })

  row_count = 40

  features = pd.DataFrame({
    column: [
      float(index + position)
      for index in range(row_count)
    ]
    for position, column in enumerate(
      SELECTED_LIVE_FEATURE_COLUMNS
    )
  })

  target = pd.Series([
    float(index * 2)
    for index in range(row_count)
  ])

  model.fit(
    features,
    target,
  )

  predictions = model.predict(
    features
  )

  assert len(predictions) == row_count

  assert (
    model.n_features_in_
    == len(SELECTED_LIVE_FEATURE_COLUMNS)
  )


def test_best_configuration_uses_lowest_cv_mae_then_rmse():
  """CV MAE is primary and CV RMSE breaks exact MAE ties."""
  result = select_best_configuration([
    {
      "learning_rate": 0.10,
      "max_iter": 100,
      "max_leaf_nodes": 31,
      "min_samples_leaf": 20,
      "l2_regularization": 0.0,
      "cv_mae": 20.0,
      "cv_rmse": 50.0,
    },
    {
      "learning_rate": 0.05,
      "max_iter": 200,
      "max_leaf_nodes": 15,
      "min_samples_leaf": 20,
      "l2_regularization": 0.0,
      "cv_mae": 19.0,
      "cv_rmse": 55.0,
    },
    {
      "learning_rate": 0.05,
      "max_iter": 200,
      "max_leaf_nodes": 31,
      "min_samples_leaf": 50,
      "l2_regularization": 1.0,
      "cv_mae": 19.0,
      "cv_rmse": 52.0,
    },
  ])

  assert result["max_leaf_nodes"] == 31
  assert result["cv_rmse"] == pytest.approx(
    52.0
  )


def test_empty_tuning_results_are_rejected():
  """A missing tuning result must fail instead of selecting defaults."""
  with pytest.raises(
    ValueError,
    match="produced no results",
  ):
    select_best_configuration([])
