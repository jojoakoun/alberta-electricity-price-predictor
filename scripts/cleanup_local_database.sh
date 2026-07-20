#!/usr/bin/env bash

set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  if [[ ! -f ".env" ]]; then
    echo "Error: DATABASE_URL is missing and .env was not found."
    exit 1
  fi

  DATABASE_URL="$(
    python3 - <<'PY'
from pathlib import Path

for raw_line in Path(".env").read_text().splitlines():
    line = raw_line.strip()

    if not line or line.startswith("#"):
        continue

    if line.startswith("DATABASE_URL="):
        value = line.split("=", 1)[1].strip().strip("'\"")

        if not value:
            raise SystemExit("DATABASE_URL is empty in .env.")

        print(value)
        raise SystemExit

raise SystemExit("DATABASE_URL was not found in .env.")
PY
  )"
fi

export DATABASE_URL

python3 - <<'PY'
import os
from urllib.parse import urlparse

parsed = urlparse(os.environ["DATABASE_URL"])

allowed_hosts = {
    "localhost",
    "127.0.0.1",
}

if parsed.hostname not in allowed_hosts:
    raise SystemExit(
        "Cleanup aborted: DATABASE_URL does not point "
        f"to a local database. Host: {parsed.hostname!r}"
    )

database_name = parsed.path.lstrip("/")

if database_name != "wattwise":
    raise SystemExit(
        "Cleanup aborted: expected database 'wattwise', "
        f"found {database_name!r}."
    )

print(
    "Local database confirmed: "
    f"{parsed.hostname}:{parsed.port}/{database_name}"
)
PY

if [[ "${CONFIRM_DB_CLEANUP:-}" != "YES" ]]; then
  echo
  echo "This command will delete all local application data."
  echo "The schema and migration history will remain."
  echo
  echo "Run:"
  echo "  make db-clean CONFIRM=YES"
  exit 1
fi

echo
echo "===== COUNTS BEFORE CLEANUP ====="

psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
    SELECT
      (SELECT COUNT(*) FROM hourly_prices)
        AS hourly_prices,
      (SELECT COUNT(*) FROM prediction_runs)
        AS prediction_runs,
      (SELECT COUNT(*) FROM predictions)
        AS predictions;
  "

echo
echo "===== CLEANING LOCAL DATABASE ====="

psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -P pager=off <<'SQL'
BEGIN;

TRUNCATE TABLE
  predictions,
  prediction_runs,
  hourly_prices
RESTART IDENTITY CASCADE;

COMMIT;
SQL

echo
echo "===== COUNTS AFTER CLEANUP ====="

psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -P pager=off \
  -c "
    SELECT
      (SELECT COUNT(*) FROM hourly_prices)
        AS hourly_prices,
      (SELECT COUNT(*) FROM prediction_runs)
        AS prediction_runs,
      (SELECT COUNT(*) FROM predictions)
        AS predictions;
  "

echo
echo "Local WattWise database cleanup completed."
