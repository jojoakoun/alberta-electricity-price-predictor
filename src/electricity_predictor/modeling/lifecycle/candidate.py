from datetime import UTC, datetime
import json
from pathlib import Path

from electricity_predictor.config import (
  load_configuration,
)
from electricity_predictor.modeling.lifecycle.paths import (
  CANDIDATE_ROOT,
  LATEST_SPLIT_MANIFEST_PATH,
)


REGRESSION_CHAMPION_METADATA_PATH = Path(
  "models/regression/"
  "selected_regression_model_metadata.csv"
)

CLASSIFICATION_CHAMPION_METADATA_PATH = Path(
  "models/classification/"
  "selected_classification_model_metadata.csv"
)


def read_json_file(
  file_path: Path,
) -> dict:
  """Read one JSON object from disk."""
  if not file_path.exists():
    raise FileNotFoundError(
      f"JSON file not found: {file_path}"
    )

  content = json.loads(
    file_path.read_text(
      encoding="utf-8"
    )
  )

  if not isinstance(content, dict):
    raise ValueError(
      f"Expected a JSON object in {file_path}."
    )

  return content


def write_json_file(
  content: dict,
  file_path: Path,
) -> Path:
  """Write one consistently formatted JSON object."""
  file_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  file_path.write_text(
    json.dumps(
      content,
      indent=2,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
  )

  return file_path


def validate_split_manifest(
  split_manifest: dict,
) -> None:
  """Validate the fields required for a candidate run."""
  required_top_level = {
    "dataset",
    "plan",
    "schema_version",
    "split_version",
    "splits",
    "strategy",
  }

  missing_top_level = (
    required_top_level
    - set(split_manifest)
  )

  if missing_top_level:
    raise ValueError(
      "Split manifest is missing required fields: "
      f"{sorted(missing_top_level)}"
    )

  required_dataset_fields = {
    "path",
    "sha256",
    "version",
    "row_count",
    "start_utc",
    "end_utc",
  }

  missing_dataset_fields = (
    required_dataset_fields
    - set(split_manifest["dataset"])
  )

  if missing_dataset_fields:
    raise ValueError(
      "Split manifest dataset is missing fields: "
      f"{sorted(missing_dataset_fields)}"
    )

  required_splits = {
    "train",
    "validation",
    "test",
  }

  missing_splits = (
    required_splits
    - set(split_manifest["splits"])
  )

  if missing_splits:
    raise ValueError(
      "Split manifest is missing splits: "
      f"{sorted(missing_splits)}"
    )


def build_candidate_model_version(
  split_version: str,
) -> str:
  """Build a deterministic candidate model version."""
  normalized_version = str(
    split_version
  ).strip()

  if not normalized_version:
    raise ValueError(
      "split_version must not be empty."
    )

  return (
    f"candidate-{normalized_version}"
  )


def build_candidate_manifest(
  split_manifest: dict,
  source_split_manifest_path: Path,
  candidate_root: Path,
  promotion_mode: str,
  created_at_utc: str | None = None,
) -> dict:
  """Build metadata for an isolated candidate run."""
  validate_split_manifest(
    split_manifest
  )

  model_version = (
    build_candidate_model_version(
      split_manifest["split_version"]
    )
  )

  candidate_directory = (
    candidate_root / model_version
  )

  created_at = (
    created_at_utc
    or datetime.now(UTC).isoformat()
  )

  return {
    "schema_version": 1,
    "model_version": model_version,
    "status": "prepared",
    "created_at_utc": created_at,
    "promotion_mode": promotion_mode,
    "dataset_version": (
      split_manifest["dataset"][
        "version"
      ]
    ),
    "dataset_sha256": (
      split_manifest["dataset"][
        "sha256"
      ]
    ),
    "split_version": (
      split_manifest["split_version"]
    ),
    "source_split_manifest_path": str(
      source_split_manifest_path
    ),
    "frozen_split_manifest_path": str(
      candidate_directory
      / "split_manifest.json"
    ),
    "candidate_directory": str(
      candidate_directory
    ),
    "tasks": {
      "regression": {
        "status": "pending",
        "artifact_directory": str(
          candidate_directory
          / "regression"
        ),
        "report_directory": str(
          candidate_directory
          / "reports"
          / "regression"
        ),
        "metadata_path": str(
          candidate_directory
          / "regression"
          / "selected_regression_model_metadata.csv"
        ),
      },
      "classification": {
        "status": "pending",
        "artifact_directory": str(
          candidate_directory
          / "classification"
        ),
        "report_directory": str(
          candidate_directory
          / "reports"
          / "classification"
        ),
        "metadata_path": str(
          candidate_directory
          / "classification"
          / "selected_classification_model_metadata.csv"
        ),
      },
    },
    "current_champion": {
      "status": "legacy_unversioned",
      "regression_metadata_path": str(
        REGRESSION_CHAMPION_METADATA_PATH
      ),
      "classification_metadata_path": str(
        CLASSIFICATION_CHAMPION_METADATA_PATH
      ),
    },
  }


def prepare_candidate_run(
  split_manifest_path: Path = (
    LATEST_SPLIT_MANIFEST_PATH
  ),
  candidate_root: Path = (
    CANDIDATE_ROOT
  ),
  promotion_mode: str | None = None,
  created_at_utc: str | None = None,
) -> tuple[Path, Path, dict]:
  """Prepare one isolated candidate directory."""
  split_manifest = read_json_file(
    split_manifest_path
  )

  resolved_promotion_mode = (
    promotion_mode
  )

  if resolved_promotion_mode is None:
    configuration = (
      load_configuration()
    )

    resolved_promotion_mode = (
      configuration[
        "model_lifecycle"
      ][
        "promotion_mode"
      ]
    )

  candidate_manifest = (
    build_candidate_manifest(
      split_manifest=split_manifest,
      source_split_manifest_path=(
        split_manifest_path
      ),
      candidate_root=candidate_root,
      promotion_mode=(
        resolved_promotion_mode
      ),
      created_at_utc=created_at_utc,
    )
  )

  candidate_directory = Path(
    candidate_manifest[
      "candidate_directory"
    ]
  )

  candidate_manifest_path = (
    candidate_directory
    / "candidate_manifest.json"
  )

  frozen_split_manifest_path = (
    candidate_directory
    / "split_manifest.json"
  )

  # The same split version maps to one stable candidate.
  if candidate_manifest_path.exists():
    existing_manifest = read_json_file(
      candidate_manifest_path
    )

    if (
      existing_manifest.get(
        "split_version"
      )
      != split_manifest[
        "split_version"
      ]
    ):
      raise ValueError(
        "Existing candidate uses a different "
        "split version."
      )

    return (
      candidate_manifest_path,
      frozen_split_manifest_path,
      existing_manifest,
    )

  for directory in [
    candidate_directory
    / "regression",
    candidate_directory
    / "classification",
    candidate_directory
    / "reports"
    / "regression",
    candidate_directory
    / "reports"
    / "classification",
  ]:
    directory.mkdir(
      parents=True,
      exist_ok=True,
    )

  write_json_file(
    content=split_manifest,
    file_path=(
      frozen_split_manifest_path
    ),
  )

  write_json_file(
    content=candidate_manifest,
    file_path=(
      candidate_manifest_path
    ),
  )

  return (
    candidate_manifest_path,
    frozen_split_manifest_path,
    candidate_manifest,
  )


def print_candidate_summary(
  candidate_manifest: dict,
) -> None:
  """Print the prepared candidate identity."""
  print("Model lifecycle candidate")
  print("=========================")

  print(
    "Model version: "
    f"{candidate_manifest['model_version']}"
  )

  print(
    "Dataset version: "
    f"{candidate_manifest['dataset_version']}"
  )

  print(
    "Split version: "
    f"{candidate_manifest['split_version']}"
  )

  print(
    "Status: "
    f"{candidate_manifest['status']}"
  )

  print(
    "Promotion mode: "
    f"{candidate_manifest['promotion_mode']}"
  )

  for task_name in [
    "regression",
    "classification",
  ]:
    task = (
      candidate_manifest[
        "tasks"
      ][task_name]
    )

    print(
      f"{task_name}: "
      f"{task['status']} | "
      f"{task['artifact_directory']}"
    )


def main() -> None:
  """Prepare the candidate for the latest split."""
  (
    candidate_manifest_path,
    frozen_split_manifest_path,
    candidate_manifest,
  ) = prepare_candidate_run()

  print_candidate_summary(
    candidate_manifest
  )

  print("")
  print(
    "Candidate manifest: "
    f"{candidate_manifest_path}"
  )
  print(
    "Frozen split manifest: "
    f"{frozen_split_manifest_path}"
  )


if __name__ == "__main__":
  main()
