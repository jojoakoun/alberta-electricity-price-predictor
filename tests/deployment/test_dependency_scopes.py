from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read_requirement_lines(filename: str) -> list[str]:
  return [
    line.strip()
    for line in (ROOT / filename).read_text(encoding="utf-8").splitlines()
    if line.strip() and not line.startswith("#")
  ]


def test_runtime_requirements_exclude_research_and_test_packages() -> None:
  runtime = read_requirement_lines("requirements.txt")

  assert runtime == [
    "pandas==3.0.3",
    "numpy==2.4.6",
    "requests==2.34.2",
    "python-dotenv==1.2.2",
    "PyYAML==6.0.3",
    "scikit-learn==1.9.0",
    "joblib==1.5.3",
    "psycopg==3.3.4",
  ]


def test_research_and_development_requirements_extend_runtime() -> None:
  assert read_requirement_lines("requirements-research.txt") == [
    "-r requirements.txt",
    "matplotlib==3.11.0",
  ]
  assert read_requirement_lines("requirements-dev.txt") == [
    "-r requirements-research.txt",
    "pytest==9.0.3",
  ]


def test_local_install_uses_development_scope() -> None:
  makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
  install_target = makefile.split("install:\n", 1)[1].split("\n\n", 1)[0]

  assert "$(PIP) install -r requirements-dev.txt" in install_target
