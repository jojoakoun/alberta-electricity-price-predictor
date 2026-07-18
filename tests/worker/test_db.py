from unittest.mock import patch

from electricity_predictor.worker.db import get_database_connection


def test_get_database_connection_uses_configured_database_url() -> None:
  with (
    patch(
      "electricity_predictor.worker.db.load_database_url",
      return_value="postgres://example",
    ),
    patch(
      "electricity_predictor.worker.db.psycopg.connect"
    ) as connect,
  ):
    get_database_connection()

  connect.assert_called_once_with("postgres://example")
