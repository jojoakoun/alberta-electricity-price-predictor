import pandas as pd

from electricity_predictor.modeling.decision.backtest_decision_windows import (
  backtest_window,
)


def test_backtest_keeps_existing_quartiles_and_price_labels() -> None:
  data = pd.DataFrame(
    {
      "datetime_universal_time": pd.date_range(
        "2024-01-01",
        periods=3,
        freq="h",
        tz="UTC",
      ),
      "actual_price": [10.0, 20.0, 30.0],
    }
  )

  result = backtest_window(data=data, window_hours=2)

  assert result.to_dict(orient="records") == [
    {
      "timestamp": pd.Timestamp("2024-01-01 02:00:00", tz="UTC"),
      "window_hours": 2,
      "actual_price": 30.0,
      "recommended_threshold": 12.5,
      "avoid_threshold": 25.0,
      "recommendation": "Avoid",
    }
  ]
