from unittest.mock import patch

import pandas as pd

from electricity_predictor.worker.decision_context import (
  DecisionContext,
)

from electricity_predictor.worker.prediction_cycle import run_prediction_cycle


def test_run_prediction_cycle_saves_predictions_and_decisions() -> None:
  generated_at = pd.Timestamp(
    "2026-07-17 18:00:00",
    tz="UTC",
  )

  features = pd.DataFrame(
    {
      "datetime_universal_time": [
        generated_at,
      ],
      "feature": [2],
    }
  )

  predictions = [
    {
      "horizon_hours": 1,
      "predicted_price": 77.19,
      "spike_probability": 0.245,
      "is_spike": False,
      "spike_threshold": 170.77,
      "forecast_kind": "model_forecast",
    }
  ]

  decisions = [
    {
      **predictions[0],
      "recommendation": "Recommended",
      "explanation": "Low spike probability.",
    }
  ]

  decision_context = DecisionContext(
    window_hours=720,
    row_count=720,
    q1=20.0,
    q3=40.0,
    iqr=20.0,
    recommended_threshold=20.0,
    avoid_threshold=70.0,
  )

  with (
    patch(
      "electricity_predictor.worker.prediction_cycle.load_configuration",
      return_value={
        "modeling": {
          "horizons_hours": [1],
        }
      },
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.prepare_model_features",
      return_value=features,
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle."
      "update_predictions_with_final_actual_prices",
      return_value=0,
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.generate_horizon_predictions",
      return_value=predictions,
    ) as generate_predictions,
    patch(
      "electricity_predictor.worker.prediction_cycle.load_decision_context",
      return_value=decision_context,
    ) as load_context,
    patch(
      "electricity_predictor.worker.prediction_cycle.apply_decision_layer",
      return_value=decisions,
    ) as apply_decisions,
    patch(
      "electricity_predictor.worker.prediction_cycle.save_successful_prediction_run",
      return_value=21,
    ) as save_run,
  ):
    result = run_prediction_cycle()

  generate_predictions.assert_called_once()
  assert generate_predictions.call_args.kwargs[
    "feature_row"
  ].equals(features)
  load_context.assert_called_once_with()
  apply_decisions.assert_called_once_with(
    predictions=predictions,
    context=decision_context,
  )

  save_run.assert_called_once_with(
    generated_at=generated_at.to_pydatetime(),
    decisions=decisions,
    detail="Application pipeline prediction cycle.",
  )

  assert result["run_id"] == 21
  assert result["decisions"] == decisions


def test_run_prediction_cycle_records_failure() -> None:
  failure = ValueError("Feature preparation failed.")

  with (
    patch(
      "electricity_predictor.worker.prediction_cycle.load_configuration",
      return_value={
        "modeling": {
          "horizons_hours": [1],
        }
      },
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle."
      "update_predictions_with_final_actual_prices",
      return_value=0,
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.prepare_model_features",
      side_effect=failure,
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.generate_horizon_predictions",
    ) as generate_predictions,
    patch(
      "electricity_predictor.worker.prediction_cycle.get_current_database_time",
      return_value=pd.Timestamp(
        "2026-07-17 18:00:00",
        tz="UTC",
      ).to_pydatetime(),
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.save_failed_prediction_run",
      return_value=32,
    ) as save_failed_run,
  ):
    try:
      run_prediction_cycle()
    except ValueError as error:
      assert str(error) == "Feature preparation failed."
    else:
      raise AssertionError("Worker failure was not re-raised.")

  save_failed_run.assert_called_once()
  generate_predictions.assert_not_called()

  saved_arguments = save_failed_run.call_args.kwargs

  assert saved_arguments["detail"] == (
    "ValueError: Feature preparation failed."
  )


def test_run_prediction_cycle_preserves_primary_error_when_failure_recording_fails(
) -> None:
  primary_error = ValueError("Feature preparation failed.")

  with (
    patch(
      "electricity_predictor.worker.prediction_cycle.load_configuration",
      return_value={"modeling": {"horizons_hours": [1]}},
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle."
      "update_predictions_with_final_actual_prices",
      return_value=0,
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.prepare_model_features",
      side_effect=primary_error,
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.get_current_database_time",
      return_value=pd.Timestamp(
        "2026-07-17 18:00:00",
        tz="UTC",
      ).to_pydatetime(),
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.save_failed_prediction_run",
      side_effect=RuntimeError("Database write failed."),
    ),
    patch(
      "electricity_predictor.worker.prediction_cycle.LOGGER.exception"
    ) as log_failure,
  ):
    try:
      run_prediction_cycle()
    except ValueError as error:
      assert error is primary_error
    else:
      raise AssertionError("Worker failure was not re-raised.")

  log_failure.assert_called_once_with(
    "Could not persist the failed worker run."
  )
