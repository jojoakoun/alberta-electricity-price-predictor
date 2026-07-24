"""Refresh operational prices and run one application prediction cycle."""

from electricity_predictor.worker.operational_refresh import (
  synchronize_operational_prices,
)
from electricity_predictor.worker.prediction_cycle import run_prediction_cycle


def run_application_prediction_pipeline() -> dict:
  """Refresh recent AESO rows before backfill, features, and prediction."""
  synchronized_rows = synchronize_operational_prices()
  worker_result = run_prediction_cycle()

  return {
    "synchronized_rows": synchronized_rows,
    **worker_result,
  }


def main() -> None:
  """Run one complete application pipeline."""
  result = run_application_prediction_pipeline()

  print(
    f"Application pipeline completed. "
    f"Synchronized rows: {result['synchronized_rows']}. "
    f"Run ID: {result['run_id']}."
  )


if __name__ == "__main__":
  main()
