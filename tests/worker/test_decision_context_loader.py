from unittest.mock import patch

import pandas as pd

from electricity_predictor.worker.decision_context_loader import (
  load_decision_context,
)


@patch(
  "electricity_predictor.worker.decision_context_loader."
  "load_recent_finalized_prices"
)
@patch(
  "electricity_predictor.worker.decision_context_loader."
  "load_configuration"
)
def test_load_decision_context(
  mock_load_configuration,
  mock_load_prices,
) -> None:
  mock_load_configuration.return_value = {
    "decision": {
      "window_hours": 8,
    }
  }
  mock_load_prices.return_value = pd.Series(
    [10, 20, 30, 40, 50, 60, 70, 80]
  )

  context = load_decision_context()

  assert context.window_hours == 8
  assert context.recommended_threshold == 27.5
  assert context.avoid_threshold == 115.0

  mock_load_prices.assert_called_once_with(limit=8)
