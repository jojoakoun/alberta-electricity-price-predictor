from pathlib import Path

from electricity_predictor.modeling.lifecycle import (
  candidate,
  manifest,
  runner,
)
from electricity_predictor.modeling.lifecycle.paths import (
  CANDIDATE_ROOT,
  LATEST_SPLIT_MANIFEST_PATH,
  LIFECYCLE_STATE_PATH,
  MANIFEST_DIRECTORY,
)


def test_stable_lifecycle_paths_preserve_exact_values() -> None:
  assert LATEST_SPLIT_MANIFEST_PATH == Path(
    "reports/model_lifecycle/latest_split_manifest.json"
  )
  assert CANDIDATE_ROOT == Path(
    "models/candidates"
  )
  assert LIFECYCLE_STATE_PATH == Path(
    "reports/model_lifecycle/lifecycle_state.json"
  )
  assert MANIFEST_DIRECTORY == Path(
    "reports/model_lifecycle/split_manifests"
  )


def test_lifecycle_modules_share_neutral_path_objects() -> None:
  assert (
    candidate.LATEST_SPLIT_MANIFEST_PATH
    is LATEST_SPLIT_MANIFEST_PATH
  )
  assert candidate.CANDIDATE_ROOT is CANDIDATE_ROOT
  assert (
    runner.LATEST_SPLIT_MANIFEST_PATH
    is LATEST_SPLIT_MANIFEST_PATH
  )
  assert runner.CANDIDATE_ROOT is CANDIDATE_ROOT
  assert runner.LIFECYCLE_STATE_PATH is LIFECYCLE_STATE_PATH
  assert manifest.MANIFEST_DIRECTORY is MANIFEST_DIRECTORY
  assert (
    manifest.LATEST_MANIFEST_PATH
    is LATEST_SPLIT_MANIFEST_PATH
  )
