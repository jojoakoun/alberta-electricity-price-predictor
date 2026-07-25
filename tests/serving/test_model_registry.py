from pathlib import Path

from electricity_predictor.serving.model_registry import (
  build_legacy_registry,
  initialize_active_registry,
  read_active_registry,
  resolve_active_metadata_paths,
)


def create_metadata_files(
  tmp_path: Path,
) -> tuple[Path, Path]:
  regression_path = (
    tmp_path / "regression.csv"
  )

  classification_path = (
    tmp_path / "classification.csv"
  )

  regression_path.write_text(
    "model_name\nregression\n",
    encoding="utf-8",
  )

  classification_path.write_text(
    "model_name\nclassification\n",
    encoding="utf-8",
  )

  return (
    regression_path,
    classification_path,
  )


def test_initialize_active_registry_is_idempotent(
  tmp_path: Path,
):
  regression_path, classification_path = (
    create_metadata_files(
      tmp_path
    )
  )

  registry_path = (
    tmp_path / "active.json"
  )

  registry = build_legacy_registry(
    updated_at_utc=(
      "2026-07-20T18:00:00+00:00"
    )
  )

  registry[
    "tasks"
  ][
    "regression"
  ][
    "metadata_path"
  ] = str(
    regression_path
  )

  registry[
    "tasks"
  ][
    "classification"
  ][
    "metadata_path"
  ] = str(
    classification_path
  )

  from electricity_predictor.serving.model_registry import (
    write_active_registry_atomic,
  )

  write_active_registry_atomic(
    registry=registry,
    registry_path=registry_path,
  )

  first_path, first = (
    initialize_active_registry(
      registry_path=registry_path
    )
  )

  second_path, second = (
    initialize_active_registry(
      registry_path=registry_path
    )
  )

  assert first_path == second_path
  assert first == second


def test_resolve_active_metadata_paths(
  tmp_path: Path,
):
  regression_path, classification_path = (
    create_metadata_files(
      tmp_path
    )
  )

  registry_path = (
    tmp_path / "active.json"
  )

  registry = build_legacy_registry()

  registry[
    "tasks"
  ][
    "regression"
  ][
    "metadata_path"
  ] = str(
    regression_path
  )

  registry[
    "tasks"
  ][
    "classification"
  ][
    "metadata_path"
  ] = str(
    classification_path
  )

  from electricity_predictor.serving.model_registry import (
    write_active_registry_atomic,
  )

  write_active_registry_atomic(
    registry=registry,
    registry_path=registry_path,
  )

  (
    resolved_regression,
    resolved_classification,
    loaded_registry,
  ) = resolve_active_metadata_paths(
    registry_path=registry_path
  )

  assert (
    resolved_regression
    == regression_path
  )

  assert (
    resolved_classification
    == classification_path
  )

  assert (
    loaded_registry[
      "tasks"
    ][
      "regression"
    ][
      "model_version"
    ]
    == "legacy-unversioned"
  )


def test_read_active_registry_rejects_missing_file(
  tmp_path: Path,
):
  import pytest

  with pytest.raises(
    FileNotFoundError,
    match="registry not found",
  ):
    read_active_registry(
      registry_path=(
        tmp_path / "missing.json"
      )
    )
