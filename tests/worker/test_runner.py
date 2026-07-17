from unittest.mock import patch

import pandas as pd

from electricity_predictor.worker.runner import run_worker_cycle


def test_run_worker_cycle_generates_configured_horizon_predictions() -> None:
  features = pd.DataFrame(
    {
      "feature": [1, 2, 3],
    }
  )

  expected_predictions = [
    {"horizon_hours": 1, "predicted_price": 40.0},
    {"horizon_hours": 3, "predicted_price": 45.0},
  ]

  with (
    patch(
      "electricity_predictor.worker.runner.load_configuration",
      return_value={
        "modeling": {
          "horizons_hours": [1, 3],
        }
      },
    ),
    patch(
      "electricity_predictor.worker.runner.prepare_model_features",
      return_value=features,
    ) as prepare_features,
    patch(
      "electricity_predictor.worker.runner.generate_horizon_predictions",
      return_value=expected_predictions,
    ) as generate_predictions,
  ):
    predictions = run_worker_cycle()

  prepare_features.assert_called_once_with()
  generate_predictions.assert_called_once()

  called_feature_row = generate_predictions.call_args.kwargs["feature_row"]

  assert len(called_feature_row) == 1
  assert called_feature_row.iloc[0]["feature"] == 3
  assert predictions == expected_predictions
