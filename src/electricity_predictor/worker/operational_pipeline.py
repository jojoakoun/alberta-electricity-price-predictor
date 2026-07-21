"""Run the PostgreSQL-first refresh and one production prediction cycle."""

from electricity_predictor.worker.operational_refresh import (
  synchronize_operational_prices,
)
from electricity_predictor.worker.runner import run_worker_cycle


def run_application_pipeline() -> dict:
  """Refresh recent AESO rows before backfill, features, and prediction."""
  synchronized_rows = synchronize_operational_prices()
  worker_result = run_worker_cycle()

  return {
    "synchronized_rows": synchronized_rows,
    **worker_result,
  }


def main() -> None:
  """Run one complete application pipeline."""
  result = run_application_pipeline()

  print(
    f"Application pipeline completed. "
    f"Synchronized rows: {result['synchronized_rows']}. "
    f"Run ID: {result['run_id']}."
  )


if __name__ == "__main__":
  main()
