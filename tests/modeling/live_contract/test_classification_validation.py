"""Tests for validation-only live classification tuning."""

import pandas as pd
import pytest

from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.features.live_feature_contract import (
  SELECTED_LIVE_FEATURE_COLUMNS,
)
from electricity_predictor.modeling.live_contract.classification_validation import (
  add_spike_targets,
  build_candidate_configurations,
  build_classifier,
  prepare_live_classification_splits,
  select_best_candidate,
)


def build_feature_rows(
  row_count: int = 80,
) -> pd.DataFrame:
  """Build a complete small classification dataset."""
  data = pd.DataFrame({
    column: [
      float(
        row_index + column_index
      )
      for row_index in range(
        row_count
      )
    ]
    for (
      column_index,
      column,
    ) in enumerate(
      SELECTED_LIVE_FEATURE_COLUMNS
    )
  })

  data["actual_price"] = [
    float(
      20 + row_index
    )
    for row_index in range(
      row_count
    )
  ]

  for horizon_hours in (
    SUPPORTED_FORECAST_HORIZONS_HOURS
  ):
    data[
      f"actual_price_target_{horizon_hours}h"
    ] = [
      (
        250.0
        if row_index % 7 == 0
        else 40.0
      )
      for row_index in range(
        row_count
      )
    ]

  return data


def test_candidate_grid_contains_both_established_families():
  candidates = (
    build_candidate_configurations()
  )

  assert len(candidates) == 13

  families = [
    candidate["model_family"]
    for candidate in candidates
  ]

  assert families.count(
    "hist_gradient_boosting"
  ) == 5

  assert families.count(
    "gradient_boosting"
  ) == 8


@pytest.mark.parametrize(
  "candidate",
  [
    {
      "model_family":
        "hist_gradient_boosting",
      "model_name":
        "hist_gradient_boosting_classifier_tuned",
      "learning_rate": 0.1,
      "max_iter": 20,
      "max_leaf_nodes": 15,
      "min_samples_leaf": 10,
      "l2_regularization": 0.0,
    },
    {
      "model_family":
        "gradient_boosting",
      "model_name":
        "gradient_boosting_classifier_tuned",
      "n_estimators": 20,
      "learning_rate": 0.1,
      "max_depth": 2,
    },
  ],
)
def test_classifier_accepts_selected_live_features(
  candidate,
):
  data = build_feature_rows()

  labeled = add_spike_targets(
    data=data,
    spike_threshold=170.77,
  )

  target_column = (
    "is_spike_target_1h"
  )

  model = build_classifier(
    candidate
  )

  model.fit(
    labeled[
      SELECTED_LIVE_FEATURE_COLUMNS
    ],
    labeled[target_column],
  )

  assert (
    model.n_features_in_
    == len(SELECTED_LIVE_FEATURE_COLUMNS)
  )


def test_candidate_selection_prefers_pr_auc_then_f1():
  selected = select_best_candidate([
    {
      "candidate": {
        "model_family": "first",
      },
      "model_name": "first",
      "cv_accuracy": 0.9,
      "cv_precision": 0.5,
      "cv_recall": 0.5,
      "cv_f1": 0.60,
      "cv_pr_auc": 0.70,
    },
    {
      "candidate": {
        "model_family": "second",
      },
      "model_name": "second",
      "cv_accuracy": 0.8,
      "cv_precision": 0.6,
      "cv_recall": 0.6,
      "cv_f1": 0.65,
      "cv_pr_auc": 0.70,
    },
    {
      "candidate": {
        "model_family": "third",
      },
      "model_name": "third",
      "cv_accuracy": 0.7,
      "cv_precision": 0.7,
      "cv_recall": 0.7,
      "cv_f1": 0.70,
      "cv_pr_auc": 0.69,
    },
  ])

  assert (
    selected["model_name"]
    == "second"
  )


def test_spike_threshold_uses_train_prices_only():
  train_data = build_feature_rows()
  validation_data = build_feature_rows()

  validation_data[
    "actual_price"
  ] = 100000.0

  (
    prepared_train,
    prepared_validation,
    threshold,
  ) = prepare_live_classification_splits(
    train_data=train_data,
    validation_data=validation_data,
  )

  expected_threshold = (
    prepare_live_classification_splits(
      train_data=train_data,
      validation_data=train_data,
    )[2]
  )

  assert threshold == pytest.approx(
    expected_threshold
  )

  assert (
    "is_spike_target_24h"
    in prepared_train.columns
  )

  assert (
    "is_spike_target_24h"
    in prepared_validation.columns
  )


def test_empty_candidate_results_are_rejected():
  with pytest.raises(
    ValueError,
    match="produced no results",
  ):
    select_best_candidate([])
