import pandas as pd
import pytest

from electricity_predictor.modeling.lifecycle.split_plan import (
  build_expanding_split_plan,
  build_lifecycle_split_plan_from_config,
)


def test_build_expanding_split_plan_moves_with_latest_data():
  plan = build_expanding_split_plan(
    latest_timestamp_utc="2026-07-20 14:00:00",
    train_start_utc="2020-01-08 07:00:00",
    validation_days=365,
    test_days=180,
    purge_hours=24,
    minimum_training_days=1095,
  )

  assert plan.test_end_utc == pd.Timestamp(
    "2026-07-20 14:00:00"
  )

  assert plan.test_start_utc == pd.Timestamp(
    "2026-01-21 15:00:00"
  )

  assert plan.validation_start_utc == pd.Timestamp(
    "2025-01-20 15:00:00"
  )

  assert plan.purge_hours == 24


def test_build_expanding_split_plan_preserves_fixed_train_start():
  plan = build_expanding_split_plan(
    latest_timestamp_utc="2027-01-01 00:00:00",
    train_start_utc="2020-01-08 07:00:00",
    validation_days=365,
    test_days=180,
    purge_hours=24,
    minimum_training_days=1095,
  )

  assert plan.train_start_utc == pd.Timestamp(
    "2020-01-08 07:00:00"
  )


def test_build_expanding_split_plan_rejects_insufficient_history():
  with pytest.raises(
    ValueError,
    match="minimum required training history",
  ):
    build_expanding_split_plan(
      latest_timestamp_utc="2022-01-01 00:00:00",
      train_start_utc="2020-01-08 07:00:00",
      validation_days=365,
      test_days=180,
      purge_hours=24,
      minimum_training_days=1095,
    )


def test_build_lifecycle_split_plan_from_config():
  plan = build_lifecycle_split_plan_from_config(
    latest_timestamp_utc="2026-07-20 14:00:00",
    modeling_config={
      "train_start_utc": "2020-01-08 07:00:00",
    },
    lifecycle_config={
      "strategy": "expanding",
      "validation_days": 365,
      "test_days": 180,
      "purge_hours": 24,
      "minimum_training_days": 1095,
    },
  )

  assert plan.test_end_utc == pd.Timestamp(
    "2026-07-20 14:00:00"
  )


def test_lifecycle_split_plan_rejects_unknown_strategy():
  with pytest.raises(
    ValueError,
    match="expanding",
  ):
    build_lifecycle_split_plan_from_config(
      latest_timestamp_utc="2026-07-20 14:00:00",
      modeling_config={
        "train_start_utc": "2020-01-08 07:00:00",
      },
      lifecycle_config={
        "strategy": "rolling",
      },
    )
