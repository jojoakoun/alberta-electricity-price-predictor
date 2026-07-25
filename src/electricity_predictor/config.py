import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


def load_configuration(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
  """Load the project configuration from YAML."""
  load_dotenv(PROJECT_ROOT / ".env")

  if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")

  with config_path.open("r", encoding="utf-8") as file:
    configuration = yaml.safe_load(file)

  if not isinstance(configuration, dict):
    raise ValueError("Config file must contain a YAML dictionary.")

  return configuration


def load_database_url() -> str:
  """Load the PostgreSQL connection string from the environment."""
  load_dotenv(PROJECT_ROOT / ".env")

  database_url = os.getenv("DATABASE_URL")

  if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is required.")

  return database_url
