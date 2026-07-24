"""Save complete prediction runs and finalized outcomes in PostgreSQL."""

import json
from datetime import datetime, timedelta

from electricity_predictor.features.feature_columns import (
  SUPPORTED_FORECAST_HORIZONS_HOURS,
)
from electricity_predictor.storage.postgres import (
  get_database_connection,
)


FORECAST_KINDS = frozenset({
  "model_forecast",
  "persistence_reference",
})


def _validate_prediction_decisions(
  decisions: list[dict],
) -> list[dict]:
  """Return decisions ordered only when all supported horizons are present."""
  if not decisions:
    raise ValueError(
      "At least one prediction decision is required."
    )

  ordered_decisions = sorted(
    decisions,
    key=lambda decision: int(
      decision["horizon_hours"]
    ),
  )

  horizons = tuple(
    int(decision["horizon_hours"])
    for decision in ordered_decisions
  )

  if horizons != SUPPORTED_FORECAST_HORIZONS_HOURS:
    supported_horizons = ", ".join(
      str(horizon_hours)
      for horizon_hours in SUPPORTED_FORECAST_HORIZONS_HOURS
    )
    raise ValueError(
      "Prediction decisions must contain exactly the horizons "
      f"{supported_horizons} hours."
    )

  return ordered_decisions


def _build_prediction_run_detail(
  decisions: list[dict],
  summary: str | None,
) -> str:
  """Serialize per-horizon provenance for fail-closed API interpretation."""
  forecast_kinds: dict[str, str] = {}

  for decision in decisions:
    forecast_kind = decision.get("forecast_kind")

    if forecast_kind not in FORECAST_KINDS:
      raise ValueError(
        f"Unsupported forecast kind: {forecast_kind!r}."
      )

    forecast_kinds[
      str(int(decision["horizon_hours"]))
    ] = forecast_kind

  return json.dumps(
    {
      "schemaVersion": 1,
      "summary": summary,
      "forecastKinds": forecast_kinds,
    },
    separators=(",", ":"),
    sort_keys=True,
  )


def save_successful_prediction_run(
  generated_at: datetime,
  decisions: list[dict],
  confidence: str | None = None,
  detail: str | None = None,
) -> int:
  """Atomically create or replace one successful five-horizon run.

  ``generated_at`` is the forecast source market hour. Repeating that source
  hour reuses the successful run and replaces all five predictions in one
  transaction, so readers never observe a partial horizon set.
  """
  ordered_decisions = _validate_prediction_decisions(
    decisions
  )
  run_detail = _build_prediction_run_detail(
    decisions=ordered_decisions,
    summary=detail,
  )

  spike_threshold = ordered_decisions[0].get(
    "spike_threshold"
  )

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
        VALUES (%s, 'success', %s, %s, %s)
        -- Match the partial unique index that permits multiple failed attempts
        -- while allowing only one successful run per forecast source hour.
        ON CONFLICT (generated_at)
          WHERE status = 'success'
        DO UPDATE SET
          confidence = EXCLUDED.confidence,
          spike_threshold = EXCLUDED.spike_threshold,
          detail = EXCLUDED.detail
        RETURNING id;
        """,
        (
          generated_at,
          confidence,
          spike_threshold,
          run_detail,
        ),
      )

      run_row = cursor.fetchone()

      if run_row is None:
        raise RuntimeError(
          "Failed to create prediction run."
        )

      run_id = int(run_row[0])

      # Reused runs replace their complete prediction set atomically. Deleting
      # first prevents stale horizons from surviving a retry.
      cursor.execute(
        """
        DELETE FROM predictions
        WHERE prediction_run_id = %s;
        """,
        (run_id,),
      )

      records = [
        (
          run_id,
          int(decision["horizon_hours"]),
          generated_at
          + timedelta(
            hours=int(
              decision["horizon_hours"]
            )
          ),
          float(decision["predicted_price"]),
          float(decision["spike_probability"]),
          bool(decision["is_spike"]),
          decision["recommendation"],
          decision["explanation"],
        )
        for decision in ordered_decisions
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
        VALUES (
          %s,
          %s,
          %s,
          %s,
          NULL,
          %s,
          %s,
          %s,
          %s
        );
        """,
        records,
      )

    connection.commit()

  return run_id


def update_predictions_with_final_actual_prices() -> int:
  """Update predictions that are missing their finalized actual prices.

  Existing prediction outcomes are immutable, and no forecast or synthetic
  value may stand in for a missing actual price.
  """
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
  """Preserve one failed attempt without prediction rows or success reuse.

  The timestamp is the source hour when one was selected, otherwise the attempt
  time. Failed rows are not eligible for forecast freshness or idempotent reuse.
  """
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
        raise RuntimeError(
          "Failed to create failed prediction run."
        )

      run_id = int(run_row[0])

    connection.commit()

  return run_id
