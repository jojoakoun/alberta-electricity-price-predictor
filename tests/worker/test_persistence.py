from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from electricity_predictor.worker.persistence import (
  get_database_time,
  upsert_hourly_prices,
)


def test_get_database_time_returns_timestamp() -> None:
  expected = datetime(2026, 7, 17, tzinfo=timezone.utc)

  cursor = MagicMock()
  cursor.fetchone.return_value = (expected,)

  connection = MagicMock()
  connection.cursor.return_value.__enter__.return_value = cursor

  with patch(
    "electricity_predictor.worker.persistence.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    result = get_database_time()

  assert result == expected


def test_upsert_hourly_prices_synchronizes_rows() -> None:
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
    "electricity_predictor.worker.persistence.get_database_connection"
  ) as get_connection:
    get_connection.return_value.__enter__.return_value = connection

    synchronized_rows = upsert_hourly_prices(data)

  assert synchronized_rows == 2
  cursor.executemany.assert_called_once()
  connection.commit.assert_called_once()


def test_upsert_hourly_prices_rejects_missing_columns() -> None:
  with pytest.raises(ValueError, match="Missing hourly price columns"):
    upsert_hourly_prices(pd.DataFrame({"actual_price": [40.0]}))
