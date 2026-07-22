from importlib.util import find_spec
from unittest.mock import patch

import pytest

from electricity_predictor.modeling.decision import (
  analyze_decision_windows,
)
from electricity_predictor.storage import postgres
from electricity_predictor.storage.postgres import (
  get_database_connection,
)
from electricity_predictor.worker import (
  persistence,
  result_persistence,
)


def test_postgres_module_exposes_connection_boundary() -> None:
  assert callable(postgres.get_database_connection)
  assert postgres.get_database_connection is get_database_connection


def test_old_worker_database_module_is_absent() -> None:
  assert find_spec(
    "electricity_predictor.worker.db"
  ) is None


def test_consumers_import_shared_postgres_connection() -> None:
  assert (
    persistence.get_database_connection
    is get_database_connection
  )
  assert (
    result_persistence.get_database_connection
    is get_database_connection
  )
  assert (
    analyze_decision_windows.get_database_connection
    is get_database_connection
  )


def test_get_database_connection_uses_configured_database_url() -> None:
  with (
    patch(
      "electricity_predictor.storage.postgres.load_database_url",
      return_value="postgres://example",
    ),
    patch(
      "electricity_predictor.storage.postgres.psycopg.connect"
    ) as connect,
  ):
    get_database_connection()

  connect.assert_called_once_with("postgres://example")


def test_get_database_connection_preserves_missing_url_error() -> None:
  missing_url_error = RuntimeError(
    "DATABASE_URL environment variable is required."
  )

  with (
    patch(
      "electricity_predictor.storage.postgres.load_database_url",
      side_effect=missing_url_error,
    ),
    patch(
      "electricity_predictor.storage.postgres.psycopg.connect"
    ) as connect,
  ):
    with pytest.raises(RuntimeError) as error:
      get_database_connection()

  assert error.value is missing_url_error
  assert str(error.value) == (
    "DATABASE_URL environment variable is required."
  )
  connect.assert_not_called()


def test_get_database_connection_preserves_driver_error() -> None:
  driver_error = ValueError(
    "invalid connection configuration"
  )

  with (
    patch(
      "electricity_predictor.storage.postgres.load_database_url",
      return_value="invalid://configuration",
    ),
    patch(
      "electricity_predictor.storage.postgres.psycopg.connect",
      side_effect=driver_error,
    ),
  ):
    with pytest.raises(ValueError) as error:
      get_database_connection()

  assert error.value is driver_error
  assert str(error.value) == (
    "invalid connection configuration"
  )
