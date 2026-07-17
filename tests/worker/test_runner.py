from unittest.mock import patch

import pandas as pd

from electricity_predictor.worker.runner import run_worker_cycle


def test_run_worker_cycle_saves_predictions_and_decisions() -> None:
  generated_at = pd.Timestamp(
    "2026-07-17 18:00:00",
    tz="UTC",
  )

  features = pd.DataFrame(
    {
      "datetime_universal_time": [
        pd.Timestamp("2026-07-17 17:00:00", tz="UTC"),
        generated_at,
      ],
      "feature": [1, 2],
    }
  )

  predictions = [
    {
      "horizon_hours": 1,
      "predicted_price": 77.19,
      "spike_probability": 0.245,
      "is_spike": False,
      "spike_threshold": 170.77,
    }
  ]

  decisions = [
    {
      **predictions[0],
      "recommendation": "Recommended",
      "explanation": "Low spike probability.",
    }
  ]

  with (
    patch(
      "electricity_predictor.worker.runner.load_configuration",
      return_value={
        "modeling": {
          "horizons_hours": [1],
        }
      },
    ),
    patch(
      "electricity_predictor.worker.runner.prepare_model_features",
      return_value=features,
    ),
    patch(
      "electricity_predictor.worker.runner.generate_horizon_predictions",
      return_value=predictions,
    ) as generate_predictions,
    patch(
      "electricity_predictor.worker.runner.apply_decision_layer",
      return_value=decisions,
    ) as apply_decisions,
    patch(
      "electricity_predictor.worker.runner.save_prediction_run",
      return_value=21,
    ) as save_run,
  ):
    result = run_worker_cycle()

  generate_predictions.assert_called_once()
  apply_decisions.assert_called_once_with(predictions)

  save_run.assert_called_once_with(
    generated_at=generated_at.to_pydatetime(),
    decisions=decisions,
    detail="Application pipeline prediction cycle.",
  )

  assert result["run_id"] == 21
  assert result["decisions"] == decisions
