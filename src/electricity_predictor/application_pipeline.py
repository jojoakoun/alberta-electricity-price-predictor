"""Application pipeline entry point."""

from electricity_predictor.worker.importer import (
  synchronize_current_history,
)
from electricity_predictor.worker.runner import run_worker_cycle


def run_application_pipeline() -> dict:
  """Synchronize application data, then run one prediction cycle."""
  synchronized_rows = synchronize_current_history()
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
