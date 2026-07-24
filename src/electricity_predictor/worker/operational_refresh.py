"""Incrementally synchronize operational AESO prices with PostgreSQL."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd

from electricity_predictor.data.aeso_api import (
  fetch_pool_price_report,
  normalize_pool_price_report,
)
from electricity_predictor.worker.hourly_price_database import (
  get_latest_hourly_price_timestamp,
  insert_or_update_hourly_prices,
)


ALBERTA_TIMEZONE = ZoneInfo("America/Edmonton")
OPERATIONAL_REFRESH_OVERLAP_DAYS = 2


def derive_api_start_date(
  latest_database_timestamp: datetime | pd.Timestamp,
) -> str:
  """Return a bounded Alberta start date derived from PostgreSQL state.

  The overlap captures recent actual-price finalizations and forecast revisions
  without downloading or rewriting the full historical dataset.
  """
  latest_timestamp = pd.Timestamp(
    latest_database_timestamp
  )

  if pd.isna(latest_timestamp):
    raise ValueError(
      "Latest database timestamp must not be missing."
    )

  if latest_timestamp.tzinfo is None:
    latest_timestamp = latest_timestamp.tz_localize(
      "UTC"
    )
  else:
    latest_timestamp = latest_timestamp.tz_convert(
      "UTC"
    )

  latest_alberta_date = latest_timestamp.tz_convert(
    ALBERTA_TIMEZONE
  ).normalize()
  overlap_start = latest_alberta_date - pd.Timedelta(
    days=OPERATIONAL_REFRESH_OVERLAP_DAYS
  )

  return overlap_start.strftime("%Y-%m-%d")


def get_current_api_end_date() -> str:
  """Return the current Alberta market date for AESO."""
  return datetime.now(
    ALBERTA_TIMEZONE
  ).strftime("%Y-%m-%d")


def build_operational_hourly_price_rows(
  api_data: pd.DataFrame,
) -> pd.DataFrame:
  """Build normalized AESO rows for the operational PostgreSQL schema."""
  operational_data = api_data.copy()

  operational_data[
    "datetime_universal_time"
  ] = pd.to_datetime(
    operational_data[
      "datetime_universal_time"
    ],
    utc=True,
  )

  # This AESO report does not carry actual AIL. Preserve any database value
  # during the conflict update instead of manufacturing one.
  operational_data[
    "alberta_internal_load"
  ] = pd.NA

  return operational_data[
    [
      "datetime_universal_time",
      "actual_price",
      "forecast_price",
      "alberta_internal_load",
    ]
  ].sort_values(
    "datetime_universal_time"
  ).reset_index(drop=True)


def synchronize_operational_prices(
  end_date: str | None = None,
) -> int:
  """Synchronize a bounded AESO overlap into operational PostgreSQL.

  PostgreSQL is the recurring worker's source of truth. An empty table is an
  explicit seed prerequisite failure, never a reason to read a deployment CSV.
  """
  latest_database_timestamp = (
    get_latest_hourly_price_timestamp()
  )

  if latest_database_timestamp is None:
    raise RuntimeError(
      "PostgreSQL contains no hourly prices; run the one-time "
      "historical database seed before the operational worker."
    )

  start_date = derive_api_start_date(
    latest_database_timestamp
  )

  if end_date is None:
    end_date = get_current_api_end_date()

  api_report = fetch_pool_price_report(
    start_date=start_date,
    end_date=end_date,
  )
  api_data = normalize_pool_price_report(
    api_report
  )
  operational_data = build_operational_hourly_price_rows(
    api_data
  )

  return insert_or_update_hourly_prices(
    data=operational_data,
    source="aeso_api",
  )
