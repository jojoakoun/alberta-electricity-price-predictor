from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from electricity_predictor.worker.hourly_price_database import (
  get_current_database_time,
  get_latest_hourly_price_timestamp,
  load_hourly_prices_for_prediction,
  insert_or_update_hourly_prices,
)


def test_get_current_database_time_returns_timestamp() -> None:
  expected = datetime(2026, 7, 17, tzinfo=timezone.utc)

  cursor = MagicMock()
  cursor.fetchone.return_value = (expected,)

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.hourly_price_database.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    result = get_current_database_time()

  assert result == expected


def test_get_latest_hourly_price_timestamp_reads_postgresql_maximum() -> None:
  expected = datetime(2026, 7, 20, 13, tzinfo=timezone.utc)

  cursor = MagicMock()
  cursor.fetchone.return_value = (expected,)

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.hourly_price_database.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    result = get_latest_hourly_price_timestamp()

  assert result == expected
  assert "MAX(datetime_utc)" in cursor.execute.call_args.args[0]


def test_insert_or_update_hourly_prices_synchronizes_rows() -> None:
  data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        ["2026-07-17 00:00:00", "2026-07-17 01:00:00"],
        utc=True,
      ),
      "actual_price": [40.0, None],
      "forecast_price": [38.0, 42.0],
      "alberta_internal_load": [8100.0, None],
    }
  )

  cursor = MagicMock()
  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.hourly_price_database.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    synchronized_rows = insert_or_update_hourly_prices(data)

  assert synchronized_rows == 2
  cursor.executemany.assert_called_once()
  connection.commit.assert_called_once()

  upsert_query = cursor.executemany.call_args.args[0]
  normalized_query = (
    " ".join(upsert_query.split())
    .replace("( ", "(")
    .replace(" )", ")")
  )

  assert (
    "actual_price = COALESCE("
    "hourly_prices.actual_price, EXCLUDED.actual_price)"
    in normalized_query
  )
  assert (
    "WHEN hourly_prices.source = 'aeso_api' "
    "AND EXCLUDED.source <> 'aeso_api'"
    in normalized_query
  )
  assert (
    "alberta_internal_load = COALESCE("
    "EXCLUDED.alberta_internal_load, "
    "hourly_prices.alberta_internal_load)"
    in normalized_query
  )
  assert "source = CASE" in normalized_query
  assert "THEN hourly_prices.source" in normalized_query
  assert "ON CONFLICT (datetime_utc)" in upsert_query



def test_load_hourly_prices_for_prediction_uses_database_candidate_window() -> None:
  candidate = datetime(
    2026,
    7,
    20,
    14,
    tzinfo=timezone.utc,
  )

  rows = [
    (
      datetime(
        2026,
        7,
        13,
        14,
        tzinfo=timezone.utc,
      ),
      40.0,
      38.0,
      8100.0,
      "aeso_api",
      candidate,
    ),
    (
      candidate,
      None,
      42.0,
      None,
      "aeso_api",
      candidate,
    ),
  ]

  cursor = MagicMock()
  cursor.fetchall.return_value = rows

  connection = MagicMock()

  connection.cursor.return_value.__enter__.return_value = (
    cursor
  )

  with patch(
    "electricity_predictor.worker.hourly_price_database."
    "get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = (
      connection
    )

    result = load_hourly_prices_for_prediction(
      lookback_hours=168
    )

  query, parameters = (
    cursor.execute.call_args.args
  )

  normalized_query = " ".join(
    query.split()
  )

  assert (
    "MAX(datetime_utc) FILTER "
    "(WHERE datetime_utc <= "
    "DATE_TRUNC('hour', CURRENT_TIMESTAMP)) "
    "AS candidate_utc"
    in normalized_query
  )

  assert (
    "inference_candidate_utc"
    in normalized_query
  )

  assert parameters == (168,)
  assert len(result) == 2

  assert (
    result.attrs[
      "inference_candidate_utc"
    ]
    == pd.Timestamp(candidate)
  )

  assert (
    "inference_candidate_utc"
    not in result.columns
  )


def test_repeated_hourly_price_upsert_uses_the_same_conflict_records() -> None:
  data = pd.DataFrame(
    {
      "datetime_universal_time": pd.to_datetime(
        ["2026-07-17 00:00:00"],
        utc=True,
      ),
      "actual_price": [40.0],
      "forecast_price": [39.0],
      "alberta_internal_load": [8100.0],
    }
  )

  cursor = MagicMock()
  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.hourly_price_database.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    first_count = insert_or_update_hourly_prices(data)
    second_count = insert_or_update_hourly_prices(data)

  assert first_count == second_count == 1
  assert cursor.executemany.call_count == 2
  assert (
    cursor.executemany.call_args_list[0].args[1]
    == cursor.executemany.call_args_list[1].args[1]
  )
  assert all(
    "ON CONFLICT (datetime_utc)" in call_args.args[0]
    for call_args in cursor.executemany.call_args_list
  )


def test_insert_or_update_hourly_prices_rejects_missing_columns() -> None:
  with pytest.raises(ValueError, match="Missing hourly price columns"):
    insert_or_update_hourly_prices(pd.DataFrame({"actual_price": [40.0]}))


def test_insert_or_update_hourly_prices_rejects_duplicate_timestamps() -> None:
  timestamp = pd.Timestamp("2026-07-17 00:00:00", tz="UTC")
  data = pd.DataFrame(
    {
      "datetime_universal_time": [timestamp, timestamp],
      "actual_price": [40.0, 41.0],
      "forecast_price": [38.0, 39.0],
      "alberta_internal_load": [8100.0, 8101.0],
    }
  )

  with pytest.raises(
    ValueError,
    match="duplicate UTC timestamps",
  ):
    insert_or_update_hourly_prices(data)
