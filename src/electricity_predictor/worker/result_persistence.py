from datetime import datetime, timedelta

from electricity_predictor.worker.db import get_database_connection


def save_prediction_run(
  generated_at: datetime,
  decisions: list[dict],
  status: str = "success",
  confidence: str | None = None,
  detail: str | None = None,
) -> int:
  """Save one prediction run and all horizon decisions."""
  if not decisions:
    raise ValueError("At least one prediction decision is required.")

  spike_threshold = decisions[0].get("spike_threshold")

  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        """
        INSERT INTO prediction_runs (
          generated_at,
          status,
          confidence,
          spike_threshold,
          detail
        )
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
          generated_at,
          status,
          confidence,
          spike_threshold,
          detail,
        ),
      )

      run_row = cursor.fetchone()

      if run_row is None:
        raise RuntimeError("Failed to create prediction run.")

      run_id = int(run_row[0])

      records = [
        (
          run_id,
          int(decision["horizon_hours"]),
          generated_at + timedelta(
            hours=int(decision["horizon_hours"])
          ),
          float(decision["predicted_price"]),
          float(decision["spike_probability"]),
          bool(decision["is_spike"]),
          decision["recommendation"],
          decision["explanation"],
        )
        for decision in decisions
      ]

      cursor.executemany(
        """
        INSERT INTO predictions (
          prediction_run_id,
          horizon_hours,
          target_time_utc,
          predicted_price,
          actual_price,
          spike_probability,
          spike_prediction,
          recommendation,
          explanation
        )
        VALUES (%s, %s, %s, %s, NULL, %s, %s, %s, %s);
        """,
        records,
      )

    connection.commit()

  return run_id


def backfill_prediction_actual_prices() -> int:
  """Fill completed predictions with their observed actual prices."""
  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        """
        UPDATE predictions AS prediction
        SET actual_price = hourly.actual_price
        FROM hourly_prices AS hourly
        WHERE prediction.target_time_utc = hourly.datetime_utc
          AND prediction.actual_price IS NULL
          AND hourly.actual_price IS NOT NULL;
        """
      )

      updated_rows = cursor.rowcount

    connection.commit()

  return updated_rows


def save_failed_prediction_run(
  generated_at: datetime,
  detail: str,
) -> int:
  """Save one failed worker run without prediction rows."""
  with get_database_connection() as connection:
    with connection.cursor() as cursor:
      cursor.execute(
        """
        INSERT INTO prediction_runs (
          generated_at,
          status,
          confidence,
          spike_threshold,
          detail
        )
        VALUES (%s, 'failed', NULL, NULL, %s)
        RETURNING id;
        """,
        (
          generated_at,
          detail,
        ),
      )

      run_row = cursor.fetchone()

      if run_row is None:
        raise RuntimeError("Failed to create failed prediction run.")

      run_id = int(run_row[0])

    connection.commit()

  return run_id
