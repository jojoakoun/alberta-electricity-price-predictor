from unittest.mock import patch

from electricity_predictor.application_pipeline import (
  run_application_pipeline,
)


def test_run_application_pipeline_synchronizes_then_runs_worker() -> None:
  worker_result = {
    "run_id": 42,
    "decisions": [],
  }

  with (
    patch(
      "electricity_predictor.application_pipeline.synchronize_current_history",
      return_value=57347,
    ) as synchronize,
    patch(
      "electricity_predictor.application_pipeline.run_worker_cycle",
      return_value=worker_result,
    ) as worker,
  ):
    result = run_application_pipeline()

  synchronize.assert_called_once_with()
  worker.assert_called_once_with()

  assert result == {
    "synchronized_rows": 57347,
    "run_id": 42,
    "decisions": [],
  }
