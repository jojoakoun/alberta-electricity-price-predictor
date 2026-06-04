from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "configs" / "config.yaml"


def load_configuration(config_path: Path = CONFIG_PATH) -> dict[str, Any]:
  """Load the project configuration from a YAML file."""
  
  # Load local environment variables if a .env file exists.
  load_dotenv()
  
  if not config_path.exists():
    raise FileNotFoundError(f"Config file not found: {config_path}")
  
  with config_path.open("r", encoding="utf-8") as file:
    config = yaml.safe_load(file)
   
  if not isinstance(config, dict):
    raise ValueError("Config file must contain a YAML dictionary.")

  return config
  

