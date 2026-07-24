"""Read and synchronize operational hourly prices in PostgreSQL."""

from datetime import datetime

import pandas as pd

from electricity_predictor.storage.postgres import (
  get_database_connection,
)


def get_database_time() -> datetime:
  """Return the current PostgreSQL timestamp."""
  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute("SELECT NOW();")
      result = cursor.fetchone()

  if result is None:
    raise RuntimeError("Failed to retrieve the database time.")

  return result[0]


def get_latest_hourly_price_timestamp() -> datetime | None:
  """Return the newest operational source timestamp in PostgreSQL."""
  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        "SELECT MAX(datetime_utc) FROM hourly_prices;"
      )
      result = cursor.fetchone()

  if result is None or result[0] is None:
    return None

  return result[0]


def upsert_hourly_prices(data: pd.DataFrame, source: str = "pipeline") -> int:
  """Synchronize unique UTC hours under the approved source precedence.

  Incoming actuals only fill null observations; finalized actual prices are
  never replaced. AESO may revise forecasts, while research or seed imports may
  not overwrite a forecast already owned by the operational API.
  """
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

  if data["datetime_universal_time"].duplicated().any():
    raise ValueError(
      "Hourly price synchronization contains duplicate UTC timestamps."
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
      -- A finalized observation is immutable; AESO can only fill a null.
      actual_price = COALESCE(
        hourly_prices.actual_price,
        EXCLUDED.actual_price
      ),
      -- AESO revisions supersede earlier forecasts. A later research import
      -- cannot replace a forecast already synchronized from the API.
      forecast_price = CASE
        WHEN hourly_prices.source = 'aeso_api'
          AND EXCLUDED.source <> 'aeso_api'
        THEN COALESCE(
          hourly_prices.forecast_price,
          EXCLUDED.forecast_price
        )
        ELSE COALESCE(
          EXCLUDED.forecast_price,
          hourly_prices.forecast_price
        )
      END,
      alberta_internal_load = COALESCE(
        EXCLUDED.alberta_internal_load,
        hourly_prices.alberta_internal_load
      ),
      -- Keep source ownership aligned with the forecast-precedence rule.
      source = CASE
        WHEN hourly_prices.source = 'aeso_api'
          AND EXCLUDED.source <> 'aeso_api'
        THEN hourly_prices.source
        ELSE EXCLUDED.source
      END;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.executemany(query, records)

    connection.commit()

  return len(records)


def load_inference_hourly_prices(
  lookback_hours: int,
) -> pd.DataFrame:
  """Load support ending at the latest available market hour."""
  if lookback_hours <= 0:
    raise ValueError(
      "Inference lookback hours must be greater than zero."
    )

  query = """
    WITH inference_bounds AS (
      SELECT
        MAX(datetime_utc) FILTER (WHERE datetime_utc <= DATE_TRUNC('hour', CURRENT_TIMESTAMP)) AS candidate_utc
      FROM hourly_prices
    )
    SELECT
      hourly_prices.datetime_utc,
      hourly_prices.actual_price,
      hourly_prices.forecast_price,
      hourly_prices.alberta_internal_load,
      hourly_prices.source,
      inference_bounds.candidate_utc AS inference_candidate_utc
    FROM hourly_prices
    CROSS JOIN inference_bounds
    WHERE inference_bounds.candidate_utc IS NOT NULL
      AND hourly_prices.datetime_utc BETWEEN
        inference_bounds.candidate_utc
          - (%s * INTERVAL '1 hour')
        AND inference_bounds.candidate_utc
    ORDER BY hourly_prices.datetime_utc;
  """

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        query,
        (lookback_hours,),
      )
      rows = cursor.fetchall()

  columns = [
    "datetime_universal_time",
    "actual_price",
    "forecast_price",
    "alberta_internal_load",
    "source",
    "inference_candidate_utc",
  ]

  data = pd.DataFrame(
    rows,
    columns=columns,
  )

  if data.empty:
    return data.drop(
      columns=[
        "inference_candidate_utc"
      ]
    )

  data[
    "datetime_universal_time"
  ] = pd.to_datetime(
    data[
      "datetime_universal_time"
    ],
    utc=True,
  )

  candidate_timestamp = pd.to_datetime(
    data[
      "inference_candidate_utc"
    ].iloc[0],
    utc=True,
  )

  data = data.drop(
    columns=[
      "inference_candidate_utc"
    ]
  )

  data.attrs[
    "inference_candidate_utc"
  ] = candidate_timestamp

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
