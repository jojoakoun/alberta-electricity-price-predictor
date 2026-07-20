import argparse
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

from electricity_predictor.config import (
  load_configuration,
)
from electricity_predictor.modeling.lifecycle.candidate import (
  prepare_candidate_run,
  read_json_file,
)
from electricity_predictor.modeling.lifecycle.classification_candidate import (
  train_classification_candidate,
)
from electricity_predictor.modeling.lifecycle.comparison import (
  compare_candidate_to_champion,
)
from electricity_predictor.modeling.lifecycle.manifest import (
  materialize_lifecycle_manifest,
)
from electricity_predictor.modeling.lifecycle.regression_candidate import (
  resolve_latest_candidate_manifest_path,
  train_regression_candidate,
)


LIFECYCLE_STATE_PATH = Path(
  "reports/model_lifecycle/lifecycle_state.json"
)

LATEST_SPLIT_MANIFEST_PATH = Path(
  "reports/model_lifecycle/latest_split_manifest.json"
)

CANDIDATE_ROOT = Path(
  "models/candidates"
)

PREPARATION_STEPS = (
  (
    "Refresh market data",
    Path(
      "src/electricity_predictor/data/pipeline.py"
    ),
  ),
  (
    "Validate market data",
    Path(
      "src/electricity_predictor/data/data_quality.py"
    ),
  ),
  (
    "Build modeling features",
    Path(
      "src/electricity_predictor/features/feature_engineering.py"
    ),
  ),
  (
    "Validate modeling features",
    Path(
      "src/electricity_predictor/features/feature_quality.py"
    ),
  ),
  (
    "Build training dataset",
    Path(
      "src/electricity_predictor/features/training_data.py"
    ),
  ),
)


def normalize_utc_datetime(
  value: datetime,
) -> datetime:
  """Return one timezone-aware UTC datetime."""
  if value.tzinfo is None:
    value = value.replace(
      tzinfo=UTC
    )

  return value.astimezone(
    UTC
  )


def parse_utc_datetime(
  value: str,
) -> datetime:
  """Parse an ISO timestamp as UTC."""
  normalized = str(
    value
  ).strip().replace(
    "Z",
    "+00:00",
  )

  try:
    parsed = datetime.fromisoformat(
      normalized
    )
  except ValueError as error:
    raise ValueError(
      f"Invalid lifecycle UTC timestamp: {value}"
    ) from error

  return normalize_utc_datetime(
    parsed
  )


def load_lifecycle_state(
  state_path: Path = (
    LIFECYCLE_STATE_PATH
  ),
) -> dict | None:
  """Load the latest successful lifecycle state."""
  if not state_path.exists():
    return None

  try:
    state = json.loads(
      state_path.read_text(
        encoding="utf-8"
      )
    )
  except json.JSONDecodeError as error:
    raise ValueError(
      f"Invalid lifecycle state JSON: {state_path}"
    ) from error

  if not isinstance(
    state,
    dict,
  ):
    raise ValueError(
      "Lifecycle state must contain a JSON object."
    )

  return state


def write_lifecycle_state(
  state: dict,
  state_path: Path = (
    LIFECYCLE_STATE_PATH
  ),
) -> Path:
  """Write lifecycle state atomically."""
  state_path.parent.mkdir(
    parents=True,
    exist_ok=True,
  )

  temporary_path = (
    state_path.parent
    / (
      f".{state_path.name}."
      f"{uuid4().hex}.tmp"
    )
  )

  temporary_path.write_text(
    json.dumps(
      state,
      indent=2,
      sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
  )

  os.replace(
    temporary_path,
    state_path,
  )

  return state_path


def load_promotion_summary(
  candidate_manifest: dict,
) -> tuple[Path | None, dict | None]:
  """Load the comparison summary for one candidate."""
  candidate_directory = (
    candidate_manifest.get(
      "candidate_directory"
    )
  )

  if not candidate_directory:
    return None, None

  summary_path = (
    Path(
      str(
        candidate_directory
      )
    )
    / "reports"
    / "comparison"
    / "promotion_summary.json"
  )

  if not summary_path.exists():
    return summary_path, None

  return (
    summary_path,
    read_json_file(
      summary_path
    ),
  )


def build_state_from_candidate(
  candidate_manifest_path: Path,
) -> dict | None:
  """Recover scheduler state from an evaluated candidate."""
  if not candidate_manifest_path.exists():
    return None

  candidate_manifest = read_json_file(
    candidate_manifest_path
  )

  if (
    candidate_manifest.get(
      "status"
    )
    != "evaluated"
  ):
    return None

  (
    promotion_summary_path,
    promotion_summary,
  ) = load_promotion_summary(
    candidate_manifest
  )

  completed_at_utc = (
    candidate_manifest.get(
      "evaluated_at_utc"
    )
  )

  if (
    completed_at_utc is None
    and promotion_summary is not None
  ):
    completed_at_utc = (
      promotion_summary.get(
        "evaluated_at_utc"
      )
    )

  if completed_at_utc is None:
    return None

  parse_utc_datetime(
    completed_at_utc
  )

  return {
    "schema_version": 1,
    "status": "completed",
    "last_completed_at_utc": (
      completed_at_utc
    ),
    "candidate_manifest_path": str(
      candidate_manifest_path
    ),
    "model_version": (
      candidate_manifest.get(
        "model_version"
      )
    ),
    "split_version": (
      candidate_manifest.get(
        "split_version"
      )
    ),
    "promotion_mode": (
      candidate_manifest.get(
        "promotion_mode",
        "manual",
      )
    ),
    "promotion_summary_path": (
      str(
        promotion_summary_path
      )
      if promotion_summary_path
      else None
    ),
    "state_source": (
      "existing_evaluated_candidate"
    ),
  }


def discover_latest_candidate_state() -> dict | None:
  """Find scheduler state from the latest candidate."""
  try:
    candidate_manifest_path = (
      resolve_latest_candidate_manifest_path(
        latest_split_manifest_path=(
          LATEST_SPLIT_MANIFEST_PATH
        ),
        candidate_root=(
          CANDIDATE_ROOT
        ),
      )
    )
  except (
    FileNotFoundError,
    ValueError,
  ):
    return None

  return build_state_from_candidate(
    candidate_manifest_path
  )


def resolve_lifecycle_state(
  state_path: Path = (
    LIFECYCLE_STATE_PATH
  ),
) -> dict | None:
  """Load state or recover it from existing reports."""
  state = load_lifecycle_state(
    state_path
  )

  if state is not None:
    return state

  recovered_state = (
    discover_latest_candidate_state()
  )

  if recovered_state is not None:
    write_lifecycle_state(
      state=recovered_state,
      state_path=state_path,
    )

  return recovered_state


def validate_lifecycle_configuration(
  lifecycle_config: dict,
) -> tuple[int, str]:
  """Validate scheduler and promotion settings."""
  try:
    interval_days = int(
      lifecycle_config[
        "retraining_interval_days"
      ]
    )
  except (
    KeyError,
    TypeError,
    ValueError,
  ) as error:
    raise ValueError(
      "model_lifecycle.retraining_interval_days "
      "must be a positive integer."
    ) from error

  if interval_days <= 0:
    raise ValueError(
      "model_lifecycle.retraining_interval_days "
      "must be greater than zero."
    )

  promotion_mode = str(
    lifecycle_config.get(
      "promotion_mode",
      "",
    )
  ).strip().lower()

  if promotion_mode != "manual":
    raise ValueError(
      "Scheduled lifecycle runs require "
      "promotion_mode: manual."
    )

  return (
    interval_days,
    promotion_mode,
  )


def calculate_lifecycle_schedule(
  state: dict | None,
  interval_days: int,
  now_utc: datetime,
) -> dict:
  """Calculate whether a new challenger is due."""
  now_utc = normalize_utc_datetime(
    now_utc
  )

  if state is None:
    return {
      "due": True,
      "last_completed_at_utc": None,
      "next_due_at_utc": None,
      "remaining_days": 0,
    }

  completed_text = state.get(
    "last_completed_at_utc"
  )

  if not completed_text:
    raise ValueError(
      "Lifecycle state is missing "
      "last_completed_at_utc."
    )

  completed_at = parse_utc_datetime(
    completed_text
  )

  next_due_at = (
    completed_at
    + timedelta(
      days=interval_days
    )
  )

  remaining = (
    next_due_at
    - now_utc
  )

  return {
    "due": (
      now_utc
      >= next_due_at
    ),
    "last_completed_at_utc": (
      completed_at.isoformat()
    ),
    "next_due_at_utc": (
      next_due_at.isoformat()
    ),
    "remaining_days": max(
      0,
      remaining.days,
    ),
  }


def prepare_lifecycle_training_data() -> None:
  """Refresh and validate the ML training dataset."""
  for (
    step_name,
    script_path,
  ) in PREPARATION_STEPS:
    if not script_path.exists():
      raise FileNotFoundError(
        f"Lifecycle preparation script "
        f"not found: {script_path}"
      )

    print()
    print(
      f"Lifecycle preparation: {step_name}"
    )
    print(
      "-" * (
        len(step_name)
        + 23
      )
    )

    subprocess.run(
      [
        sys.executable,
        str(
          script_path
        ),
      ],
      check=True,
    )


def run_lifecycle(
  force: bool = False,
  now_utc: datetime | None = None,
  state_path: Path = (
    LIFECYCLE_STATE_PATH
  ),
) -> dict:
  """Create and evaluate one challenger without promotion."""
  configuration = (
    load_configuration()
  )

  lifecycle_config = configuration[
    "model_lifecycle"
  ]

  (
    interval_days,
    promotion_mode,
  ) = validate_lifecycle_configuration(
    lifecycle_config
  )

  effective_now = (
    normalize_utc_datetime(
      now_utc
    )
    if now_utc is not None
    else datetime.now(
      UTC
    )
  )

  existing_state = (
    resolve_lifecycle_state(
      state_path
    )
  )

  schedule = (
    calculate_lifecycle_schedule(
      state=existing_state,
      interval_days=interval_days,
      now_utc=effective_now,
    )
  )

  if (
    not schedule[
      "due"
    ]
    and not force
  ):
    return {
      "status": "skipped",
      "reason": (
        "retraining_interval_not_reached"
      ),
      "interval_days": interval_days,
      "promotion_mode": promotion_mode,
      **schedule,
      "model_version": (
        existing_state.get(
          "model_version"
        )
        if existing_state
        else None
      ),
    }

  started_at_utc = (
    effective_now.isoformat()
  )

  prepare_lifecycle_training_data()

  materialize_lifecycle_manifest()

  (
    candidate_manifest_path,
    _,
    candidate_manifest,
  ) = prepare_candidate_run(
    split_manifest_path=(
      LATEST_SPLIT_MANIFEST_PATH
    ),
    candidate_root=(
      CANDIDATE_ROOT
    ),
    promotion_mode=(
      promotion_mode
    ),
  )

  train_regression_candidate(
    candidate_manifest_path=(
      candidate_manifest_path
    )
  )

  train_classification_candidate(
    candidate_manifest_path=(
      candidate_manifest_path
    )
  )

  compare_candidate_to_champion(
    candidate_manifest_path=(
      candidate_manifest_path
    )
  )

  evaluated_manifest = read_json_file(
    candidate_manifest_path
  )

  if (
    evaluated_manifest.get(
      "status"
    )
    != "evaluated"
  ):
    raise RuntimeError(
      "Lifecycle comparison did not mark "
      "the candidate as evaluated."
    )

  (
    promotion_summary_path,
    promotion_summary,
  ) = load_promotion_summary(
    evaluated_manifest
  )

  if promotion_summary is None:
    raise FileNotFoundError(
      "Lifecycle comparison did not produce "
      "promotion_summary.json."
    )

  completed_at_text = (
    promotion_summary.get(
      "evaluated_at_utc"
    )
  )

  if not completed_at_text:
    completed_at_text = (
      datetime.now(
        UTC
      ).isoformat()
      if now_utc is None
      else effective_now.isoformat()
    )

  completed_at = parse_utc_datetime(
    completed_at_text
  )

  next_due_at = (
    completed_at
    + timedelta(
      days=interval_days
    )
  )

  completed_state = {
    "schema_version": 1,
    "status": "completed",
    "started_at_utc": (
      started_at_utc
    ),
    "last_completed_at_utc": (
      completed_at.isoformat()
    ),
    "next_due_at_utc": (
      next_due_at.isoformat()
    ),
    "retraining_interval_days": (
      interval_days
    ),
    "candidate_manifest_path": str(
      candidate_manifest_path
    ),
    "model_version": (
      evaluated_manifest[
        "model_version"
      ]
    ),
    "split_version": (
      evaluated_manifest[
        "split_version"
      ]
    ),
    "promotion_mode": (
      promotion_mode
    ),
    "promotion_summary_path": str(
      promotion_summary_path
    ),
    "regression_gate_pass": (
      promotion_summary.get(
        "regression_gate_pass"
      )
    ),
    "classification_gate_pass": (
      promotion_summary.get(
        "classification_gate_pass"
      )
    ),
    "promotion_ready": (
      promotion_summary.get(
        "promotion_ready"
      )
    ),
    "automatic_promotion_performed": (
      False
    ),
    "state_source": (
      "scheduled_lifecycle_run"
    ),
  }

  write_lifecycle_state(
    state=completed_state,
    state_path=state_path,
  )

  return {
    **completed_state,
    "status": "completed",
    "candidate_directory": (
      candidate_manifest[
        "candidate_directory"
      ]
    ),
  }


def get_lifecycle_status(
  now_utc: datetime | None = None,
  state_path: Path = (
    LIFECYCLE_STATE_PATH
  ),
) -> dict:
  """Return current scheduler status."""
  configuration = (
    load_configuration()
  )

  lifecycle_config = configuration[
    "model_lifecycle"
  ]

  (
    interval_days,
    promotion_mode,
  ) = validate_lifecycle_configuration(
    lifecycle_config
  )

  effective_now = (
    normalize_utc_datetime(
      now_utc
    )
    if now_utc is not None
    else datetime.now(
      UTC
    )
  )

  state = resolve_lifecycle_state(
    state_path
  )

  schedule = (
    calculate_lifecycle_schedule(
      state=state,
      interval_days=interval_days,
      now_utc=effective_now,
    )
  )

  return {
    "status": (
      "due"
      if schedule[
        "due"
      ]
      else "waiting"
    ),
    "checked_at_utc": (
      effective_now.isoformat()
    ),
    "retraining_interval_days": (
      interval_days
    ),
    "promotion_mode": (
      promotion_mode
    ),
    "automatic_promotion": False,
    **schedule,
    "model_version": (
      state.get(
        "model_version"
      )
      if state
      else None
    ),
    "candidate_manifest_path": (
      state.get(
        "candidate_manifest_path"
      )
      if state
      else None
    ),
  }


def print_lifecycle_status(
  status: dict,
) -> None:
  """Print a readable scheduler status."""
  print("Model lifecycle status")
  print("======================")

  print(
    f"Status: {status['status']}"
  )

  print(
    "Retraining interval: "
    f"{status['retraining_interval_days']} days"
  )

  print(
    "Promotion mode: "
    f"{status['promotion_mode']}"
  )

  print(
    "Automatic promotion: no"
  )

  print(
    "Last completed: "
    f"{status.get('last_completed_at_utc')}"
  )

  print(
    "Next due: "
    f"{status.get('next_due_at_utc')}"
  )

  print(
    "Model version: "
    f"{status.get('model_version')}"
  )

  print(
    "Candidate manifest: "
    f"{status.get('candidate_manifest_path')}"
  )


def print_lifecycle_result(
  result: dict,
) -> None:
  """Print one runner result."""
  print("Model lifecycle runner")
  print("======================")

  print(
    f"Status: {result['status']}"
  )

  if result[
    "status"
  ] == "skipped":
    print(
      "Reason: retraining interval "
      "has not been reached."
    )

    print(
      "Next due: "
      f"{result['next_due_at_utc']}"
    )

    return

  print(
    "Model version: "
    f"{result['model_version']}"
  )

  print(
    "Candidate manifest: "
    f"{result['candidate_manifest_path']}"
  )

  print(
    "Promotion summary: "
    f"{result['promotion_summary_path']}"
  )

  print(
    "Regression gate: "
    f"{result['regression_gate_pass']}"
  )

  print(
    "Classification gate: "
    f"{result['classification_gate_pass']}"
  )

  print(
    "Automatic promotion performed: no"
  )

  print(
    "Next due: "
    f"{result['next_due_at_utc']}"
  )


def main() -> None:
  """Run or inspect the scheduled model lifecycle."""
  parser = argparse.ArgumentParser(
    description=(
      "Create and evaluate WattWise "
      "champion-challenger models."
    )
  )

  parser.add_argument(
    "--status",
    action="store_true",
    help=(
      "Show whether retraining is due "
      "without running it."
    ),
  )

  parser.add_argument(
    "--force",
    action="store_true",
    help=(
      "Run lifecycle training even when "
      "the 90-day interval is not due."
    ),
  )

  arguments = parser.parse_args()

  if arguments.status:
    print_lifecycle_status(
      get_lifecycle_status()
    )

    return

  result = run_lifecycle(
    force=arguments.force
  )

  print_lifecycle_result(
    result
  )


if __name__ == "__main__":
  main()
