from electricity_predictor.config import load_configuration


def test_load_configuration_returns_project_name() -> None:
  # The configuration file should load the official project name.
  configuration = load_configuration()

  assert configuration["project"]["name"] == "Alberta Electricity Price Predictor"


def test_load_configuration_contains_required_paths() -> None:
  # These paths are needed by future data, model, and logging modules.
  configuration = load_configuration()

  assert "raw_data_dir" in configuration["paths"]
  assert "processed_data_dir" in configuration["paths"]
  assert "log_dir" in configuration["paths"]