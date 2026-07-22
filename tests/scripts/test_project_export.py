import csv
import hashlib
from pathlib import Path
import zipfile

import pytest

from scripts.project_export.inventory import collect_project_files
from scripts.project_export.policy import (
  exclusion_reason,
  validate_archive_path,
)
from scripts.project_export.verification import (
  load_manifest,
  verify_project_export,
)
from scripts.project_export.writers import (
  write_context,
  write_manifests,
  write_zip,
)


@pytest.mark.parametrize(
  "path",
  [
    "docs/private.md",
    "reports/results.csv",
    "models/model.joblib",
    "context_exports/archive.zip",
    "codex-review.txt",
    "claude-review.md",
    "audit-final.txt",
    ".env",
    ".env.local",
    ".env.staging",
    "nested/service-account-prod.json",
  ],
)
def test_policy_excludes_local_and_secret_paths(path: str) -> None:
  assert exclusion_reason(Path(path)) is not None


def test_policy_allows_public_environment_example() -> None:
  assert exclusion_reason(Path(".env.example")) is None


def test_inventory_is_deterministic_and_excludes_local_paths(
  tmp_path: Path,
) -> None:
  (tmp_path / "zeta.txt").write_text("z", encoding="utf-8")
  (tmp_path / "alpha.txt").write_text("a", encoding="utf-8")
  (tmp_path / ".env.example").write_text("SAFE=value\n", encoding="utf-8")
  (tmp_path / ".env.private").write_text("SECRET=value\n", encoding="utf-8")
  reports = tmp_path / "reports"
  reports.mkdir()
  (reports / "result.csv").write_text("value\n1\n", encoding="utf-8")

  files, excluded = collect_project_files(tmp_path)

  assert [item.relative_path.as_posix() for item in files] == [
    ".env.example",
    "alpha.txt",
    "zeta.txt",
  ]
  assert [path for path, _ in excluded] == [".env.private", "reports/"]


def test_inventory_rejects_file_symlinks(tmp_path: Path) -> None:
  source = tmp_path / "source.txt"
  source.write_text("source", encoding="utf-8")
  link = tmp_path / "linked.txt"

  try:
    link.symlink_to(source)
  except OSError:
    pytest.skip("File symlinks are unavailable on this platform")

  files, excluded = collect_project_files(tmp_path)

  assert [item.relative_path.as_posix() for item in files] == ["source.txt"]
  assert ("linked.txt", "symbolic link") in excluded


def test_manifest_and_archive_round_trip_uses_relative_paths(
  tmp_path: Path,
) -> None:
  project_root = tmp_path / "project"
  project_root.mkdir()
  (project_root / "app.js").write_text("export const value = 1;\n", encoding="utf-8")
  files, excluded = collect_project_files(project_root)

  output = tmp_path / "output"
  manifest_path = output / "manifest.txt"
  excluded_path = output / "excluded.txt"
  context_path = output / "context.txt"
  zip_path = output / "project.zip"

  write_manifests(files, excluded, manifest_path, excluded_path)
  context_path.write_text("context\n", encoding="utf-8")
  write_zip(files, zip_path)

  assert verify_project_export(
    zip_path,
    manifest_path,
    context_path,
    excluded_path,
  ) == 1

  with zipfile.ZipFile(zip_path) as archive:
    assert archive.namelist() == ["app.js"]


def test_context_git_diagnostics_use_only_inventory_allowed_paths(
  tmp_path: Path,
  monkeypatch,
) -> None:
  project_root = tmp_path / "project"
  project_root.mkdir()
  (project_root / "app.js").write_text("safe\n", encoding="utf-8")
  (project_root / "safe*.js").write_text("also safe\n", encoding="utf-8")
  private_docs = project_root / "docs"
  private_docs.mkdir()
  (private_docs / "private.md").write_text("secret\n", encoding="utf-8")
  files, excluded = collect_project_files(project_root)

  output = tmp_path / "output"
  manifest_path = output / "manifest.txt"
  excluded_path = output / "excluded.txt"
  context_path = output / "context.txt"
  write_manifests(files, excluded, manifest_path, excluded_path)

  commands = []

  def capture_command(command, root):
    commands.append(command)
    return ""

  monkeypatch.setattr(
    "scripts.project_export.writers.run_command",
    capture_command,
  )

  write_context(
    files=files,
    excluded=excluded,
    root=project_root,
    context_path=context_path,
    manifest_path=manifest_path,
    excluded_path=excluded_path,
  )

  scoped_git_commands = [
    command
    for command in commands
    if command[:2] in (["git", "status"], ["git", "diff"])
  ]

  assert scoped_git_commands
  assert all(
    ":(top,literal)app.js" in command
    for command in scoped_git_commands
  )
  assert all(
    ":(top,literal)safe*.js" in command
    for command in scoped_git_commands
  )
  assert all("app.js" not in command for command in scoped_git_commands)
  assert all("safe*.js" not in command for command in scoped_git_commands)
  assert all("docs/private.md" not in command for command in scoped_git_commands)


@pytest.mark.parametrize("path", ["../secret", "/absolute", "docs/private.md", ".env.prod"])
def test_archive_validation_rejects_unsafe_or_forbidden_paths(path: str) -> None:
  with pytest.raises(ValueError):
    validate_archive_path(path)


def test_manifest_rejects_duplicate_paths(tmp_path: Path) -> None:
  manifest_path = tmp_path / "manifest.txt"
  manifest_path.write_text(
    "path\tsize_bytes\tsha256\tkind\n"
    "app.js\t1\ta\ttext\n"
    "app.js\t1\ta\ttext\n",
    encoding="utf-8",
  )

  with pytest.raises(ValueError, match="Duplicate paths exist in the manifest"):
    load_manifest(manifest_path)


def test_verification_rejects_unsafe_directory_only_archive_entry(
  tmp_path: Path,
) -> None:
  zip_path = tmp_path / "project.zip"
  manifest_path = tmp_path / "manifest.txt"
  context_path = tmp_path / "context.txt"
  excluded_path = tmp_path / "excluded.txt"

  with zipfile.ZipFile(zip_path, "w") as archive:
    archive.writestr("../escape/", b"")

  manifest_path.write_text(
    "path\tsize_bytes\tsha256\tkind\n",
    encoding="utf-8",
  )
  context_path.write_text("context\n", encoding="utf-8")
  excluded_path.write_text("path\treason\n", encoding="utf-8")

  with pytest.raises(ValueError, match="Unsafe archive path: ../escape/"):
    verify_project_export(
      zip_path,
      manifest_path,
      context_path,
      excluded_path,
    )


def test_verification_rejects_checksum_mismatch(tmp_path: Path) -> None:
  zip_path = tmp_path / "project.zip"
  manifest_path = tmp_path / "manifest.txt"
  context_path = tmp_path / "context.txt"
  excluded_path = tmp_path / "excluded.txt"
  content = b"actual"

  with zipfile.ZipFile(zip_path, "w") as archive:
    archive.writestr("app.js", content)

  wrong_hash = hashlib.sha256(b"different").hexdigest()
  with manifest_path.open("w", encoding="utf-8", newline="") as manifest_file:
    writer = csv.writer(manifest_file, delimiter="\t")
    writer.writerow(["path", "size_bytes", "sha256", "kind"])
    writer.writerow(["app.js", len(content), wrong_hash, "text"])

  context_path.write_text("context\n", encoding="utf-8")
  excluded_path.write_text("path\treason\n", encoding="utf-8")

  with pytest.raises(ValueError, match="Checksum mismatch: app.js"):
    verify_project_export(
      zip_path,
      manifest_path,
      context_path,
      excluded_path,
    )
