from datetime import datetime

import pandas as pd

from electricity_predictor.worker.db import get_database_connection


def get_database_time() -> datetime:
  """Return the current PostgreSQL timestamp."""
  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute("SELECT NOW();")
      result = cursor.fetchone()

  if result is None:
    raise RuntimeError("Failed to retrieve the database time.")

  return result[0]


def upsert_hourly_prices(data: pd.DataFrame, source: str = "pipeline") -> int:
  """Insert or update hourly prices and return the synchronized row count."""
  required_columns = {
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
  }

  missing_columns = required_columns - set(data.columns)

  if missing_columns:
    raise ValueError(
      f"Missing hourly price columns: {sorted(missing_columns)}"
    )

  records = [
    (
      row.datetime_universal_time.to_pydatetime(),
      None if pd.isna(row.actual_price) else float(row.actual_price),
      None if pd.isna(row.forecast_price) else float(row.forecast_price),
      (
        None
        if pd.isna(row.alberta_internal_load)
        else float(row.alberta_internal_load)
      ),
      source,
    )
    for row in data.itertuples(index=False)
  ]

  query = """
    INSERT INTO hourly_prices (
      datetime_utc,
      actual_price,
      forecast_price,
      alberta_internal_load,
      source
    )
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (datetime_utc)
    DO UPDATE SET
      actual_price = EXCLUDED.actual_price,
      forecast_price = EXCLUDED.forecast_price,
      alberta_internal_load = EXCLUDED.alberta_internal_load,
      source = EXCLUDED.source;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.executemany(query, records)

    connection.commit()

  return len(records)


def load_hourly_prices(limit: int = 200) -> pd.DataFrame:
  """Load recent hourly prices in chronological order."""
  query = """
    SELECT
      datetime_utc,
      actual_price,
      forecast_price,
      alberta_internal_load,
      source
    FROM (
      SELECT
        datetime_utc,
        actual_price,
        forecast_price,
        alberta_internal_load,
        source
      FROM hourly_prices
      ORDER BY datetime_utc DESC
      LIMIT %s
    ) recent
    ORDER BY datetime_utc;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(query, (limit,))
      rows = cursor.fetchall()

  columns = [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
    "source",
  ]

  data = pd.DataFrame(rows, columns=columns)

  if not data.empty:
    data["datetime_universal_time"] = pd.to_datetime(
      data["datetime_universal_time"],
      utc=True,
    )

  return data


def load_recent_finalized_prices(limit: int) -> pd.Series:
  """Load recent finalized actual prices in chronological order."""
  if limit <= 0:
    raise ValueError("Price limit must be greater than zero.")

  query = """
    SELECT actual_price
    FROM (
      SELECT
        datetime_utc,
        actual_price
      FROM hourly_prices
      WHERE actual_price IS NOT NULL
      ORDER BY datetime_utc DESC
      LIMIT %s
    ) recent
    ORDER BY datetime_utc;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(query, (limit,))
      rows = cursor.fetchall()

  return pd.Series(
    [row[0] for row in rows],
    name="actual_price",
  )


def load_recent_finalized_prices(limit: int) -> pd.Series:
  """Load recent finalized actual prices in chronological order."""
  if limit <= 0:
    raise ValueError("Price limit must be greater than zero.")

  query = """
    SELECT actual_price
    FROM (
      SELECT
        datetime_utc,
        actual_price
      FROM hourly_prices
      WHERE actual_price IS NOT NULL
      ORDER BY datetime_utc DESC
      LIMIT %s
    ) recent
    ORDER BY datetime_utc;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(query, (limit,))
      rows = cursor.fetchall()

  return pd.Series(
    [row[0] for row in rows],
    name="actual_price",
  )
