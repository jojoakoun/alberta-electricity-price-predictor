from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from electricity_predictor.worker.result_persistence import (
  save_prediction_run,
)


def test_save_prediction_run_inserts_run_and_horizon_decisions() -> None:
  generated_at = datetime(
    2026,
    7,
    17,
    18,
    0,
    tzinfo=timezone.utc,
  )

  decisions = [
    {
      "horizon_hours": 1,
      "predicted_price": 77.19,
      "spike_probability": 0.245,
      "is_spike": False,
      "spike_threshold": 170.77,
      "recommendation": "Recommended",
      "explanation": "Low spike probability.",
    },
    {
      "horizon_hours": 3,
      "predicted_price": 180.37,
      "spike_probability": 0.476,
      "is_spike": True,
      "spike_threshold": 170.77,
      "recommendation": "Avoid",
      "explanation": "High spike probability.",
    },
  ]

  cursor = MagicMock()
  cursor.fetchone.return_value = (12,)

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.result_persistence.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    run_id = save_prediction_run(
      generated_at=generated_at,
      decisions=decisions,
      confidence="medium",
    )

  records = cursor.executemany.call_args.args[1]

  assert run_id == 12
  assert records[0][2].hour == 19
  assert records[1][2].hour == 21
  connection.commit.assert_called_once()


def test_save_prediction_run_rejects_empty_decisions() -> None:
  with pytest.raises(
    ValueError,
    match="At least one prediction decision is required",
  ):
    save_prediction_run(
      generated_at=datetime.now(timezone.utc),
      decisions=[],
    )


def test_backfill_prediction_actual_prices() -> None:
  from unittest.mock import MagicMock, patch

  from electricity_predictor.worker.result_persistence import (
    backfill_prediction_actual_prices,
  )

  cursor = MagicMock()
  cursor.rowcount = 4

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.result_persistence.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    updated_rows = backfill_prediction_actual_prices()

  cursor.execute.assert_called_once()
  connection.commit.assert_called_once_with()
  assert updated_rows == 4


def test_save_failed_prediction_run() -> None:
  from datetime import UTC, datetime
  from unittest.mock import MagicMock, patch

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
