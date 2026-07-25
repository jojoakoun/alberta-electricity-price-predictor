"""Verify the single authoritative Python dependency contract."""

from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[2]


def read_requirement_lines() -> list[str]:
  """Return package entries while ignoring comments and blank lines."""
  return [
    line.strip()
    for line in (
      ROOT
      / "requirements.txt"
    ).read_text(
      encoding="utf-8"
    ).splitlines()
    if (
      line.strip()
      and not line.lstrip().startswith("#")
    )
  ]


def test_requirements_contains_every_python_package() -> None:
  assert read_requirement_lines() == [
    "pandas==3.0.3",
    "numpy==2.4.6",
    "requests==2.34.2",
    "python-dotenv==1.2.2",
    "PyYAML==6.0.3",
    "scikit-learn==1.9.0",
    "joblib==1.5.3",
    "psycopg==3.3.4",
    "matplotlib==3.11.0",
    "pytest==9.0.3",
  ]


def test_obsolete_requirement_files_are_absent() -> None:
  assert not (
    ROOT
    / "requirements-dev.txt"
  ).exists()

  assert not (
    ROOT
    / "requirements-research.txt"
  ).exists()


def test_requirements_does_not_include_other_files() -> None:
  assert not any(
    line.startswith("-r ")
    for line in read_requirement_lines()
  )


def test_local_install_uses_the_single_requirements_file() -> None:
  makefile = (
    ROOT
    / "Makefile"
  ).read_text(
    encoding="utf-8"
  )

  install_target = makefile.split(
    "install:\n",
    1,
  )[1].split(
    "\n\n",
    1,
  )[0]

  assert (
    "$(PIP) install -r requirements.txt"
    in install_target
  )


def test_pyproject_does_not_duplicate_python_packages() -> None:
  pyproject = tomllib.loads(
    (
      ROOT
      / "pyproject.toml"
    ).read_text(
      encoding="utf-8"
    )
  )

  project = pyproject.get(
    "project",
    {}
  )

  assert not project.get(
    "dependencies",
    []
  )

  assert not project.get(
    "optional-dependencies",
    {}
  )
