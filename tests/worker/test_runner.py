from unittest.mock import patch

import pandas as pd

from electricity_predictor.worker.runner import run_worker_cycle


def test_run_worker_cycle_returns_latest_feature_row() -> None:
  features = pd.DataFrame(
    {
      "feature": [1, 2, 3],
    }
  )

  with patch(
    "electricity_predictor.worker.runner.prepare_model_features",
    return_value=features,
  ) as prepare_features:
    latest = run_worker_cycle()

  prepare_features.assert_called_once_with()

  assert len(latest) == 1
  assert latest.iloc[0]["feature"] == 3
