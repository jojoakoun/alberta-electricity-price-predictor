from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from electricity_predictor.worker.result_persistence import (
  save_prediction_run,
)


def build_decisions() -> list[dict]:
  return [
    {
      "horizon_hours": horizon,
      "predicted_price": 70.0 + horizon,
      "spike_probability": 0.1,
      "is_spike": False,
      "spike_threshold": 170.77,
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


def test_save_prediction_run_upserts_and_replaces_horizons() -> None:
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
    "electricity_predictor.worker.result_persistence."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    run_id = save_prediction_run(
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

  connection.commit.assert_called_once()


def test_save_prediction_run_rejects_empty_decisions() -> None:
  with pytest.raises(
    ValueError,
    match="At least one prediction decision is required",
  ):
    save_prediction_run(
      generated_at=datetime.now(
        timezone.utc
      ),
      decisions=[],
    )


def test_save_prediction_run_rejects_incomplete_horizons() -> None:
  with pytest.raises(
    ValueError,
    match=(
      "exactly the horizons "
      "1, 3, 6, 12, and 24 hours"
    ),
  ):
    save_prediction_run(
      generated_at=datetime.now(
        timezone.utc
      ),
      decisions=build_decisions()[:-1],
    )


def test_backfill_prediction_actual_prices() -> None:
  from electricity_predictor.worker.result_persistence import (
    backfill_prediction_actual_prices,
  )

  cursor = MagicMock()
  cursor.rowcount = 4

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.result_persistence."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    updated_rows = (
      backfill_prediction_actual_prices()
    )

  cursor.execute.assert_called_once()
  connection.commit.assert_called_once_with()

  assert updated_rows == 4


def test_save_failed_prediction_run() -> None:
  from datetime import UTC

  from electricity_predictor.worker.result_persistence import (
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
    "electricity_predictor.worker.result_persistence."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    run_id = save_failed_prediction_run(
      generated_at=generated_at,
      detail="ValueError: test failure",
    )

  assert run_id == 31
  connection.commit.assert_called_once_with()
