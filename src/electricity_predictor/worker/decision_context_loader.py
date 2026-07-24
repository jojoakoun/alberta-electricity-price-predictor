"""Load the configured observed-price window for worker decision rules."""

from electricity_predictor.config import load_configuration
from electricity_predictor.worker.decision_context import (
  DecisionContext,
  build_decision_context,
)
from electricity_predictor.worker.hourly_price_database import (
  load_recent_finalized_prices,
)


def load_decision_context() -> DecisionContext:
  """Build the current context from recent finalized prices."""
  configuration = load_configuration()
  window_hours = int(
    configuration["decision"]["window_hours"]
  )

  prices = load_recent_finalized_prices(
    limit=window_hours,
  )

  return build_decision_context(
    prices=prices,
    window_hours=window_hours,
  )
