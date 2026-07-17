from unittest.mock import patch

import pandas as pd

from electricity_predictor.worker.feature_preparation import (
  prepare_model_features,
)


def test_prepare_model_features_builds_complete_application_features() -> None:
  raw = pd.DataFrame(
    {
      "datetime_universal_time": pd.date_range(
        "2026-01-01",
        periods=200,
        freq="h",
        tz="UTC",
      ),
      "actual_price": [float(value) for value in range(200)],
      "forecast_price": [float(value) for value in range(200)],
      "alberta_internal_load": [8000.0] * 200,
      "source": ["pipeline"] * 200,
    }
  )

  with patch(
    "electricity_predictor.worker.feature_preparation.load_hourly_prices",
    return_value=raw,
  ):
    result = prepare_model_features()

  latest = result.iloc[-1]

  assert "datetime_local_time" in result.columns
  assert "actual_price_target_1h" not in result.columns
  assert latest["actual_price_lag_1h"] == 198.0
  assert latest["actual_price_lag_24h"] == 175.0
  assert latest["forecast_price_lag_1h"] == 198.0
  assert pd.notna(latest["actual_price_rolling_7d_mean"])
