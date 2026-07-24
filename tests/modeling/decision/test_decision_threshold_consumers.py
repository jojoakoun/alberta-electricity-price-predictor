import pandas as pd

from electricity_predictor.modeling.decision import calibrate_decision_policy
from electricity_predictor.modeling.decision.stress_test_predicted_decisions import (
  build_dynamic_thresholds,
)


def test_calibration_search_space_remains_unchanged() -> None:
  assert calibrate_decision_policy.RECOMMENDED_QUANTILES == [
    0.10,
    0.15,
    0.20,
    0.25,
  ]
  assert calibrate_decision_policy.AVOID_IQR_MULTIPLIERS == [
    1.5,
    2.0,
    2.5,
    3.0,
  ]


def test_calibration_threshold_wrapper_preserves_configurable_policy(
  monkeypatch,
) -> None:
  monkeypatch.setattr(calibrate_decision_policy, "WINDOW_HOURS", 3)
  prices = pd.Series([10.0, 20.0, 30.0, 40.0])

  result = calibrate_decision_policy.build_thresholds(
    prices=prices,
    recommended_quantile=0.10,
    avoid_iqr_multiplier=2.0,
  )

  assert result.loc[3, "recommended_threshold"] == 12.0
  assert result.loc[3, "avoid_threshold"] == 45.0


def test_calibration_uses_validation_without_exposing_protected_test(
  monkeypatch,
) -> None:
  train_data = pd.DataFrame({"split": ["train"]})
  validation_data = pd.DataFrame({"split": ["validation"]})
  protected_test_data = pd.DataFrame({"split": ["test"]})

  monkeypatch.setattr(
    calibrate_decision_policy,
    "split_time_series_data_from_config",
    lambda **_: (
      train_data,
      validation_data,
      protected_test_data,
    ),
  )

  selected_train, selected_validation = (
    calibrate_decision_policy.split_calibration_data(
    data=pd.DataFrame(),
    modeling_config={},
    )
  )

  assert selected_train is train_data
  assert selected_validation is validation_data


def test_stress_threshold_wrapper_preserves_q1_and_iqr_policy() -> None:
  data = pd.DataFrame({"actual_price": [10.0, 20.0, 30.0, 40.0]})

  result = build_dynamic_thresholds(data=data, window_hours=3)

  assert result.loc[3, "recommended_threshold"] == 15.0
  assert result.loc[3, "avoid_threshold"] == 40.0
