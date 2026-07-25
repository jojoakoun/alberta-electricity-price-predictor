import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from electricity_predictor.worker.prediction_run_database import (
  save_successful_prediction_run,
)


def build_decisions() -> list[dict]:
  return [
    {
      "horizon_hours": horizon,
      "predicted_price": 70.0 + horizon,
      "spike_probability": 0.1,
      "is_spike": False,
      "spike_threshold": 170.77,
      "forecast_kind": (
        "persistence_reference"
        if horizon == 24
        else "model_forecast"
      ),
      "recommendation": "Recommended",
      "explanation": "Low spike probability.",
    }
    for horizon in [
      1,
      3,
      6,
      12,
      24,
    ]
  ]


def test_save_successful_prediction_run_upserts_and_replaces_horizons() -> None:
  generated_at = datetime(
    2026,
    7,
    17,
    18,
    0,
    tzinfo=timezone.utc,
  )

  cursor = MagicMock()
  cursor.fetchone.return_value = (12,)

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.prediction_run_database."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    run_id = save_successful_prediction_run(
      generated_at=generated_at,
      decisions=build_decisions(),
      confidence="medium",
    )

  insert_query = (
    cursor.execute.call_args_list[0]
    .args[0]
  )

  delete_query = (
    cursor.execute.call_args_list[1]
    .args[0]
  )

  records = (
    cursor.executemany
    .call_args
    .args[1]
  )

  assert run_id == 12
  assert (
    "ON CONFLICT (generated_at)"
    in insert_query
  )
  assert (
    "WHERE status = 'success'"
    in insert_query
  )
  assert (
    "DELETE FROM predictions"
    in delete_query
  )
  assert [
    record[1]
    for record in records
  ] == [
    1,
    3,
    6,
    12,
    24,
  ]

  run_values = (
    cursor.execute.call_args_list[0]
    .args[1]
  )
  run_detail = json.loads(run_values[3])

  assert run_detail == {
    "forecastKinds": {
      "1": "model_forecast",
      "3": "model_forecast",
      "6": "model_forecast",
      "12": "model_forecast",
      "24": "persistence_reference",
    },
    "schemaVersion": 1,
    "summary": None,
  }

  connection.commit.assert_called_once()


def test_two_worker_writes_for_one_source_hour_reuse_one_five_horizon_run() -> None:
  generated_at = datetime(
    2026,
    7,
    17,
    18,
    0,
    tzinfo=timezone.utc,
  )

  cursor = MagicMock()
  cursor.fetchone.side_effect = [
    (12,),
    (12,),
  ]

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.prediction_run_database."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    first_run_id = save_successful_prediction_run(
      generated_at=generated_at,
      decisions=build_decisions(),
    )
    second_run_id = save_successful_prediction_run(
      generated_at=generated_at,
      decisions=build_decisions(),
    )

  assert first_run_id == second_run_id == 12
  assert cursor.executemany.call_count == 2
  assert connection.commit.call_count == 2

  insert_calls = [
    call_arguments
    for call_arguments in cursor.execute.call_args_list
    if "INSERT INTO prediction_runs" in call_arguments.args[0]
  ]

  assert len(insert_calls) == 2
  assert all(
    "ON CONFLICT (generated_at)" in call_arguments.args[0]
    and "WHERE status = 'success'" in call_arguments.args[0]
    for call_arguments in insert_calls
  )

  for call_arguments in cursor.executemany.call_args_list:
    records = call_arguments.args[1]

    assert [record[1] for record in records] == [
      1,
      3,
      6,
      12,
      24,
    ]


def test_save_successful_prediction_run_rejects_empty_decisions() -> None:
  with pytest.raises(
    ValueError,
    match="At least one prediction decision is required",
  ):
    save_successful_prediction_run(
      generated_at=datetime.now(
        timezone.utc
      ),
      decisions=[],
    )


def test_save_successful_prediction_run_rejects_incomplete_horizons() -> None:
  with pytest.raises(
    ValueError,
    match=(
      "exactly the horizons "
      "1, 3, 6, 12, 24 hours"
    ),
  ):
    save_successful_prediction_run(
      generated_at=datetime.now(
        timezone.utc
      ),
      decisions=build_decisions()[:-1],
    )


def test_save_successful_prediction_run_rejects_unknown_forecast_kind() -> None:
  decisions = build_decisions()
  decisions[0]["forecast_kind"] = "mystery"

  with pytest.raises(
    ValueError,
    match="Unsupported forecast kind",
  ):
    save_successful_prediction_run(
      generated_at=datetime.now(
        timezone.utc
      ),
      decisions=decisions,
    )


def test_update_predictions_with_final_actual_prices() -> None:
  from electricity_predictor.worker.prediction_run_database import (
    update_predictions_with_final_actual_prices,
  )

  cursor = MagicMock()
  cursor.rowcount = 4

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.prediction_run_database."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    updated_rows = (
      update_predictions_with_final_actual_prices()
    )

  cursor.execute.assert_called_once()
  connection.commit.assert_called_once_with()

  assert updated_rows == 4


def test_save_failed_prediction_run() -> None:
  from datetime import UTC

  from electricity_predictor.worker.prediction_run_database import (
    save_failed_prediction_run,
  )

  cursor = MagicMock()
  cursor.fetchone.return_value = (31,)

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  generated_at = datetime(
    2026,
    7,
    17,
    18,
    tzinfo=UTC,
  )

  with patch(
    "electricity_predictor.worker.prediction_run_database."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    run_id = save_failed_prediction_run(
      generated_at=generated_at,
      detail="ValueError: test failure",
    )

  assert run_id == 31
  connection.commit.assert_called_once_with()
