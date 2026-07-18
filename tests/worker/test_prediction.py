from unittest.mock import call, patch

import pandas as pd
import pytest

from electricity_predictor.worker.prediction import (
  generate_horizon_predictions,
)


def test_generate_horizon_predictions_calls_each_model_horizon() -> None:
  feature_row = pd.DataFrame(
    {
      "forecast_price": [40.0],
      "actual_price_lag_1h": [42.0],
    }
  )

  with patch(
    "electricity_predictor.worker.prediction.predict_horizon",
    side_effect=lambda horizon_hours, features: {
      "horizon_hours": horizon_hours,
      "predicted_price": float(horizon_hours * 10),
    },
  ) as predict:
    predictions = generate_horizon_predictions(
      feature_row=feature_row,
      horizons_hours=[1, 3, 6, 12, 24],
    )

  assert len(predictions) == 5
  assert predictions[-1]["horizon_hours"] == 24

  predict.assert_has_calls(
    [
      call(
        horizon_hours=1,
        features=feature_row.iloc[0].to_dict(),
      ),
      call(
        horizon_hours=3,
        features=feature_row.iloc[0].to_dict(),
      ),
      call(
        horizon_hours=6,
        features=feature_row.iloc[0].to_dict(),
      ),
      call(
        horizon_hours=12,
        features=feature_row.iloc[0].to_dict(),
      ),
      call(
        horizon_hours=24,
        features=feature_row.iloc[0].to_dict(),
      ),
    ]
  )


def test_generate_horizon_predictions_requires_one_row() -> None:
  with pytest.raises(
    ValueError,
    match="Prediction requires exactly one feature row",
  ):
    generate_horizon_predictions(
      feature_row=pd.DataFrame({"feature": [1, 2]}),
      horizons_hours=[1],
    )
