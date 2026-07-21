import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: str) -> dict:
  return json.loads(
    (ROOT / path).read_text(
      encoding="utf-8"
    )
  )


def test_web_railway_configuration() -> None:
  config = load_json(
    "railway.json"
  )

  assert (
    config["build"]["builder"]
    == "RAILPACK"
  )

  assert (
    "app/server"
    in config["build"]["buildCommand"]
  )

  assert (
    "app/client"
    in config["build"]["buildCommand"]
  )

  assert config[
    "deploy"
  ][
    "preDeployCommand"
  ] == (
    "npm --prefix app/server "
    "run migrate:prod"
  )

  assert config[
    "deploy"
  ][
    "startCommand"
  ] == (
    "npm --prefix app/server start"
  )

  assert config[
    "deploy"
  ][
    "healthcheckPath"
  ] == "/api/v1/health"

  assert config[
    "deploy"
  ][
    "restartPolicyType"
  ] == "ON_FAILURE"


def test_migration_cli_is_available_in_production() -> None:
  package = load_json(
    "app/server/package.json"
  )

  assert (
    "node-pg-migrate"
    in package["dependencies"]
  )

  assert (
    "node-pg-migrate"
    not in package.get(
      "devDependencies",
      {},
    )
  )


def test_node_runtime_is_constrained() -> None:
  expected = ">=22.22.3 <23"

  server = load_json(
    "app/server/package.json"
  )

  client = load_json(
    "app/client/package.json"
  )

  assert (
    server["engines"]["node"]
    == expected
  )

  assert (
    client["engines"]["node"]
    == expected
  )


def test_worker_remains_a_separate_cron() -> None:
  worker = load_json(
    "railway.worker.json"
  )

  assert worker[
    "deploy"
  ][
    "startCommand"
  ] == "make worker-run"

  assert worker[
    "deploy"
  ][
    "cronSchedule"
  ] == "15 * * * *"

  assert worker[
    "deploy"
  ][
    "restartPolicyType"
  ] == "NEVER"


def test_required_variables_are_documented() -> None:
  content = (
    ROOT / ".env.example"
  ).read_text(
    encoding="utf-8"
  )

  for variable in (
    "NODE_ENV=",
    "DATABASE_URL=",
    "MODEL_RELEASE_URL=",
    "MODEL_RELEASE_SHA256=",
  ):
    assert variable in content
