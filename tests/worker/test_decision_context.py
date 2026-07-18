import pandas as pd
import pytest

from electricity_predictor.worker.decision_context import (
  build_decision_context,
)


def test_build_decision_context() -> None:
  context = build_decision_context(
    prices=pd.Series([10, 20, 30, 40, 50, 60, 70, 80]),
    window_hours=8,
  )

  assert context.window_hours == 8
  assert context.row_count == 8
  assert context.q1 == 27.5
  assert context.q3 == 62.5
  assert context.iqr == 35.0
  assert context.recommended_threshold == 27.5
  assert context.avoid_threshold == 115.0


def test_build_decision_context_rejects_insufficient_prices() -> None:
  with pytest.raises(
    ValueError,
    match="requires 8 finalized prices",
  ):
    build_decision_context(
      prices=pd.Series([10, 20, 30]),
      window_hours=8,
    )
