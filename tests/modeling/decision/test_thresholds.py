import pandas as pd

from electricity_predictor.config import load_configuration
from electricity_predictor.modeling.decision.thresholds import (
  DECISION_WINDOW_HOURS,
  build_rolling_price_thresholds,
)


def test_decision_window_matches_project_configuration() -> None:
  assert DECISION_WINDOW_HOURS == int(
    load_configuration()["decision"]["window_hours"]
  )


def test_rolling_thresholds_use_only_preceding_prices() -> None:
  prices = pd.Series([10.0, 20.0, 30.0, 400.0])

  thresholds = build_rolling_price_thresholds(
    prices=prices,
    window_hours=3,
    recommended_quantile=0.25,
    avoid_iqr_multiplier=1.5,
  )

  assert thresholds.index.equals(prices.index)
  assert thresholds.iloc[:3].isna().all().all()
  assert thresholds.loc[3, "recommended_threshold"] == 15.0
  assert thresholds.loc[3, "avoid_threshold"] == 40.0


def test_current_price_cannot_change_its_own_thresholds() -> None:
  low_current = pd.Series([10.0, 20.0, 30.0, -100.0])
  high_current = pd.Series([10.0, 20.0, 30.0, 1000.0])

  low_thresholds = build_rolling_price_thresholds(
    prices=low_current,
    window_hours=3,
    recommended_quantile=0.25,
    avoid_iqr_multiplier=1.5,
  )
  high_thresholds = build_rolling_price_thresholds(
    prices=high_current,
    window_hours=3,
    recommended_quantile=0.25,
    avoid_iqr_multiplier=1.5,
  )

  pd.testing.assert_series_equal(
    low_thresholds.loc[3],
    high_thresholds.loc[3],
  )
