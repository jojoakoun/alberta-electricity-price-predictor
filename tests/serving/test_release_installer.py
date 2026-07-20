from hashlib import sha256
import io
import json
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
