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
          spike_probability,
          spike_prediction,
          recommendation,
          explanation
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """,
        records,
      )

    connection.commit()

  return run_id
