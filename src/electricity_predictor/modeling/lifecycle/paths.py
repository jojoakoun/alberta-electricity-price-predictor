"""Own stable paths shared across model lifecycle workflows."""

from pathlib import Path


MANIFEST_DIRECTORY = Path(
  "reports/model_lifecycle/split_manifests"
)

LATEST_SPLIT_MANIFEST_PATH = Path(
  "reports/model_lifecycle/latest_split_manifest.json"
)

CANDIDATE_ROOT = Path(
  "models/candidates"
)

LIFECYCLE_STATE_PATH = Path(
  "reports/model_lifecycle/lifecycle_state.json"
)
