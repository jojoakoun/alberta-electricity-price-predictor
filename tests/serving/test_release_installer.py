import fcntl
from hashlib import sha256
import io
import json
import multiprocessing
from pathlib import Path
import tarfile

import joblib
import pandas as pd
import pytest

from electricity_predictor.modeling.lifecycle.release_bundle import (
  build_production_release,
)
from electricity_predictor.serving.model_registry import (
  build_legacy_registry,
  write_active_registry_atomic,
)
from electricity_predictor.serving.release_installer import (
  _validate_release_task,
  acquire_release_install_lock,
  install_release_archive,
  install_release_from_url,
)


HORIZONS = [
  1,
  3,
  6,
  12,
  24,
]


def test_release_task_validation_rejects_duplicate_horizon(
  tmp_path: Path,
) -> None:
  rows = []

  for index, horizon in enumerate([*HORIZONS, 24]):
    artifact_path = tmp_path / f"artifact-{index}.joblib"
    artifact_path.write_bytes(b"artifact")
    rows.append({
      "horizon_hours": horizon,
      "artifact_path": artifact_path.name,
    })

  metadata_path = tmp_path / "metadata.csv"
  pd.DataFrame(rows).to_csv(metadata_path, index=False)

  with pytest.raises(
    ValueError,
    match="exactly one row for each horizon",
  ):
    _validate_release_task(
      extraction_root=tmp_path,
      tasks={
        "regression": {
          "metadata_path": metadata_path.name,
        }
      },
      task_name="regression",
    )


def hold_release_install_lock(
  models_root_text: str,
  ready,
  release,
) -> None:
  models_root = Path(models_root_text)
  models_root.mkdir(parents=True, exist_ok=True)

  with acquire_release_install_lock(models_root):
    ready.set()

    if not release.wait(timeout=30):
      raise TimeoutError(
        "Timed out waiting to release the test install lock."
      )


def install_release_in_process(
  archive_path_text: str,
  expected_sha256: str,
  project_root_text: str,
  start,
  results,
) -> None:
  if not start.wait(timeout=30):
    raise TimeoutError(
      "Timed out waiting to start the concurrent install."
    )

  try:
    result = install_release_archive(
      archive_path=Path(archive_path_text),
      expected_sha256=expected_sha256,
      project_root=Path(project_root_text),
    )
  except Exception as error:
    results.put(
      {
        "error": (
          f"{type(error).__name__}: {error}"
        )
      }
    )
  else:
    results.put(
      {
        "status": result["status"],
        "release_id": result["release_id"],
      }
    )


def write_task_bundle(
  directory: Path,
  task_name: str,
) -> Path:
  directory.mkdir(
    parents=True,
    exist_ok=True,
  )

  rows = []

  for horizon in HORIZONS:
    artifact_path = (
      directory
      / f"{task_name}-{horizon}.joblib"
    )

    joblib.dump(
      {
        "task": task_name,
        "horizon": horizon,
      },
      artifact_path,
    )

    row = {
      "model_name":
        f"{task_name}_model",
      "horizon_hours": horizon,
      "artifact_path": str(
        artifact_path
      ),
      "feature_columns": (
        "forecast_price|"
        "actual_price_lag_1h"
      ),
    }

    if task_name == "classification":
      row.update(
        {
          "spike_threshold": 157.885,
          "decision_threshold": 0.5,
        }
      )

    rows.append(row)

  metadata_path = (
    directory / "metadata.csv"
  )

  pd.DataFrame(
    rows
  ).to_csv(
    metadata_path,
    index=False,
  )

  return metadata_path


def build_test_release(
  tmp_path: Path,
) -> dict:
  regression_metadata = (
    write_task_bundle(
      tmp_path / "source-regression",
      "regression",
    )
  )

  classification_metadata = (
    write_task_bundle(
      tmp_path / "source-classification",
      "classification",
    )
  )

  registry = build_legacy_registry()

  registry[
    "tasks"
  ][
    "regression"
  ].update(
    {
      "model_version":
        "regression-v1",
      "metadata_path": str(
        regression_metadata
      ),
      "source": "candidate",
    }
  )

  registry[
    "tasks"
  ][
    "classification"
  ].update(
    {
      "model_version":
        "classification-v1",
      "metadata_path": str(
        classification_metadata
      ),
      "source": "legacy",
    }
  )

  registry_path = (
    tmp_path / "active_models.json"
  )

  write_active_registry_atomic(
    registry=registry,
    registry_path=registry_path,
  )

  return build_production_release(
    registry_path=registry_path,
    build_root=(
      tmp_path / "release-build"
    ),
  )


def test_install_release_from_file_url(
  tmp_path: Path,
):
  descriptor = build_test_release(
    tmp_path
  )

  archive_path = Path(
    descriptor[
      "archive_path"
    ]
  ).resolve()

  project_root = (
    tmp_path / "installed-project"
  )

  result = install_release_from_url(
    release_url=archive_path.as_uri(),
    expected_sha256=descriptor[
      "archive_sha256"
    ],
    project_root=project_root,
  )

  assert result[
    "status"
  ] == "installed"

  assert result[
    "release_id"
  ] == descriptor[
    "release_id"
  ]

  registry_path = (
    project_root
    / "models"
    / "production"
    / "active_models.json"
  )

  assert registry_path.exists()

  registry = json.loads(
    registry_path.read_text(
      encoding="utf-8"
    )
  )

  for task_name in [
    "regression",
    "classification",
  ]:
    metadata_path = (
      project_root
      / registry[
        "tasks"
      ][task_name][
        "metadata_path"
      ]
    )

    metadata = pd.read_csv(
      metadata_path
    )

    assert set(
      metadata[
        "horizon_hours"
      ].astype(int)
    ) == set(
      HORIZONS
    )

    for artifact_text in metadata[
      "artifact_path"
    ]:
      assert (
        project_root
        / str(
          artifact_text
        )
      ).exists()

  second_result = (
    install_release_from_url(
      release_url=(
        archive_path.as_uri()
      ),
      expected_sha256=descriptor[
        "archive_sha256"
      ],
      project_root=project_root,
    )
  )

  assert (
    second_result["status"]
    == "already_installed"
  )


def test_install_rejects_wrong_archive_checksum(
  tmp_path: Path,
):
  descriptor = build_test_release(
    tmp_path
  )

  archive_path = Path(
    descriptor[
      "archive_path"
    ]
  )

  project_root = (
    tmp_path / "installed-project"
  )

  with pytest.raises(
    ValueError,
    match="archive checksum mismatch",
  ):
    install_release_archive(
      archive_path=archive_path,
      expected_sha256="0" * 64,
      project_root=project_root,
    )

  assert not (
    project_root
    / "models"
    / "production"
  ).exists()


def test_install_rejects_unsafe_archive_path(
  tmp_path: Path,
):
  archive_path = (
    tmp_path / "unsafe.tar.gz"
  )

  content = b"unsafe\n"

  with tarfile.open(
    archive_path,
    mode="w:gz",
  ) as archive:
    member = tarfile.TarInfo(
      name="../outside.txt"
    )

    member.size = len(
      content
    )

    archive.addfile(
      member,
      io.BytesIO(
        content
      ),
    )

  digest = sha256(
    archive_path.read_bytes()
  ).hexdigest()

  with pytest.raises(
    ValueError,
    match="unsafe path",
  ):
    install_release_archive(
      archive_path=archive_path,
      expected_sha256=digest,
      project_root=(
        tmp_path / "project"
      ),
    )

  assert not (
    tmp_path / "outside.txt"
  ).exists()


def test_release_install_lock_excludes_another_process(
  tmp_path: Path,
) -> None:
  context = multiprocessing.get_context("spawn")
  models_root = tmp_path / "project" / "models"
  models_root.mkdir(parents=True)
  ready = context.Event()
  release = context.Event()

  holder = context.Process(
    target=hold_release_install_lock,
    args=(
      str(models_root),
      ready,
      release,
    ),
  )
  holder.start()

  try:
    assert ready.wait(timeout=30)

    lock_path = (
      models_root / ".release-install.lock"
    )

    with lock_path.open("a+b") as lock_stream:
      with pytest.raises(BlockingIOError):
        fcntl.flock(
          lock_stream.fileno(),
          fcntl.LOCK_EX | fcntl.LOCK_NB,
        )

    release.set()
    holder.join(timeout=30)

    assert not holder.is_alive()
    assert holder.exitcode == 0

    with lock_path.open("a+b") as lock_stream:
      fcntl.flock(
        lock_stream.fileno(),
        fcntl.LOCK_EX | fcntl.LOCK_NB,
      )
      fcntl.flock(
        lock_stream.fileno(),
        fcntl.LOCK_UN,
      )
  finally:
    release.set()

    if holder.is_alive():
      holder.terminate()
      holder.join(timeout=30)


def test_concurrent_release_installs_serialize_and_reuse_release(
  tmp_path: Path,
) -> None:
  descriptor = build_test_release(tmp_path)
  archive_path = Path(descriptor["archive_path"])
  project_root = tmp_path / "installed-project"
  context = multiprocessing.get_context("spawn")
  start = context.Event()
  results = context.Queue()

  installers = [
    context.Process(
      target=install_release_in_process,
      args=(
        str(archive_path),
        descriptor["archive_sha256"],
        str(project_root),
        start,
        results,
      ),
    )
    for _ in range(2)
  ]

  for installer in installers:
    installer.start()

  start.set()

  process_results = [
    results.get(timeout=60)
    for _ in installers
  ]

  for installer in installers:
    installer.join(timeout=60)

    if installer.is_alive():
      installer.terminate()
      installer.join(timeout=30)

    assert installer.exitcode == 0

  assert not any(
    "error" in result
    for result in process_results
  )
  assert sorted(
    result["status"]
    for result in process_results
  ) == [
    "already_installed",
    "installed",
  ]
  assert {
    result["release_id"]
    for result in process_results
  } == {
    descriptor["release_id"]
  }

  production_root = (
    project_root / "models" / "production"
  )
  registry = json.loads(
    (
      production_root / "active_models.json"
    ).read_text(encoding="utf-8")
  )

  assert registry["release_id"] == descriptor["release_id"]
  assert not list(
    (project_root / "models").glob(
      ".release-install-*"
    )
  )
  assert not list(
    (project_root / "models").glob(
      ".production-backup-*"
    )
  )
