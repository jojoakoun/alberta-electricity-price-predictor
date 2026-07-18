import psycopg
from psycopg import Connection

from electricity_predictor.config import load_database_url


def get_database_connection() -> Connection:
  """Return a new PostgreSQL connection."""
  return psycopg.connect(load_database_url())
