"""Derive one worker cycle's price thresholds from finalized observations."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DecisionContext:
  """Store the dynamic thresholds used by one worker cycle."""

  window_hours: int
  row_count: int
  q1: float
  q3: float
  iqr: float
  recommended_threshold: float
  avoid_threshold: float


def build_decision_context(
  prices: pd.Series,
  window_hours: int,
) -> DecisionContext:
  """Build dynamic decision thresholds from recent finalized prices."""
  numeric_prices = pd.to_numeric(
    prices,
    errors="coerce",
  ).dropna()

  if len(numeric_prices) < window_hours:
    raise ValueError(
      f"Decision context requires {window_hours} finalized prices, "
      f"but only {len(numeric_prices)} are available."
    )

  recent_prices = numeric_prices.tail(window_hours)

  q1 = float(recent_prices.quantile(0.25))
  q3 = float(recent_prices.quantile(0.75))
  iqr = q3 - q1

  return DecisionContext(
    window_hours=window_hours,
    row_count=len(recent_prices),
    q1=q1,
    q3=q3,
    iqr=iqr,
    recommended_threshold=q1,
    avoid_threshold=q3 + (1.5 * iqr),
  )
