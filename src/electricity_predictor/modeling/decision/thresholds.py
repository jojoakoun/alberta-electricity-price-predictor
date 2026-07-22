"""Leakage-safe threshold construction for decision research."""

import pandas as pd

from electricity_predictor.config import load_configuration


def load_decision_window_hours() -> int:
  """Return the configured finalized-price history used by decisions."""
  return int(load_configuration()["decision"]["window_hours"])


DECISION_WINDOW_HOURS = load_decision_window_hours()


def build_rolling_price_thresholds(
  prices: pd.Series,
  window_hours: int,
  recommended_quantile: float,
  avoid_iqr_multiplier: float,
) -> pd.DataFrame:
  """Build thresholds using only prices preceding each evaluated row."""
  # Shift first so the current observed price cannot influence its own label.
  historical_prices = pd.to_numeric(
    prices,
    errors="coerce",
  ).shift(1)

  recommended_threshold = historical_prices.rolling(
    window=window_hours,
    min_periods=window_hours,
  ).quantile(recommended_quantile)
  q1 = historical_prices.rolling(
    window=window_hours,
    min_periods=window_hours,
  ).quantile(0.25)
  q3 = historical_prices.rolling(
    window=window_hours,
    min_periods=window_hours,
  ).quantile(0.75)

  return pd.DataFrame(
    {
      "recommended_threshold": recommended_threshold,
      "avoid_threshold": q3 + avoid_iqr_multiplier * (q3 - q1),
    },
    index=prices.index,
  )
